import paho.mqtt.client as mqtt
import ssl
import certifi
import schedule
import time
import json
import platform
import uuid
from datetime import datetime
# --- IMPORT PERSISTENCE FUNCTIONS ---
import persistence # Changed slightly to ensure correct import if needed, but original was 'from persistence import ...'
from persistence import load_schedules, save_schedules, load_clients, save_clients ,save_switches, load_switches ,load_switches_state, save_switches_state
# ------------------------------------

# =================================================================
# --- 1. CONFIGURATION ---
# =================================================================

BROKER_ADDRESS = "b79f9ebae0ab4f2fb4478ac4ee286e33.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "rajendra"
PASSWORD = "Root1234"

KEEPALIVE = 60
    

CONTROL_TOPIC = "myhome/scheduler/submit_job"
PING_TOPIC = "myhome/scheduler/ping"          # Topic to receive ping requests
STATUS_TOPIC = "myhome/scheduler/status"      # Topic to publish pong/status responses
LIST_JOBS_TOPIC = "myhome/scheduler/list_jobs"  # Topic to request list of all jobs
ACTIVE_CLIENT_TOPIC = "active_client"

# --- NEW DELETION TOPICS ---
DELETE_JOB_TOPIC = "myhome/scheduler/delete_job"      # Topic to receive a specific job to delete
DELETE_ALL_TOPIC = "myhome/scheduler/delete_all_jobs" # Topic to delete all jobs
# ---------------------------
# --- NEW CLIENT TOPICS ---
CLIENT_REQUEST_TOPIC = "+/request/clients"            # Topic to receive requests for client list
# ---------------------------
# --- NEW SWITCH TOPICS ---
SWITCH_CREATE_TOPIC = "+/create/switch"            # Topic to receive requests for switch list
# ---------------------------
SWITCH_STATE_TOPIC = "+/command"            # Topic to receive requests for switch list
# ---------------------------


# Global list to hold the raw JSON data for all active jobs
PERSISTENT_JOBS = [] 
# Global dict to hold active clients
ACTIVE_CLIENTS = {} 
# Global dict to hold all switches
ALL_SWITCHES = load_switches()
# Global dict to hold all switches state
ALL_SWITCHES_STATE = load_switches_state()



# =================================================================
# --- 2. CORE LOGIC & MQTT SETUP ---
# =================================================================

def get_client_id():
    """Generates a unique client ID based on OS and MAC address."""
    mac = uuid.getnode()
    mac_address = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    return f"{platform.system()}_{mac_address}"

CLIENT_ID = get_client_id()
print(f"Generated Client ID: {CLIENT_ID}")

client = mqtt.Client(client_id=CLIENT_ID)

def _delete_job_entry(job_data_to_delete):
    """
    Helper function to remove a job from the schedule library and the global persistence list.
    Returns the number of jobs deleted (0 or 1).
    """
    global PERSISTENT_JOBS
    topic = job_data_to_delete.get("topic")
    payload = job_data_to_delete.get("payload")
    time_value = job_data_to_delete.get("time")
    deleted_count = 0
    
    # 1. Find and cancel the job in the schedule library
    jobs = schedule.default_scheduler.get_jobs(tag="dynamic")
    
    # We must iterate over a copy of the list if we modify the list during iteration.
    # However, schedule.get_jobs() returns a copy, so modifying schedule using cancel_job is safe.
    for job in jobs:
        # A simple but reliable way to match is checking if the specific topic/payload/time 
        # is present in the string representation of the job's wrapper function.
        if topic in str(job.job_func) and payload in str(job.job_func):
            schedule.cancel_job(job)
            print(f"  -> CANCELED from schedule: {job}")
            deleted_count = 1 # We assume a unique job based on topic/payload/time
            break # Exit after finding and cancelling the job

    # 2. Remove from the global persistence list (match all 4 fields for safety)
    initial_length = len(PERSISTENT_JOBS)
    PERSISTENT_JOBS = [j for j in PERSISTENT_JOBS if not (
        j.get("type") == job_data_to_delete.get("type") and
        j.get("topic") == topic and 
        j.get("payload") == payload and 
        j.get("time") == time_value
    )]
    
    # 3. Save the updated list if any changes occurred
    if len(PERSISTENT_JOBS) < initial_length:
        save_schedules(PERSISTENT_JOBS)
        print("  -> SAVED: Updated persistence file.")
    elif deleted_count == 1:
        # This covers cases where the job might have been canceled in schedule but failed to save last time.
        # We still save the persistence list to ensure consistency.
        save_schedules(PERSISTENT_JOBS)
        
    return deleted_count

