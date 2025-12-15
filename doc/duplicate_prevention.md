# Duplicate Job Prevention

The MQTT scheduler now includes automatic duplicate detection to prevent the same job from being scheduled multiple times.

## How It Works

When you submit a new job, the scheduler checks if an **identical job** already exists before adding it. A job is considered a duplicate if ALL of the following match:

- **Type**: `daily`, `interval`, or `once`
- **Topic**: The MQTT topic to publish to
- **Payload**: The message payload
- **Time**: The scheduled time (HH:MM for daily/once, seconds for interval)

## Duplicate Detection Example

### Scenario 1: Preventing Duplicates

**First submission:**

```json
{
  "type": "daily",
  "topic": "esp8266/command",
  "payload": "OFF",
  "time": "22:00"
}
```

✅ **Result**: Job added successfully

**Second submission (identical):**

```json
{
  "type": "daily",
  "topic": "esp8266/command",
  "payload": "OFF",
  "time": "22:00"
}
```

⚠️ **Result**: Duplicate detected, job NOT added

**Console output:**

```
------------------------------
[19:10:30] Received New Job Request.
⚠️  DUPLICATE JOB DETECTED - Job already exists in schedule!
   Type: daily, Topic: esp8266/command, Payload: OFF, Time: 22:00
   Skipping duplicate job.
------------------------------
```

### Scenario 2: Similar But Not Duplicate

These jobs are **NOT** considered duplicates because they differ in at least one field:

**Job 1:**

```json
{
  "type": "daily",
  "topic": "esp8266/command",
  "payload": "OFF",
  "time": "22:00"
}
```

**Job 2 (different time):**

```json
{
  "type": "daily",
  "topic": "esp8266/command",
  "payload": "OFF",
  "time": "23:00"
}
```

✅ Both jobs will be added (different times)

**Job 3 (different payload):**

```json
{
  "type": "daily",
  "topic": "esp8266/command",
  "payload": "ON",
  "time": "22:00"
}
```

✅ Both jobs will be added (different payloads)

## Checking Current Jobs

Before submitting a new job, you can check what's already scheduled:

### Method 1: Using Python Script

```bash
python list_jobs.py
```

**Output:**

```
============================================================
📋 SCHEDULED JOBS
============================================================
Timestamp:   2025-12-15 19:10:45
Total Jobs:  2
============================================================

Job #1:
  Type:    daily
  Topic:   esp8266/command
  Payload: OFF
  Time:    22:00

Job #2:
  Type:    interval
  Topic:   sensor/status
  Payload: CHECK
  Time:    300

============================================================
```

### Method 2: Using MQTT Client

**Send request:**

```bash
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/list_jobs" -m "list"
```

**Listen for response:**

```bash
mosquitto_sub -h broker.hivemq.com -t "myhome/scheduler/status" -v
```

**Response:**

```json
{
  "timestamp": "2025-12-15 19:10:45",
  "total_jobs": 2,
  "jobs": [
    {
      "type": "daily",
      "topic": "esp8266/command",
      "payload": "OFF",
      "time": "22:00"
    },
    {
      "type": "interval",
      "topic": "sensor/status",
      "payload": "CHECK",
      "time": 300
    }
  ]
}
```

### Method 3: Check schedules.json File

```bash
cat schedules.json
```

or

```bash
cat schedules.json | python -m json.tool
```

## Benefits of Duplicate Prevention

1. **Prevents Accidental Resubmission**: If you accidentally submit the same job twice, only one will be scheduled
2. **Saves Resources**: Avoids multiple identical scheduled tasks running
3. **Cleaner Schedule**: Keeps `schedules.json` clean without duplicates
4. **Predictable Behavior**: You know exactly what jobs are running

## Edge Cases

### One-Time Jobs

One-time jobs are automatically removed after execution, so you can resubmit them:

```json
{
  "type": "once",
  "topic": "notification/alert",
  "payload": "REMINDER",
  "time": "15:30"
}
```

- **Before 15:30**: Duplicate detection applies
- **After 15:30**: Job is removed, can be resubmitted for future times

### Restart Behavior

When the scheduler restarts:

