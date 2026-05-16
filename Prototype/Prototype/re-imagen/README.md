# Installation

For our demonstration, we used an Ubuntu 22.04 host machine with _qemu-system-x86_ installed.

`~$ apt-get install qemu-system-x86`

We set up the Re-imagen project in a Python venv. Our OCR patch for pyautoqemu has to be applied after pulling the original pyautoqemu repo (that is included in the requirements.txt).

# Preparation of a Simulation Run

There is some initial preparation effort required, before the interaction with the target VM can be carried out in automated manner. In the following, we describe how we prepared our [Demonstration Examples](https://github.com/lenavoigt/re-imagen/tree/main/Demonstration-Examples).

## Initial Creation and Configuration of the target VM

To set up the target VMs we used for our demonstration, we proceeded as described in the following. It should be noted that some steps of the preparation was only neccessary to improve performance.

**Set up target VM using Virtualbox**

- 4096 MB memory, 4 cpus
- Windows 10 Home (64bit, Version 22H2)
  - keyboard layout: qwerty (US-international)
  - language: English (UK)
  - Time and currency: German
  - username and password matching the scenario (e.g. for [Example 1](https://github.com/lenavoigt/re-imagen/tree/main/Demonstration-Examples/Example1-Maximilian): "Maximilian", "12345678")
- Disable Startup Applications and Background Applications

**Convert vdi to qcow2 file**

`~$ qemu-img convert -O qcow2 <windows10>.vdi <windows10>.qcow2`

**Start and further preparation of the VM**

Start the VM using qemu:

`~$ qemu-system-x86_64 -m 4G -enable-kvm -cpu host -device qemu-xhci -device usb-tablet -vga std -rtc base=localtime -qmp tcp:localhost:4444,server,nowait <windows10>.qcow2`

Prepare the system for the simulation:

- Firefox:
  - Install Firefox (Version 116.0.1)
  - Accept Google cookies
  - Disable translator popup (enter `about:config` in the address bar and set `browser.translations.automaticallyPopup = false`)
  - Disable session restores (in ``about:config`: set `browser.sessionstore.max_resumed_crashes`to`0```)
- Microsoft Store: Disable automatic updates and live tile in microsoft store
- Screen resolution: 1920x1080, scaling 100%
- Windows updates: Pause

**Preparation for the automation with pyautoqemu**

- Create templates/screenshots of the GUI elements that should be interacted with via mouse clicks during the scenario.
  - _Note: We observed that the host resolution needs to be set to 2560x1440 or less when creating the screenshots. For us, a host resolution of 2560x1600, 100% Scale worked._
- Shutdown the VM, create a copy of the qcow2 file (to be used as a backup of the base image for the VM)

## Required Files

To be able to run the Re-imagen translator module:

- Activity Description Script, final output of the LLM interaction ([Example](https://github.com/lenavoigt/re-imagen/blob/main/Demonstration-Examples/Example1-Maximilian/Activity-Description-Script_Maximilian.json))

To be able to run the Re-imagen VM instruction module:

- VM Interaction Script as it is output by the Translator module ([Example](https://github.com/lenavoigt/re-imagen/blob/main/Demonstration-Examples/Example1-Maximilian/VM-Interaction-Script_Maximilian.csv))
- Disk of a VM prepared in advance, see above (windows10.qcow2)
- [Templates](https://github.com/lenavoigt/re-imagen/tree/main/Prototype/re-imagen/shared/templates) for GUI interaction using pyautoqemu, prepared in advance (see below)

## Templates

As required by _pyautoqemu_, templates of the GUI elements that should be interacted with during VM control automation have to be provided.

While we provide the templates we used for the prototype implementation, to run the prototype code, the templates in the shared/templates directory need to be replaced with screenshots of the respective GUI elements of the VM configured for an example run.

In particular, to run our prototype, we used the following templates:

- win_menu.png: Windows Menu button
- win_menu_onoff.png: On/off button within the Windows Menu
- win_menu_shutdown.png: Shutdown button within the on/off menu
- firefox_desktop.png: Firefox icon, desktop shortcut
- firefox_go_back.png: Button within Firefox to navigate to the previously visited website
- firefox_google_new_search.png: Button within Google search bar in Firefox to conduct a new (consecutive) search
- firefox_close_active_tab.png: Button within Firefox to clase an active tab
- firefox_new_tab.png: Button within Firefox to open a new tab
- google_surf_failure.png: Failure indicator for a google search (e.g. Google searchbar that is still visible, when we should have navigated to a search result)

Note: During our experiments we observed, that (when using pyautoqemu) GUI interaction via mouse clicks is rather unrobust. Therefore, whenever possible, interaction via the keyboard should be preferred.

# How to run Re-imagen - an example

0. Prepare a VM and templates
1. LLM interaction: retrieve an Activity Description Script
2. Re-imagen translator module: translate the Activity Description Script to an VM Interaction Script
3. Re-imagen VM instruction module: use the VM Interaction Script and prepared VM to automate the VM interaction

# Retrieving the final EWF disk image

For our demonstration, we proceeded as follows to create EWF files from the resulting qcow2 files (for further analysis in Autopsy).

Convert qemu disk to raw disk image:

`~$ qemu-img convert -p -O raw windows10.qcow2 windows10.img`

Convert raw disk image to E01:

`~$ ewfacquire -t windows10 windows10.img`

# Potential for Improvement

The code we provide is research code for a prototype and we acknowledge that there is potential for improvement. To give some examples:

- Integration with a VM control automation tool (e.g. [ForTrace++](https://gitlab.com/DW0lf/fortrace)) that is actively maintained and, e.g., provides more functionality to check whether actions were successful/lead to the expected result, to avoid hardcoded sleep times, or to handle unexpected results (e.g., popups).
- Support of further activities and system types
- Usability improvements