def publish_status(topic, payload):
    # ... (same as before)
    if client.is_connected():
        result = client.publish(topic, payload)
        # ... (logging logic remains the same)
        status = result[0]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if status == mqtt.MQTT_ERR_SUCCESS:
            print(f"[{current_time}] PUBLISHED: '{payload}' to Topic: {topic}")
        else:
            print(f"[{current_time}] FAILED to publish message to Topic: {topic}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Client not connected. Skipping publish.")


def _create_schedule_job(job_data):
    """Helper to register a job with the 'schedule' library."""
    global PERSISTENT_JOBS
    schedule_type = job_data.get("type") 
    topic = job_data.get("topic")
    payload = job_data.get("payload")
    time_value = job_data.get("time")

    def job_action_wrapper():
        # Execute the primary task
        publish_status(topic, payload)

        # --- LOGIC FOR ONE-TIME JOB CANCELLATION ---
        if schedule_type == "once":
            # Cancellation logic remains here, but now calls save_schedules() from the imported module
            
            # Find and cancel the job in the schedule library
            jobs = schedule.default_scheduler.get_jobs(tag="dynamic")
            for job in jobs:
                if topic in str(job.job_func) and payload in str(job.job_func):
                    schedule.cancel_job(job)
                    print(f"  -> CANCELED: One-time job finished and cancelled itself: {job}")
                    
                    # Remove from the global persistence list
                    global PERSISTENT_JOBS
                    PERSISTENT_JOBS = [j for j in PERSISTENT_JOBS if not (j.get("topic") == topic and j.get("payload") == payload and j.get("time") == time_value)]
                    
                    # --- CALL THE IMPORTED SAVE FUNCTION ---
                    save_schedules(PERSISTENT_JOBS)
                    # --------------------------------------
                    return
    
    # Register the job with the schedule library
    if schedule_type == "daily" and isinstance(time_value, str):
        schedule.every().day.at(time_value).do(job_action_wrapper).tag("dynamic")
        print(f"  -> SCHEDULED DAILY at {time_value}: publish '{payload}' to {topic}")
    elif schedule_type == "interval" and isinstance(time_value, int):
        schedule.every(time_value).seconds.do(job_action_wrapper).tag("dynamic")
        print(f"  -> SCHEDULED INTERVAL ({time_value} seconds): publish '{payload}' to {topic}")
    elif schedule_type == "once" and isinstance(time_value, str):
        schedule.every().day.at(time_value).do(job_action_wrapper).tag("dynamic")
        print(f"  -> SCHEDULED ONCE at {time_value}: publish '{payload}' to {topic}. Will self-cancel.")


def on_connect(client, userdata, flags, rc):
    # ... (same as before)
    if rc != 0: 
        print(f"Failed to connect, return code {rc}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to MQTT Broker!")
        
        # Subscribe to control topic for job submissions
        client.subscribe(CONTROL_TOPIC)
        print(f"Subscribed to control topic: {CONTROL_TOPIC}")
        
        # Subscribe to ping topic for health checks
        client.subscribe(PING_TOPIC)
        print(f"Subscribed to ping topic: {PING_TOPIC}")
        
        # Subscribe to list jobs topic
        client.subscribe(LIST_JOBS_TOPIC)
        print(f"Subscribed to list jobs topic: {LIST_JOBS_TOPIC}")

        # --- NEW SUBSCRIPTIONS ---
        client.subscribe(DELETE_JOB_TOPIC)
        print(f"Subscribed to specific job deletion topic: {DELETE_JOB_TOPIC}")
        
        client.subscribe(DELETE_ALL_TOPIC)
        print(f"Subscribed to delete all jobs topic: {DELETE_ALL_TOPIC}")
        client.subscribe(ACTIVE_CLIENT_TOPIC)
        print(f"Subscribed to active client topic: {ACTIVE_CLIENT_TOPIC}")
        client.subscribe(CLIENT_REQUEST_TOPIC)
        print(f"Subscribed to client request topic: {CLIENT_REQUEST_TOPIC}")
        client.subscribe(SWITCH_CREATE_TOPIC)
        print(f"Subscribed to switch create topic: {SWITCH_CREATE_TOPIC}")
        client.subscribe(SWITCH_STATE_TOPIC)
        print(f"Subscribed to switch state topic: {SWITCH_STATE_TOPIC}")    

        
        # Publish initial status message
        status_msg = json.dumps({
            "client_id": CLIENT_ID,
            "type": "scheduler_service",
            "status": "online",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "active_jobs": len(PERSISTENT_JOBS)
        })
        client.publish(STATUS_TOPIC, status_msg, retain=True)
        print(f"Published online status to {STATUS_TOPIC}")
        presence_payload = {"id":CLIENT_ID, "status": "connected"}
        client.publish(ACTIVE_CLIENT_TOPIC, json.dumps(presence_payload), retain=True)
        print(f"Published online status to {ACTIVE_CLIENT_TOPIC}")

