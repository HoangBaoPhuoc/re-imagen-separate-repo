import datetime
import os
import random
import subprocess
import time

import pyautoqemu
from PIL import ImageGrab

from shared import config

# Activity repo for pyautoqemu integration
# currently all implemented login or power on/off related activities are for a single user Windows 10 Home system

# Notes:
# Could be solved in a nicer way (inheritance - activity objects with execute and log functions, vm object)
# If provided by vm control automation tool: Would be nice to add success criteria to implemented activities
# For now: sleep times between actions in an activity are hardcoded

vm = None


def capture_screenshot(activity_name):
    screenshot_name = f"screenshot-taken-at{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{activity_name}.png"
    screenshot_path = os.path.join(config.screenshot_dir, screenshot_name)
    img = ImageGrab.grab()
    img.save(screenshot_path)


def check_vm_running():
    if not vm:
        raise RuntimeError("Expected the VM to be running, but it isn't.")


def start_computer():
    global vm

    qcow2_file = os.path.join(config.shared_dir, config.qcow2_file_name)

    # start vm
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Start computer")
    command = "qemu-system-x86_64 -m 4G -enable-kvm -cpu host -device qemu-xhci -device usb-tablet -vga std -rtc base=localtime -qmp tcp:localhost:" + str(config.qmp_port) +",server,nowait " + qcow2_file
    subprocess.Popen(["/bin/bash", "-c", command])

    # connect to vm
    time.sleep(40)
    vm = pyautoqemu.VM.connect("localhost", config.qmp_port)
    time.sleep(20)


def login_single_user(password):
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "User login")
    vm.send_key("ret")
    time.sleep(10)
    # login
    vm.send_text(str(password))
    time.sleep(1)
    vm.send_key("ret")
    time.sleep(60)


def start_computer_and_login_single_user(password):
    start_computer()
    login_single_user(password)


def shutdown_via_menu():
    # shutdown Windows
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Shutting down VM")
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "win_menu.png"), 5)
    vm.leftclick(x, y)
    time.sleep(5)
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "win_menu_onoff.png"), 5)
    vm.doubleclick(x, y)
    time.sleep(5)
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "win_menu_shutdown.png"), 5)
    vm.leftclick(x, y)
    vm = None


'''
Browsing session - Firefox
'''


def firefox_open_browser_from_desktop():
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Firefox - Start browsing session")
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "firefox_desktop.png"), 5)
    vm.doubleclick(x, y)
    time.sleep(15)
    vm.send_key("meta_l-up")
    time.sleep(10)


def _firefox_open_browser_and_search(search_term):
    global vm
    check_vm_running()
    firefox_open_browser_from_desktop()
    vm.send_key("ctrl-l")
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Firefox - Initial search for: " + search_term)
    vm.send_text(str(search_term))
    time.sleep(1)
    vm.send_key("ret")
    time.sleep(15)
    capture_screenshot("firefox_open_browser_and_search")


def firefox_open_new_tab_and_search(search_term, *args):
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Firefox - New tab and searching for: " + search_term)
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "firefox_new_tab.png"), 5)
    vm.leftclick(x, y)
    vm.send_text(str(search_term))
    time.sleep(1)
    vm.send_key("ret")
    time.sleep(15)
    capture_screenshot("firefox_open_new_tab_and_search")
    _firefox_google_running_click_links(*args)


def notepad_create_document(filename, content, *args):
    notepad_start()
    capture_screenshot("notepad_create_document_start")
    write_text(content)
    capture_screenshot("notepad_create_document_write_text")
    notepad_save_document_close(filename, args)


def notepad_start():
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Notepad - start")
    (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "win_menu.png"), 5)
    vm.leftclick(x, y)
    time.sleep(1)
    vm.send_text(str("Notepad"))
    time.sleep(1)
    vm.send_key("ret")
    time.sleep(3)


# this should probably be in the pyautoqemu/vm control automation tool instead ...
def write_text(content):
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Writing text: " + content)
    vm.send_text(content)
    time.sleep(3)


# currently always saving in base document directory
def notepad_save_document_close(filename, *args):
    global vm
    check_vm_running()
    time.sleep(60)
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Notepad - save document as: " + filename)
    vm.send_key("ctrl-s")
    time.sleep(1)
    write_text(filename)
    time.sleep(3)
    capture_screenshot("notepad_create_document_save")
    vm.send_key("ret")
    time.sleep(1)
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Notepad close")
    vm.send_key("ctrl-w")
    time.sleep(5)


# def firefox_google_click_on_search_results_by_icon(): # e.g. wikipedia


def _firefox_google_running_click_links(*args):
    global vm
    check_vm_running()
    # Random 2 to 5 times: Try to click on a search result, check success criterion, proceed
    num_times = random.randint(1, 3)
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
          "Firefox - Selecting number of links to click:" + str(num_times))
    for i in range(num_times):

        (x, y) = vm.tesseract_find_scroll("https", 10, False, ymin=70) # identify search results via "https" text in links, exclude currently visited url in browser bar from ocr by restricting ymin
        vm.leftclick(x, y)
        time.sleep(10)
        try:
            j = i + 1
            vm.cv_wait(os.path.join(config.templates_dir, "google_surf_failure.png"), 5)
            print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Round", j,
                  "No success: Failure Indicator template found.")
            activity = "surf_to_result_fail_round" + str(j)
            capture_screenshot(activity)
            vm.send_key("pgdn")
            time.sleep(1)
        except RuntimeError:
            j = i + 1
            print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Round", j,
                  "Success: Failure Indicator template not found.")
            activity = "surf_to_result_success_round" + str(j)
            stay_on_page = random.randint(5, 30) # currently waiting on each page for 5 to 30 seconds
            time.sleep(stay_on_page)
            capture_screenshot(activity)
            (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "firefox_go_back.png"), 5)
            vm.leftclick(x, y)
            time.sleep(5)
            vm.send_key("pgdn")
            time.sleep(1)
            vm.send_key("pgdn")


def firefox_simple_initial_google_search_session(search_term, *args):
    _firefox_open_browser_and_search(search_term)
    _firefox_google_running_click_links(*args)


def firefox_simple_followup_google_search_session(search_term, *args):
    _firefox_google_running_and_search_term(search_term)
    _firefox_google_running_click_links(*args)


# only works if something else has been searched on google before and we are still on google
def _firefox_google_running_and_search_term(search_term):
    global vm
    check_vm_running()
    print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), "Firefox - same tab and searching for: " + search_term)
    vm.send_key("ctrl-l")
    vm.send_text(str(search_term))
    time.sleep(1)
    vm.send_key("ret")
    time.sleep(15)
    capture_screenshot("firefox_same_tab_search")


# def firefox_close_active_tabs(tab_count=2):
#     global vm
#     check_vm_running()
#     for _ in range(tab_count):
#         (x, y) = vm.cv_wait(os.path.join(config.templates_dir, "firefox_close_active_tab.png"), 15)
#         vm.leftclick(x, y)
