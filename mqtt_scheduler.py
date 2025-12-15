import paho.mqtt.client as mqtt
import schedule
import time
import json
from datetime import datetime
# --- IMPORT PERSISTENCE FUNCTIONS ---
from persistence import load_schedules, save_schedules
# ------------------------------------

# =================================================================
# --- 1. CONFIGURATION ---
# =================================================================

BROKER_ADDRESS = "broker.hivemq.com" 
PORT = 1883        
KEEPALIVE = 60
USERNAME = None    
PASSWORD = None    

CONTROL_TOPIC = "myhome/scheduler/submit_job"
PING_TOPIC = "myhome/scheduler/ping"          # Topic to receive ping requests
STATUS_TOPIC = "myhome/scheduler/status"      # Topic to publish pong/status responses
LIST_JOBS_TOPIC = "myhome/scheduler/list_jobs"  # Topic to request list of all jobs

# Global list to hold the raw JSON data for all active jobs
PERSISTENT_JOBS = [] 


# =================================================================
# --- 2. CORE LOGIC & MQTT SETUP ---
# =================================================================

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

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


def on_connect(client, userdata, flags, reason_code, properties):
    # ... (same as before)
    if reason_code.is_failure: 
        print(f"Failed to connect, return code {reason_code.rc}")
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
        
        # Publish initial status message
        status_msg = json.dumps({
            "status": "online",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "active_jobs": len(PERSISTENT_JOBS)
        })
        client.publish(STATUS_TOPIC, status_msg, retain=True)
        print(f"Published online status to {STATUS_TOPIC}")

def on_message(client, userdata, msg):
    """Receives new job commands and ping requests."""
    
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
                return

            print("-" * 30)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received New Job Request.")
            
            # --- CHECK FOR DUPLICATE JOBS ---
            global PERSISTENT_JOBS
            
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
                print("⚠️  DUPLICATE JOB DETECTED - Job already exists in schedule!")
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
        except Exception as e:
            print(f"CRITICAL ERROR during scheduling: {e}")

# Set the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Add authentication if needed
if USERNAME and PASSWORD:
    client.username_pw_set(USERNAME, PASSWORD)

# =================================================================
# --- 4. EXECUTION STARTUP ---
# =================================================================

# 1. Load any previously saved jobs BEFORE connecting to the broker
jobs_to_recreate = load_schedules()
for job_data in jobs_to_recreate:
    PERSISTENT_JOBS.append(job_data) # Re-populate the runtime list
    _create_schedule_job(job_data)   # Recreate job in the scheduler

# 2. Connect to the broker
try:
    print(f"\nAttempting to connect to {BROKER_ADDRESS}:{PORT}...")
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