# MQTT Scheduler Ping/Pong Health Check

This guide explains how to check if the MQTT scheduler is alive and connected using the built-in ping/pong mechanism.

## Overview

The scheduler listens on a **ping topic** and responds with status information on a **status topic**. This allows any MQTT client to verify the scheduler is running and get real-time information about its state.

## Topics

| Topic | Purpose | Direction |
|-------|---------|-----------|
| `myhome/scheduler/ping` | Send ping requests | Client → Scheduler |
| `myhome/scheduler/status` | Receive status responses | Scheduler → Client |

## How It Works

1. **Client sends** a ping message to `myhome/scheduler/ping`
2. **Scheduler receives** the ping and immediately responds
3. **Scheduler publishes** status information to `myhome/scheduler/status`
4. **Client receives** the pong response with scheduler status

## Response Format

When you ping the scheduler, it responds with a JSON object:

```json
{
  "status": "alive",
  "timestamp": "2025-12-15 18:45:30",
  "active_jobs": 3,
  "total_persistent_jobs": 5,
  "ping_received": "ping"
}
```

**Fields:**

- `status`: Always "alive" if scheduler is running
- `timestamp`: Current time on the scheduler
- `active_jobs`: Number of currently scheduled jobs in memory
- `total_persistent_jobs`: Total jobs saved in persistence
- `ping_received`: Echo of the ping message sent

## Method 1: Using MQTT Explorer (GUI)

### Step 1: Connect to Broker

1. Open MQTT Explorer
2. Connect to `broker.hivemq.com:1883` (or your broker)

### Step 2: Subscribe to Status Topic

1. Click on `myhome/scheduler/status` in the topic tree
2. Or manually subscribe to `myhome/scheduler/status`

### Step 3: Send Ping

1. Click "Publish" button
2. Set topic: `myhome/scheduler/ping`
3. Set message: `ping` (or any text)
4. Click "Publish"

### Step 4: Check Response

- Look at `myhome/scheduler/status` topic
- You should see the JSON response immediately

## Method 2: Using mosquitto_pub/sub (Command Line)

### Terminal 1 - Subscribe to Status

```bash
mosquitto_sub -h broker.hivemq.com -t "myhome/scheduler/status" -v
```

Keep this running to see responses.

### Terminal 2 - Send Ping

```bash
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/ping" -m "ping"
```

### Expected Output in Terminal 1

```
myhome/scheduler/status {"status": "alive", "timestamp": "2025-12-15 18:45:30", "active_jobs": 3, "total_persistent_jobs": 5, "ping_received": "ping"}
```

## Method 3: Using Python Script

Create a file `ping_scheduler.py`:

```python
#!/usr/bin/env python3
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
            
            if status.get('status') == 'alive':
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
```

### Run the Script

```bash
python ping_scheduler.py
```

### Expected Output (Scheduler Online)

```
✓ Connected to broker.hivemq.com:1883
✓ Subscribed to myhome/scheduler/status
✓ Sent ping to myhome/scheduler/ping

Waiting for response...

==================================================
📡 SCHEDULER STATUS RECEIVED
==================================================
Status:        alive
Timestamp:     2025-12-15 18:45:30
Active Jobs:   3
Persistent:    5
Ping Echo:     ping
==================================================

✅ Scheduler is ALIVE and CONNECTED!
```

### Expected Output (Scheduler Offline)

```
✓ Connected to broker.hivemq.com:1883
✓ Subscribed to myhome/scheduler/status
✓ Sent ping to myhome/scheduler/ping

Waiting for response...

⏱️  Timeout: No response received within 5 seconds
   Scheduler is likely OFFLINE or not connected
```

## Method 4: Continuous Monitoring Script

Create `monitor_scheduler.py` for continuous health checks:

```python
#!/usr/bin/env python3
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

def on_message(client, userdata, msg):
    if msg.topic == STATUS_TOPIC:
        try:
            status = json.loads(msg.payload.decode('utf-8'))
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if status.get('status') == 'alive':
                print(f"[{timestamp}] ✅ Scheduler ALIVE - Jobs: {status.get('active_jobs', 0)}")
            elif status.get('status') == 'online':
                print(f"[{timestamp}] 🟢 Scheduler ONLINE - Jobs: {status.get('active_jobs', 0)}")
            else:
                print(f"[{timestamp}] ⚠️  Scheduler status: {status.get('status', 'unknown')}")
                
        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Invalid response")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)
client.loop_start()

print(f"Monitoring scheduler health every {PING_INTERVAL} seconds...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Send ping
        client.publish(PING_TOPIC, "health-check")
        time.sleep(PING_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\nStopping monitor...")
    client.loop_stop()
    client.disconnect()
```

Run it:

```bash
python monitor_scheduler.py
```

## Method 5: Web Dashboard (Advanced)

