import csv
import datetime
import os
import time

# from PIL import ImageGrab

import activities

from shared import config


def read_csv(path_to_csv):
    """
        Reads a CSV file (the VM Interaction Script) and returns the rows as a list of lists.
    """
    with open(path_to_csv, 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = [row for row in reader]
    return rows


def execute_single_activity(row):
    """
        Executes a single activity.
    """
    cmd = row[1]   # Activity command name
    args = row[2:]  # Additional arguments for the activity

    try:
        # Find activity function dynamically in the activities module
        activity_function = getattr(activities, cmd)

        # Get current time with timezone information
        local_now = datetime.datetime.now().replace(microsecond=0)
        offset = datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset()
        actual_time = local_now.replace(tzinfo=datetime.timezone(offset)).isoformat()

        # Execute activity with provided arguments
        activity_function(*args)

        # Log activity
        log_activity(actual_time, cmd, *args)
        # capture_screenshot(actual_time, cmd)
    except AttributeError:
        print(f"Unknown command: {cmd}")


def execute_activities(rows):
    """
       Executes a list of activities at their specified times.
    """
    for row in rows:
        # Parse scheduled activity time
        cmd_time = datetime.datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S%z")

        # Wait until scheduled time
        while datetime.datetime.now(datetime.timezone.utc) < cmd_time:
            time.sleep(1)  # wait for 1 second before checking again

        # Execute activity once scheduled time is reached
        execute_single_activity(row)


def log_activity(actual_time, activity_name, *args):
    """
        Logs the execution of an activity to a log file.
    """
    with open(log_filepath, 'a') as log_file:
        log_file.write(f"{actual_time} - Executed activity >{activity_name}< with arguments: {args}\n")


# def capture_screenshot(cmd_time, activity_name):
#     """
#         Captures a screenshot and saves it to the screenshots directory.
#     """
#     # not the nicest way to solve this...
#
#     # Generate a unique screenshot filename
#     screenshot_name = f"screenshot-taken-at{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{activity_name}_{cmd_time}.png"
#     screenshot_path = os.path.join(screenshot_dir, screenshot_name)
#
#     # Capture and save screenshot
#     img = ImageGrab.grab()
#     img.save(screenshot_path)


if __name__ == "__main__":
    # Define file paths for input CSV and log file
    csv_file_name = os.path.join(config.shared_dir, config.script_base_file_name + ".csv")
    rows = read_csv(csv_file_name)

    # Create log filename based on the current time
    log_filename = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z") + ".log"
    log_filepath = os.path.join(config.log_dir, log_filename)

    # Execute activities
    execute_activities(rows)