1. It loads jobs from `schedules.json`
2. Duplicate detection is active immediately
3. Trying to resubmit a persisted job will be rejected as duplicate

## Manual Duplicate Removal

If you need to remove duplicates from `schedules.json` manually:

### Option 1: Edit schedules.json

```bash
nano schedules.json
```

Remove duplicate entries and save.

### Option 2: Clear All Jobs

```bash
echo "[]" > schedules.json
```

Then restart the scheduler.

### Option 3: Python Script

Create `remove_duplicates.py`:

```python
import json

# Load schedules
with open('schedules.json', 'r') as f:
    jobs = json.load(f)

# Remove duplicates while preserving order
seen = set()
unique_jobs = []

for job in jobs:
    # Create a unique key for each job
    key = (
        job.get('type'),
        job.get('topic'),
        job.get('payload'),
        str(job.get('time'))
    )
    
    if key not in seen:
        seen.add(key)
        unique_jobs.append(job)
    else:
        print(f"Removing duplicate: {job}")

# Save cleaned schedules
with open('schedules.json', 'w') as f:
    json.dump(unique_jobs, f, indent=4)

print(f"\nCleaned: {len(jobs)} → {len(unique_jobs)} jobs")
```

Run it:

```bash
python remove_duplicates.py
```

## Testing Duplicate Detection

### Test Script

Create `test_duplicate.py`:

```python
import paho.mqtt.client as mqtt
import json
import time

BROKER = "broker.hivemq.com"
CONTROL_TOPIC = "myhome/scheduler/submit_job"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)
client.loop_start()

# Submit the same job twice
test_job = {
    "type": "interval",
    "topic": "test/duplicate",
    "payload": "test",
    "time": 60
}

print("Submitting job first time...")
client.publish(CONTROL_TOPIC, json.dumps(test_job))
time.sleep(2)

print("Submitting same job again (should be rejected)...")
client.publish(CONTROL_TOPIC, json.dumps(test_job))
time.sleep(2)

client.loop_stop()
client.disconnect()

print("\nCheck scheduler console for duplicate detection message!")
```

Run it:

```bash
python test_duplicate.py
```

**Expected scheduler output:**

```
------------------------------
[19:15:00] Received New Job Request.
  -> SCHEDULED INTERVAL (60 seconds): publish 'test' to test/duplicate
[PERSISTENCE] Scheduler state saved to schedules.json.
------------------------------
------------------------------
[19:15:02] Received New Job Request.
⚠️  DUPLICATE JOB DETECTED - Job already exists in schedule!
   Type: interval, Topic: test/duplicate, Payload: test, Time: 60
   Skipping duplicate job.
------------------------------
```

## Topics Summary

| Topic | Purpose | Example Message |
|-------|---------|-----------------|
| `myhome/scheduler/submit_job` | Submit new jobs | Job JSON object |
| `myhome/scheduler/list_jobs` | Request list of all jobs | Any text (e.g., "list") |
| `myhome/scheduler/status` | Receive responses | Job list or status |
| `myhome/scheduler/ping` | Health check | "ping" |

## Troubleshooting

### Job Not Being Added

**Problem**: You submit a job but it's not added.

**Possible Cause**: It's a duplicate of an existing job.

**Solution**:

1. Check current jobs: `python list_jobs.py`
2. Verify your job is not already scheduled
3. If needed, modify the job slightly (different time, topic, or payload)

### Want to Update Existing Job

**Problem**: You want to change a scheduled job.

**Current Limitation**: The scheduler doesn't support job updates yet.

**Workaround**:

1. Stop the scheduler
2. Edit `schedules.json` manually
3. Restart the scheduler

**Future Enhancement**: Add a delete/update job feature via MQTT topics.

## Summary

✅ **Automatic duplicate detection** prevents the same job from being added twice

✅ **List jobs command** lets you see what's currently scheduled

✅ **Clean persistence** ensures `schedules.json` stays organized

✅ **Predictable behavior** makes the scheduler more reliable

For more information, see:

- [README.md](../README.md) - Main documentation
- [ping_pong_health_check.md](ping_pong_health_check.md) - Health monitoring
- [check_connection.md](check_connection.md) - Connection verification