def on_message(client, userdata, msg):
    """Receives new job commands and ping requests."""
    
    global PERSISTENT_JOBS, ACTIVE_CLIENTS  # Declare at the top of the function
    
    # Handle ping requests for health checks
    if msg.topic == PING_TOPIC:
        try:
            payload = msg.payload.decode('utf-8').strip()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received PING request: '{payload}'")
            
            # Prepare pong response with status information
            pong_response = json.dumps({
                "status": "alive",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active_jobs": len(schedule.default_scheduler.get_jobs()),
                "total_persistent_jobs": len(PERSISTENT_JOBS),
                "ping_received": payload if payload else "ping"
            })
            
            client.publish(STATUS_TOPIC, pong_response)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent PONG response to {STATUS_TOPIC}")
            
        except Exception as e:
            print(f"ERROR handling ping: {e}")
    
    # Handle list jobs requests
    elif msg.topic == LIST_JOBS_TOPIC:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received LIST JOBS request")
            
            # Prepare response with all current jobs
            jobs_response = json.dumps({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_jobs": len(PERSISTENT_JOBS),
                "jobs": PERSISTENT_JOBS
            }, indent=2)
            
            client.publish(STATUS_TOPIC, jobs_response)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {len(PERSISTENT_JOBS)} job(s) to {STATUS_TOPIC}")
            
        except Exception as e:
            print(f"ERROR handling list jobs request: {e}")
    
    # Handle job submission requests
    elif msg.topic == CONTROL_TOPIC:
        try:
            job_data = json.loads(msg.payload.decode('utf-8'))
            
            if not all([job_data.get("type"), job_data.get("topic"), job_data.get("payload"), job_data.get("time")]):
                print("ERROR: Job data is incomplete.")
                error_msg = json.dumps({
                    "status": "error",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": "ERROR: Job data is incomplete."
                })
                client.publish(STATUS_TOPIC, error_msg, retain=True)
                return

            print("-" * 30)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received New Job Request.")
            
            # --- CHECK FOR DUPLICATE JOBS ---
            # Check if this exact job already exists
            is_duplicate = False
            for existing_job in PERSISTENT_JOBS:
                if (existing_job.get("type") == job_data.get("type") and
                    existing_job.get("topic") == job_data.get("topic") and
                    existing_job.get("payload") == job_data.get("payload") and
                    existing_job.get("time") == job_data.get("time")):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                error_msg = json.dumps({
                    "status": "error",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": "DUPLICATE JOB DETECTED - Job already exists in schedule!"
                })
                print("⚠️  DUPLICATE JOB DETECTED - Job already exists in schedule!")
                client.publish(STATUS_TOPIC, error_msg, retain=True)

                print(f"   Type: {job_data.get('type')}, Topic: {job_data.get('topic')}, "
                      f"Payload: {job_data.get('payload')}, Time: {job_data.get('time')}")
                print("   Skipping duplicate job.")
                print("-" * 30)
                return
            # --------------------------------
            
            # 1. Register the job with the schedule library
            _create_schedule_job(job_data)
            
            # 2. Add the job to the persistent list
            PERSISTENT_JOBS.append(job_data)
            
            # 3. Save the new list to the file using the imported function
            save_schedules(PERSISTENT_JOBS)
            print("-" * 30)
            
        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from topic {CONTROL_TOPIC}. Payload: {msg.payload}")
            error_msg = json.dumps({
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "ERROR: Failed to decode JSON from topic {CONTROL_TOPIC}. Payload: {msg.payload}"
            })
            client.publish(STATUS_TOPIC, error_msg, retain=True)
        except Exception as e:
            print(f"CRITICAL ERROR during scheduling: {e}")
            error_msg = json.dumps({
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"CRITICAL ERROR during scheduling: {e}"
            })
            client.publish(STATUS_TOPIC, error_msg, retain=True)
        # ===============================================================
    # --- NEW: Handle Delete Specific Job Request ---
    # ===============================================================
    elif msg.topic == DELETE_JOB_TOPIC:
        try:
            job_data_to_delete = json.loads(msg.payload.decode('utf-8'))
            print("-" * 30)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received Delete Job Request.")
            
            # Ensure the payload has the necessary fields to identify the job
            if not all([job_data_to_delete.get("type"), job_data_to_delete.get("topic"), job_data_to_delete.get("payload"), job_data_to_delete.get("time")]):
                print("ERROR: Delete job data is incomplete (requires type, topic, payload, and time).")
                return

            deleted_count = _delete_job_entry(job_data_to_delete)
            
            response = json.dumps({
                "status": "job_deleted",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Job deletion attempted. Deleted {deleted_count} job(s).",
                "job": job_data_to_delete
            })
            client.publish(STATUS_TOPIC, response)
            print(f"Published deletion status to {STATUS_TOPIC}")
            print("-" * 30)
            
        except json.JSONDecodeError:
            print(f"ERROR: Failed to decode JSON from topic {DELETE_JOB_TOPIC}. Payload: {msg.payload}")
            error_msg = json.dumps({
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"ERROR: Failed to decode JSON from topic {DELETE_JOB_TOPIC}. Payload: {msg.payload}"
            })
            client.publish(STATUS_TOPIC, error_msg, retain=True)
        except Exception as e:
            print(f"CRITICAL ERROR during specific job deletion: {e}")
            error_msg = json.dumps({
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"CRITICAL ERROR during specific job deletion: {e}"
            })
            client.publish(STATUS_TOPIC, error_msg, retain=True)

    # ===============================================================
    # --- NEW: Handle Delete ALL Jobs Request ---
    # ===============================================================
    elif msg.topic == DELETE_ALL_TOPIC:
        try:
            print("-" * 30)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received DELETE ALL Jobs Request!")
            
            jobs_before = len(PERSISTENT_JOBS)
            
            # 1. Clear the schedule library
            schedule.clear("dynamic")
            
            # 2. Clear the global persistence list
            PERSISTENT_JOBS.clear()
            
            # 3. Save the empty list to the file
            save_schedules(PERSISTENT_JOBS)
            
            response = json.dumps({
                "status": "all_jobs_deleted",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"SUCCESS: Cleared all {jobs_before} persistent and scheduled jobs."
            })
            client.publish(STATUS_TOPIC, response)
            print("  -> CLEARED: All jobs cancelled and persistence saved.")
            print(f"Published status to {STATUS_TOPIC}")
            print("-" * 30)
            
        except Exception as e:
            print(f"CRITICAL ERROR during delete all jobs: {e}")
            error_msg = json.dumps({
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"CRITICAL ERROR during delete all jobs: {e}"
            })
            client.publish(STATUS_TOPIC, error_msg, retain=True)

    # ===============================================================
    # --- NEW: Handle Active Client Updates ---
    # ===============================================================
    elif msg.topic == ACTIVE_CLIENT_TOPIC:
        try:
            payload_data = json.loads(msg.payload.decode('utf-8'))
            client_id = payload_data.get("id")
            status = payload_data.get("status")
            
            if client_id:
                # Update the client data
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ACTIVE_CLIENTS[client_id] = {
                    "id": client_id,
                    "status": status,
                    "last_seen": current_time,
                    "payload": payload_data # Store full payload in case of extra fields
                }
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Client Update: {client_id} is {status}")
                save_clients(ACTIVE_CLIENTS)
                
        except Exception as e:
            print(f"ERROR handling active client update: {e}")

    # ===============================================================
    # --- NEW: Handle Client List Request ---
    # ===============================================================
    elif msg.topic.endswith("/request/clients"):
        try:
            # Decode and parse payload to check for self-echo
            try:
                payload_str = msg.payload.decode('utf-8')
                data = json.loads(payload_str)
            except:
                data = {} # Treat non-JSON/empty as a valid request

            # STOP LOOP: If the payload contains 'clients', it is our own response echoing back.
            if isinstance(data, dict) and "clients" in data:
                return

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received Client List Request on {msg.topic}")
            
            # Convert dictionary keys/values to list for publishing
            client_list_response = []
            for cid, cdata in ACTIVE_CLIENTS.items():
                # Create a copy so we don't permanently alter ACTIVE_CLIENTS in memory
                merged_data = cdata.copy()
                # Attach switches if they exist for this specific client ID
                client_switches = ALL_SWITCHES.get(cid, [])
                
                # Merge state for each switch
                merged_switches = []
                for switch in client_switches:
                    s_copy = switch.copy()
                    s_id = s_copy.get("id")
                    if cid in ALL_SWITCHES_STATE:
                        s_copy.update(ALL_SWITCHES_STATE[cid])
                    elif s_id and s_id in ALL_SWITCHES_STATE:
                        s_copy.update(ALL_SWITCHES_STATE[s_id])
                    merged_switches.append(s_copy)
                
                merged_data["switches"] = merged_switches
                client_list_response.append(merged_data)

            response = json.dumps({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_clients": len(client_list_response),
                "clients": client_list_response # This now matches your requested structure
            }, indent=4)
            
            client.publish(msg.topic, response)
            print(f"Sent merged client/switch list to {msg.topic}")            
        except Exception as e:
            print(f"ERROR handling client list request: {e}")
    elif msg.topic.endswith("/create/switch"):
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            client_id = data.get("client_id")
            structure = data.get("structure")

            if client_id and structure:
                # Generate a unique ID if not present
                if "id" not in structure:
                    structure["id"] = f"{client_id}/{uuid.uuid4().hex[:8]}"
                
                # Initialize list for this client if it doesn't exist
                if client_id not in ALL_SWITCHES:
                    ALL_SWITCHES[client_id] = []
                
                # Prevent duplicate structures (topic check)
                new_topic = structure.get("topic")
                if new_topic:
                    is_duplicate = False
                    for existing_switch in ALL_SWITCHES[client_id]:
                        if existing_switch.get("topic") == new_topic:
                            is_duplicate = True
                            break
                    
                    if is_duplicate:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Switch with topic '{new_topic}' already exists for client {client_id}. Skipping creation.")
                        # Optional: Publish an error back to status topic
                        error_resp = json.dumps({"status": "error", "message": f"Topic {new_topic} already exists."})
                        client.publish(STATUS_TOPIC, error_resp)
                        return

                ALL_SWITCHES[client_id].append(structure)
                
                save_switches(ALL_SWITCHES)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved new switch for {client_id}")
        except Exception as e:
            print(f"ERROR creating switch: {e}")
    elif msg.topic.endswith("/command"):
        try:
            device_id  = msg.topic.split("/")[-2]
            state = msg.payload.decode('utf-8')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ALL_SWITCHES_STATE[device_id] = {
                "state": state,
                "time": current_time
            }
            save_switches_state(ALL_SWITCHES_STATE)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Switch State Updated: {device_id} -> {state}")
        except Exception as e:
            print(f"ERROR updating switch state: {e}")

