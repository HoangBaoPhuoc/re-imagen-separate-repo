import csv
import json
import os
import random
from datetime import datetime

from activity_mapping import ACTIVITY_MAPPINGS
from sys_specs import SYS_SPECS
from shared import config

# Global variable to track state of Firefox
firefox_closed = True  # Indicates whether Firefox is currently closed


def load_json_file(filename):
    """
        Loads and parses a JSON file.
    """
    with open(filename, 'r') as file:
        data = json.load(file)
    return data


def extract_time_activity_args_pairs(parsed_data):
    """
        Extracts (time, activity, *args) tuples from parsed JSON data.
    """
    time_activity_args_pairs = []

    for item in parsed_data:
        # Ensure mandatory fields 'time' and 'activity' are present
        if 'time' in item and 'activity' in item:
            # Create base tuple with non-optional fields
            attributes_tuple = (item['time'], item['activity'])
            # If present: Include any optional fields
            for key, value in item.items():
                if key not in ['time', 'activity']:
                    attributes_tuple += (value,)
            # Add tuple to result list
            time_activity_args_pairs.append(attributes_tuple)
        else:
            raise KeyError(f"Missing required fields in item: {item}")

    return time_activity_args_pairs


def generate_csv_rows_for_single_activity(time, activity, *further_args):
    """
        Generates CSV rows for a single activity based on system type and activity mappings.
    """

    global firefox_closed

    # Get system type
    system_type = SYS_SPECS.get('type')

    # Check if system type is supported
    if system_type not in ACTIVITY_MAPPINGS:
        raise ValueError(f"No activity implementation found for system type: {system_type}")

    rows = []
    args = []

    # Retrieve activity mapping for system type
    mapping = ACTIVITY_MAPPINGS[system_type].get(activity, {})

    # Check if activity is supported for given system type
    if not mapping:
        raise ValueError(f"No activity implementation found for activity: {activity}")

    # Handle activities based on their execution mode
    if mapping['mode'] == 'sequential':
        # Execute sequentially
        for command in mapping['commands']:
            # Add password and mark Firefox as closed
            if command == 'login_single_user':
                args.append(SYS_SPECS['password'])
                firefox_closed = True
            rows.append([time, command] + args + list(further_args))

    elif mapping['mode'] == 'conditional':
        # Handle conditional commands
        if activity == 'google_search':
            # If Firefox is closed, use the first command
            if firefox_closed:
                command = mapping['commands'][0]
                firefox_closed = False # Update state
            else:
                # Otherwise, choose randomly from remaining options
                command = random.choice(mapping['commands'][1:])
            rows.append([time, command] + args + list(further_args))

    return rows


def generate_csv_for_activities(time_activity_args_pairs):
    """
        Generates a list of CSV rows for all time-activity pairs from a list of (time, activity, *args) tuples.
    """
    all_rows = []
    for pair in time_activity_args_pairs:
        time = pair[0]
        activity = pair[1] # Activity name
        further_args = pair[2:]
        # Generate rows for single activity and add them to the overall list
        rows = generate_csv_rows_for_single_activity(time, activity, *further_args)
        all_rows.extend(rows) # Merge new rows into main list
    return all_rows


def write_to_csv(filename, rows):
    """
       Writes a list of rows to a CSV file.
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


def check_ads_validity(time_activity_args_pairs):
    """
        Validates activity description script by checking:
        1. Times are in ascending order.
        2. Proper sequence of computer_on and computer_off activities.
    """
    # check that times are in correct order
    time_strings = [entry[0] for entry in time_activity_args_pairs]
    times = [datetime.fromisoformat(time_string.replace("Z", "+00:00")) for time_string in time_strings]
    if not all(times[i] <= times[i + 1] for i in range(len(times) - 1)):
        raise RuntimeError("Activity Description Script invalid: Times not in ascending order")

    # Check that computer_on and computer_off follow a valid sequence
    computer_state = 'off' # Start with computer being off
    for entry in time_activity_args_pairs:
        activity = entry[1]
        if activity == 'computer_on':
            if computer_state == 'on':
                raise RuntimeError(
                    "Activity Description Script invalid: computer_on activity not followed by computer_off")  # TODO: or more: without off before on again
            computer_state = 'on'
        elif activity == 'computer_off':
            # Ensure no consecutive computer_off activities
            if computer_state == 'off':
                raise RuntimeError(
                    "Activity Description Script invalid: computer_off activity without preceding computer_on")
            computer_state = 'off'


if __name__ == "__main__":
    # Define paths for shared directory and files
    json_filename = os.path.join(config.shared_dir, config.script_base_file_name + ".json")
    csv_filename = os.path.join(config.shared_dir, config.script_base_file_name + ".csv")

    try:
        # 1. Load and parse the JSON file (activity desc. script)
        parsed_data = load_json_file(json_filename)
        # 2. Extract time-activity pairs
        time_activity_args_pairs = extract_time_activity_args_pairs(parsed_data)
        # 3. Validate activity description script
        check_ads_validity(time_activity_args_pairs)
        # 4. Generate CSV rows for the activities in vm interaction script
        rows = generate_csv_for_activities(time_activity_args_pairs)
        # 5. Write generated rows to CSV
        write_to_csv(csv_filename, rows)

        print(f"Successfully translated Activity Description Script to VM Interaction Script and saved to '{csv_filename}'.")

    except FileNotFoundError:
        print(f"Error: File '{json_filename}' not found.")

    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON from '{json_filename}'. Please check the file for valid JSON format.")

    except Exception as e:
        print(f"Script translation failed with error: {e}")

