#!/usr/bin/env python3
"""
MQTT Scheduler Ping Test
Sends a ping to the scheduler and waits for a pong response.
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

BROKER = "broker.hivemq.com"
PORT = 1883
PING_TOPIC = "myhome/scheduler/ping"
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
        
        # Wait a moment then send ping
        time.sleep(0.5)
        client.publish(PING_TOPIC, "ping")
        print(f"✓ Sent ping to {PING_TOPIC}")
        print("\nWaiting for response...")

def on_message(client, userdata, msg):
    global response_received
    
    if msg.topic == STATUS_TOPIC:
        response_received = True
        try:
            status = json.loads(msg.payload.decode('utf-8'))
            
            print("\n" + "="*50)
            print("📡 SCHEDULER STATUS RECEIVED")
            print("="*50)
            print(f"Status:        {status.get('status', 'unknown')}")
            print(f"Timestamp:     {status.get('timestamp', 'N/A')}")
            print(f"Active Jobs:   {status.get('active_jobs', 0)}")
            print(f"Persistent:    {status.get('total_persistent_jobs', 0)}")
            print(f"Ping Echo:     {status.get('ping_received', 'N/A')}")
            print("="*50)
            
            if status.get('status') in ['alive', 'online']:
                print("\n✅ Scheduler is ALIVE and CONNECTED!")
            else:
                print("\n⚠️  Scheduler responded but status is unusual")
                
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