# Set the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Add authentication if needed
if USERNAME and PASSWORD:
    client.username_pw_set(USERNAME, PASSWORD)

# Enable TLS for HiveMQ Cloud (Port 8883)
client.tls_set(ca_certs=certifi.where())

# =================================================================
# --- 4. EXECUTION STARTUP ---
# =================================================================

# 1. Load any previously saved jobs BEFORE connecting to the broker
jobs_to_recreate = load_schedules()
for job_data in jobs_to_recreate:
    PERSISTENT_JOBS.append(job_data) # Re-populate the runtime list
    _create_schedule_job(job_data)   # Recreate job in the scheduler

# 1.5 Load known clients
ACTIVE_CLIENTS = load_clients()

# 2. Connect to the broker
try:
    print(f"\nAttempting to connect to {BROKER_ADDRESS}:{PORT}...")
    
    # Set Last Will and Testament (LWT) for disconnection
    will_msg = json.dumps({
        "id": CLIENT_ID,
        "status": "disconnected",
        "timestamp": "unexpected_disconnect",
        "type": "scheduler_service"
    })
    client.will_set(ACTIVE_CLIENT_TOPIC, will_msg, retain=True)
    
    client.connect(BROKER_ADDRESS, PORT, KEEPALIVE)
    client.loop_start() 
except Exception as e:
    print(f"Could not connect to broker: {e}")
    exit(1)

print("\nScheduler Initialized and Running.")
print(f"System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Waiting for Commands on: {CONTROL_TOPIC}")

# 3. Main Loop
while True:
    schedule.run_pending()
    time.sleep(1)