# How to Check if MQTT Scheduler is Connected

This guide explains various methods to verify that your MQTT scheduler is successfully connected to the MQTT broker.

## Method 1: Check Console Output

When you run the scheduler, look for these messages in the console:

### Successful Connection

```
Attempting to connect to broker.hivemq.com:1883...
[18:30:45] Connected to MQTT Broker!
Subscribed to control topic: myhome/scheduler/submit_job

Scheduler Initialized and Running.
System Time: 2025-12-15 18:30:45
Waiting for Commands on: myhome/scheduler/submit_job
```

### Failed Connection

```
Attempting to connect to broker.hivemq.com:1883...
Failed to connect, return code 1
Could not connect to broker: [Error details]
```

## Method 2: Test with MQTT Client

Use an MQTT client tool to verify the connection by sending a test job.

### Using MQTT Explorer (GUI Tool)

1. Download MQTT Explorer: <http://mqtt-explorer.com/>
2. Connect to the same broker (e.g., `broker.hivemq.com:1883`)
3. Publish a test message to `myhome/scheduler/submit_job`:

```json
{
  "type": "once",
  "topic": "test/connection",
  "payload": "Connection test successful!",
  "time": "18:35"
}
```

4. If connected, you should see output in the scheduler console:

```
------------------------------
[18:33:29] Received New Job Request.
  -> SCHEDULED ONCE at 18:35: publish 'Connection test successful!' to test/connection. Will self-cancel.
[PERSISTENCE] Scheduler state saved to schedules.json.
------------------------------
```

### Using mosquitto_pub (Command Line)

```bash
# Install mosquitto client tools first
# On Linux/macOS:
sudo apt install mosquitto-clients  # Debian/Ubuntu
brew install mosquitto              # macOS

# On Termux:
pkg install mosquitto

# Send test message
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/submit_job" -m '{
  "type": "interval",
  "topic": "test/heartbeat",
  "payload": "alive",
  "time": 10
}'
```

### Using Python Script

Create a file `test_connection.py`:

```python
import paho.mqtt.client as mqtt
import json
import time

BROKER = "broker.hivemq.com"
PORT = 1883
CONTROL_TOPIC = "myhome/scheduler/submit_job"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"❌ Failed to connect: {reason_code}")
    else:
        print("✓ Connected to broker successfully!")
        
        # Send test job
        test_job = {
            "type": "interval",
            "topic": "test/ping",
            "payload": "pong",
            "time": 30
        }
        
        client.publish(CONTROL_TOPIC, json.dumps(test_job))
        print(f"✓ Test job sent to {CONTROL_TOPIC}")
        print("Check your scheduler console for confirmation.")
        
        time.sleep(2)
        client.disconnect()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect

print(f"Connecting to {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
```

Run it:

```bash
python test_connection.py
```

## Method 3: Monitor Network Connection

### Check if Process is Running

```bash
# Linux/macOS/Termux
ps aux | grep mqtt_scheduler.py

# Or using pgrep
pgrep -f mqtt_scheduler.py
```

### Check Network Connections

```bash
# Linux/macOS
netstat -an | grep 1883

# Or using lsof
lsof -i :1883

# Termux
netstat -an | grep 1883
```

You should see an ESTABLISHED connection to the broker's IP address on port 1883.

## Method 4: Check Logs in Real-Time

If you're running the scheduler in the background, you can monitor logs:

### Using screen

```bash
# Start scheduler in screen
screen -S mqtt-scheduler
python mqtt_scheduler.py

# Detach: Ctrl+A, then D

# Reattach to check status
screen -r mqtt-scheduler
```

### Using tmux

```bash
# Start scheduler in tmux
tmux new -s mqtt-scheduler
python mqtt_scheduler.py

# Detach: Ctrl+B, then D

# Reattach to check status
tmux attach -t mqtt-scheduler
```

### Redirect to Log File

```bash
# Run with output redirected to log file
python mqtt_scheduler.py > scheduler.log 2>&1 &

# Monitor the log
tail -f scheduler.log

# Check for connection message
grep "Connected to MQTT Broker" scheduler.log
```

## Method 5: Programmatic Connection Check

You can modify the code to add a connection status indicator. Here's an enhanced version:

### Add Connection Status Variable