Create a simple web-based health monitor `health_dashboard.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>MQTT Scheduler Health Monitor</title>
    <script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .status-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .status-indicator {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
        }
        .online { background: #4CAF50; }
        .offline { background: #f44336; }
        .waiting { background: #FFC107; }
        button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #1976D2; }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="status-card">
        <h2>MQTT Scheduler Health Monitor</h2>
        <div style="margin: 20px 0;">
            <span class="status-indicator waiting" id="indicator"></span>
            <span id="status-text">Connecting...</span>
        </div>
        <button onclick="sendPing()">🔄 Ping Scheduler</button>
    </div>

    <div class="status-card" id="details" style="display: none;">
        <h3>Scheduler Details</h3>
        <div class="info-row">
            <span>Status:</span>
            <strong id="detail-status">-</strong>
        </div>
        <div class="info-row">
            <span>Last Update:</span>
            <strong id="detail-time">-</strong>
        </div>
        <div class="info-row">
            <span>Active Jobs:</span>
            <strong id="detail-jobs">-</strong>
        </div>
        <div class="info-row">
            <span>Persistent Jobs:</span>
            <strong id="detail-persistent">-</strong>
        </div>
    </div>

    <script>
        const BROKER = 'wss://broker.hivemq.com:8884/mqtt';
        const PING_TOPIC = 'myhome/scheduler/ping';
        const STATUS_TOPIC = 'myhome/scheduler/status';

        const client = mqtt.connect(BROKER);

        client.on('connect', () => {
            console.log('Connected to broker');
            document.getElementById('status-text').textContent = 'Connected to broker';
            client.subscribe(STATUS_TOPIC);
            sendPing();
        });

        client.on('message', (topic, message) => {
            if (topic === STATUS_TOPIC) {
                const status = JSON.parse(message.toString());
                updateStatus(status);
            }
        });

        function sendPing() {
            client.publish(PING_TOPIC, 'web-dashboard-ping');
            document.getElementById('status-text').textContent = 'Waiting for response...';
            document.getElementById('indicator').className = 'status-indicator waiting';
        }

        function updateStatus(status) {
            document.getElementById('indicator').className = 'status-indicator online';
            document.getElementById('status-text').textContent = 'Scheduler is Online';
            document.getElementById('details').style.display = 'block';
            
            document.getElementById('detail-status').textContent = status.status;
            document.getElementById('detail-time').textContent = status.timestamp;
            document.getElementById('detail-jobs').textContent = status.active_jobs || 0;
            document.getElementById('detail-persistent').textContent = status.total_persistent_jobs || 0;
        }

        // Auto-ping every 30 seconds
        setInterval(sendPing, 30000);
    </script>
</body>
</html>
```

Open in browser to see real-time status!

## Initial Status on Connection

When the scheduler connects to the broker, it automatically publishes an initial status message:

```json
{
  "status": "online",
  "timestamp": "2025-12-15 18:30:45",
  "active_jobs": 0
}
```

This message is published with the **retain flag**, so new subscribers will immediately see the last known status.

## Troubleshooting

### No Response Received

**Possible Causes:**

1. Scheduler is not running
2. Scheduler is not connected to broker
3. Wrong broker address
4. Network issues

**Solutions:**

```bash
# Check if scheduler process is running
ps aux | grep mqtt_scheduler.py

# Check scheduler console for connection messages
# Should see: "Connected to MQTT Broker!"
# Should see: "Subscribed to ping topic: myhome/scheduler/ping"
```

### Response Timeout

If using the Python ping script and getting timeout:

- Increase timeout from 5 to 10 seconds
- Check network connectivity
- Verify broker address matches scheduler configuration

### Wrong Status Information

If job counts seem incorrect:

- Restart the scheduler to reload persistent jobs
- Check `schedules.json` file for saved jobs

## Integration Examples

### Shell Script Health Check

```bash
#!/bin/bash
# health_check.sh

TIMEOUT=5
RESPONSE=$(timeout $TIMEOUT mosquitto_sub -h broker.hivemq.com \
    -t "myhome/scheduler/status" -C 1 & \
    sleep 0.5; \
    mosquitto_pub -h broker.hivemq.com \
    -t "myhome/scheduler/ping" -m "ping")

if [ -n "$RESPONSE" ]; then
    echo "✅ Scheduler is alive"
    echo "$RESPONSE" | jq .
    exit 0
else
    echo "❌ Scheduler is offline"
    exit 1
fi
```

### Cron Job Monitoring

Add to crontab to check every 5 minutes:

```cron
*/5 * * * * /path/to/ping_scheduler.py >> /var/log/scheduler_health.log 2>&1
```

## Summary

**Quick Test:**

```bash
# Terminal 1: Listen for response
mosquitto_sub -h broker.hivemq.com -t "myhome/scheduler/status" -v

# Terminal 2: Send ping
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/ping" -m "ping"
```

**Expected Result:**

- Immediate JSON response on status topic
- Response includes "status": "alive"
- Shows current job counts

This ping/pong mechanism provides a reliable way to verify the scheduler is running and get real-time status information! 🎯
