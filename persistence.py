import json
import os

SCHEDULE_FILE = "schedules.json"

def load_schedules():
    """Reads schedules from the JSON file. Returns an empty list if file not found or corrupted."""
    
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                jobs_to_load = json.load(f)
            print(f"[PERSISTENCE] Successfully loaded {len(jobs_to_load)} job(s) from {SCHEDULE_FILE}.")
            return jobs_to_load
        
        except (IOError, json.JSONDecodeError) as e:
            print(f"[PERSISTENCE ERROR] Failed to load schedules: {e}. Starting with an empty schedule.")
            return []
    else:
        print("[PERSISTENCE] No persistent schedule file found. Starting fresh.")
        return []


def save_schedules(persistent_jobs_list):
    """Saves the current list of job dictionaries to the JSON file."""
    try:
        with open(SCHEDULE_FILE, 'w') as f:
            # Use indent=4 for human-readable formatting
            json.dump(persistent_jobs_list, f, indent=4)
        print(f"[PERSISTENCE] Scheduler state saved to {SCHEDULE_FILE}.")
    except IOError as e:
        print(f"[PERSISTENCE ERROR] Could not save schedules to file: {e}")

# Note: This file only contains functions and constants, no execution logic.
CLIENTS_FILE = "clients.json"

def load_clients():
    """Reads clients from the JSON file. Returns an empty dict if file not found or corrupted."""
    
    if os.path.exists(CLIENTS_FILE):
        try:
            with open(CLIENTS_FILE, 'r') as f:
                clients_to_load = json.load(f)
            print(f"[PERSISTENCE] Successfully loaded {len(clients_to_load)} client(s) from {CLIENTS_FILE}.")
            # ensure it's a dict (in case it was saved as list previously, though we implement as dict)
            if isinstance(clients_to_load, list):
                 # Convert list to dict keyed by 'id' if possible, or just start fresh if strict
                 temp_dict = {}
                 for c in clients_to_load:
                     if 'id' in c:
                         temp_dict[c['id']] = c
                 return temp_dict
            return clients_to_load
        
        except (IOError, json.JSONDecodeError) as e:
            print(f"[PERSISTENCE ERROR] Failed to load clients: {e}. Starting with an empty client list.")
            return {}
    else:
        print("[PERSISTENCE] No persistent clients file found. Starting fresh.")
        return {}


def save_clients(clients_dict):
    """Saves the current dict of clients to the JSON file."""
    try:
        with open(CLIENTS_FILE, 'w') as f:
            # Use indent=4 for human-readable formatting
            json.dump(clients_dict, f, indent=4)
        print(f"[PERSISTENCE] Client state saved to {CLIENTS_FILE}.")
    except IOError as e:
        print(f"[PERSISTENCE ERROR] Could not save clients to file: {e}")

# Note: This file only contains functions and constants, no execution logic.
SWITCHES_FILE = "switches.json"

def load_switches():
    if os.path.exists(SWITCHES_FILE):
        with open(SWITCHES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_switches(switches_data):
    with open(SWITCHES_FILE, 'w') as f:
        json.dump(switches_data, f, indent=4)

# Note: This file only contains functions and constants, no execution logic.

SWITCHES_STATE_FILE = "switches_state.json"

def load_switches_state():
    if os.path.exists(SWITCHES_STATE_FILE):
        with open(SWITCHES_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_switches_state(switches_state_data):
    with open(SWITCHES_STATE_FILE, 'w') as f:
        json.dump(switches_state_data, f, indent=4)
