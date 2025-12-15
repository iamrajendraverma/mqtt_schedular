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