```python
# Add this global variable at the top
IS_CONNECTED = False

def on_connect(client, userdata, flags, reason_code, properties):
    global IS_CONNECTED
    if reason_code.is_failure: 
        print(f"Failed to connect, return code {reason_code.rc}")
        IS_CONNECTED = False
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to MQTT Broker!")
        IS_CONNECTED = True
        client.subscribe(CONTROL_TOPIC)
        print(f"Subscribed to control topic: {CONTROL_TOPIC}")

def on_disconnect(client, userdata, reason_code, properties):
    global IS_CONNECTED
    IS_CONNECTED = False
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected from broker. Reason: {reason_code}")
```

## Method 6: Health Check Endpoint (Advanced)

For production environments, you can add a simple HTTP health check:

Create `mqtt_scheduler_with_health.py`:

```python
import paho.mqtt.client as mqtt
import schedule
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

# ... (your existing code)

IS_CONNECTED = False

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            status = {
                "status": "healthy" if IS_CONNECTED else "unhealthy",
                "connected": IS_CONNECTED,
                "timestamp": datetime.now().isoformat(),
                "active_jobs": len(schedule.default_scheduler.get_jobs())
            }
            
            self.send_response(200 if IS_CONNECTED else 503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    print("Health check server running on http://0.0.0.0:8080/health")
    server.serve_forever()

# Start health check server in background thread
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# ... (rest of your code)
```

Then check health:

```bash
curl http://localhost:8080/health
```

## Common Connection Issues

### Issue: "Connection Refused"

**Possible Causes:**

- Broker is down or unreachable
- Incorrect broker address or port
- Firewall blocking connection
- No internet connection

**Solution:**

```bash
# Test broker connectivity
ping broker.hivemq.com

# Test port connectivity
telnet broker.hivemq.com 1883
# or
nc -zv broker.hivemq.com 1883
```

### Issue: "Connection Timeout"

**Possible Causes:**

- Network issues
- Broker is slow to respond
- Firewall/proxy blocking

**Solution:**

- Increase keepalive timeout in code
- Check network connectivity
- Try a different broker

### Issue: "Authentication Failed"

**Possible Causes:**

- Incorrect username/password
- Broker requires authentication but none provided

**Solution:**

- Verify credentials in `mqtt_scheduler.py`
- Check if broker requires authentication

## Quick Connection Test Checklist

✅ **Pre-flight Checks:**

1. [ ] Python script runs without errors
2. [ ] Console shows "Connected to MQTT Broker!"
3. [ ] Console shows "Subscribed to control topic: ..."
4. [ ] No error messages in console

✅ **Functional Checks:**

1. [ ] Can send test job via MQTT client
2. [ ] Scheduler receives and processes the job
3. [ ] Job appears in `schedules.json`
4. [ ] Scheduled messages are published at correct times

✅ **Network Checks:**

1. [ ] Can ping broker address
2. [ ] Port 1883 is accessible
3. [ ] Process shows ESTABLISHED connection

## Monitoring Script

Create `monitor_scheduler.sh`:

```bash
#!/bin/bash

echo "=== MQTT Scheduler Connection Monitor ==="
echo ""

# Check if process is running
if pgrep -f mqtt_scheduler.py > /dev/null; then
    echo "✓ Scheduler process is running"
    PID=$(pgrep -f mqtt_scheduler.py)
    echo "  PID: $PID"
else
    echo "✗ Scheduler process is NOT running"
    exit 1
fi

# Check network connection
if netstat -an 2>/dev/null | grep -q ":1883.*ESTABLISHED"; then
    echo "✓ Network connection to broker is ESTABLISHED"
else
    echo "✗ No ESTABLISHED connection on port 1883"
fi

# Check recent logs (if logging to file)
if [ -f "scheduler.log" ]; then
    echo ""
    echo "=== Recent Log Entries ==="
    tail -n 5 scheduler.log
fi

echo ""
echo "=== Active Scheduled Jobs ==="
if [ -f "schedules.json" ]; then
    cat schedules.json | python -m json.tool
else
    echo "No schedules.json file found"
fi
```

Make it executable and run:

```bash
chmod +x monitor_scheduler.sh
./monitor_scheduler.sh
```

## Summary

**Easiest Methods:**

1. **Console Output** - Look for "Connected to MQTT Broker!" message
2. **Send Test Job** - Use MQTT Explorer or mosquitto_pub
3. **Check Process** - Verify the Python process is running

**For Production:**

- Add health check endpoint
- Implement logging to file
- Use process monitoring tools (systemd, supervisor, etc.)
- Set up alerts for disconnections
