# MQTT Scheduler - Quick Reference

## Health Check Commands

### Check if Scheduler is Alive

**Method 1: Using mosquitto (Command Line)**

Terminal 1 - Listen for response:

```bash
mosquitto_sub -h broker.hivemq.com -t "myhome/scheduler/status" -v
```

Terminal 2 - Send ping:

```bash
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/ping" -m "ping"
```

**Method 2: Using Python Script**

```bash
python ping_scheduler.py
```

**Method 3: Continuous Monitoring**

```bash
python monitor_scheduler.py
```

## Topics

| Topic | Purpose |
|-------|---------|
| `myhome/scheduler/submit_job` | Submit new scheduled jobs |
| `myhome/scheduler/ping` | Send health check ping |
| `myhome/scheduler/status` | Receive scheduler status |
| `myhome/scheduler/list_jobs` | Request list of all jobs |

## List All Scheduled Jobs

```bash
python list_jobs.py
```

or using MQTT:

```bash
# Request list
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/list_jobs" -m "list"

# Listen for response
mosquitto_sub -h broker.hivemq.com -t "myhome/scheduler/status" -v
```

## Duplicate Prevention

The scheduler automatically prevents duplicate jobs. If you submit the same job twice, the second submission will be rejected.

## Expected Response

When you ping the scheduler, you'll receive:

```json
{
  "status": "alive",
  "timestamp": "2025-12-15 18:45:30",
  "active_jobs": 3,
  "total_persistent_jobs": 5,
  "ping_received": "ping"
}
```

## Status Indicators

- ✅ **"alive"** - Scheduler is running and responding to pings
- 🟢 **"online"** - Scheduler just connected to broker
- ❌ **No response** - Scheduler is offline or not connected

## Files

- `mqtt_scheduler.py` - Main scheduler (enhanced with ping/pong)
- `ping_scheduler.py` - One-time health check script
- `monitor_scheduler.py` - Continuous monitoring script
- `doc/ping_pong_health_check.md` - Detailed documentation

## Quick Test

1. Start the scheduler:

   ```bash
   python mqtt_scheduler.py
   ```

2. In another terminal, test the connection:

   ```bash
   python ping_scheduler.py
   ```

3. You should see:

   ```
   ✅ Scheduler is ALIVE and CONNECTED!
   ```
