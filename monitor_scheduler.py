#!/usr/bin/env python3
"""
MQTT Scheduler Continuous Monitor
Continuously monitors the scheduler health by sending periodic pings.
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

BROKER = "broker.hivemq.com"
PORT = 1883
PING_TOPIC = "myhome/scheduler/ping"
STATUS_TOPIC = "myhome/scheduler/status"
PING_INTERVAL = 30  # seconds

def on_connect(client, userdata, flags, reason_code, properties):
    if not reason_code.is_failure:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to broker")
        client.subscribe(STATUS_TOPIC)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Subscribed to {STATUS_TOPIC}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to connect: {reason_code}")

def on_message(client, userdata, msg):
    if msg.topic == STATUS_TOPIC:
        try:
            status = json.loads(msg.payload.decode('utf-8'))
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if status.get('status') == 'alive':
                print(f"[{timestamp}] ✅ Scheduler ALIVE - Active Jobs: {status.get('active_jobs', 0)}, Persistent: {status.get('total_persistent_jobs', 0)}")
            elif status.get('status') == 'online':
                print(f"[{timestamp}] 🟢 Scheduler ONLINE - Jobs: {status.get('active_jobs', 0)}")
            else:
                print(f"[{timestamp}] ⚠️  Scheduler status: {status.get('status', 'unknown')}")
                
        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Invalid response: {msg.payload.decode('utf-8')}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {BROKER}:{PORT}...")
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

print(f"Monitoring scheduler health every {PING_INTERVAL} seconds...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Send ping
        timestamp = datetime.now().strftime('%H:%M:%S')
        client.publish(PING_TOPIC, "health-check")
        print(f"[{timestamp}] 📤 Ping sent...")
        time.sleep(PING_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\nStopping monitor...")
    client.loop_stop()
    client.disconnect()
    print("Disconnected.")
