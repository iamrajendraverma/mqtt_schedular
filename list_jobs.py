#!/usr/bin/env python3
"""
List all scheduled jobs from the MQTT scheduler
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

BROKER = "broker.hivemq.com"
PORT = 1883
LIST_JOBS_TOPIC = "myhome/scheduler/list_jobs"
STATUS_TOPIC = "myhome/scheduler/status"

response_received = False

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"❌ Failed to connect to broker: {reason_code}")
        sys.exit(1)
    else:
        print(f"✓ Connected to {BROKER}:{PORT}")
        
        # Subscribe to status topic first
        client.subscribe(STATUS_TOPIC)
        print(f"✓ Subscribed to {STATUS_TOPIC}")
        
        # Wait a moment then request job list
        time.sleep(0.5)
        client.publish(LIST_JOBS_TOPIC, "list")
        print(f"✓ Requested job list from {LIST_JOBS_TOPIC}")
        print("\nWaiting for response...\n")

def on_message(client, userdata, msg):
    global response_received
    
    if msg.topic == STATUS_TOPIC:
        response_received = True
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            
            # Check if this is a jobs list response
            if "jobs" in data:
                print("="*60)
                print("📋 SCHEDULED JOBS")
                print("="*60)
                print(f"Timestamp:   {data.get('timestamp', 'N/A')}")
                print(f"Total Jobs:  {data.get('total_jobs', 0)}")
                print("="*60)
                
                jobs = data.get('jobs', [])
                
                if not jobs:
                    print("\n📭 No jobs currently scheduled.\n")
                else:
                    print()
                    for idx, job in enumerate(jobs, 1):
                        print(f"Job #{idx}:")
                        print(f"  Type:    {job.get('type', 'N/A')}")
                        print(f"  Topic:   {job.get('topic', 'N/A')}")
                        print(f"  Payload: {job.get('payload', 'N/A')}")
                        print(f"  Time:    {job.get('time', 'N/A')}")
                        print()
                
                print("="*60)
            else:
                # This might be a ping response or other status message
                print("ℹ️  Received status message (not job list):")
                print(json.dumps(data, indent=2))
                
        except json.JSONDecodeError:
            print(f"\n⚠️  Received non-JSON response: {msg.payload.decode('utf-8')}")
        
        # Disconnect after receiving response
        client.disconnect()

def on_disconnect(client, userdata, reason_code, properties):
    if not response_received:
        print("\n❌ Disconnected without receiving response")
        print("   Scheduler may be offline or not responding")
        sys.exit(1)

# Create client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Set timeout
print(f"Connecting to {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)

# Run for max 5 seconds
client.loop_start()
time.sleep(5)

if not response_received:
    print("\n⏱️  Timeout: No response received within 5 seconds")
    print("   Scheduler is likely OFFLINE or not connected")
    client.loop_stop()
    sys.exit(1)

client.loop_stop()
