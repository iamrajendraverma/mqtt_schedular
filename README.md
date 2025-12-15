# MQTT Scheduler

A Python-based MQTT scheduler that allows you to schedule and automate MQTT message publishing. This tool enables you to create daily, interval-based, and one-time scheduled jobs that publish messages to MQTT topics at specified times.

## Features

- **Multiple Schedule Types**
  - **Daily**: Publish messages at a specific time every day
  - **Interval**: Publish messages at regular intervals (in seconds)
  - **Once**: Publish a message once at a specific time (auto-cancels after execution)

- **Persistent Scheduling**: All scheduled jobs are saved to a JSON file and automatically restored on restart

- **Dynamic Job Management**: Add new jobs via MQTT messages without restarting the scheduler

- **Real-time Logging**: Detailed logging of all operations with timestamps

- **Automatic Reconnection**: Handles MQTT broker disconnections gracefully

## Architecture

The project consists of three main components:

1. **`mqtt_scheduler.py`**: Main scheduler application that handles MQTT communication and job scheduling
2. **`persistence.py`**: Manages loading and saving of schedules to/from JSON file
3. **`schedules.json`**: Persistent storage for scheduled jobs

## Requirements

- Python 3.7+
- `paho-mqtt` - MQTT client library
- `schedule` - Job scheduling library

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install paho-mqtt schedule
```

## Configuration

Edit the configuration section in `mqtt_scheduler.py`:

```python
BROKER_ADDRESS = "broker.hivemq.com"  # Your MQTT broker address
PORT = 1883                            # MQTT broker port
KEEPALIVE = 60                         # Connection keepalive interval
USERNAME = None                        # MQTT username (if required)
PASSWORD = None                        # MQTT password (if required)

CONTROL_TOPIC = "myhome/scheduler/submit_job"  # Topic to submit new jobs
```

## Usage

### Starting the Scheduler

Run the scheduler:
```bash
python mqtt_scheduler.py
```

The scheduler will:
1. Load any previously saved jobs from `schedules.json`
2. Connect to the MQTT broker
3. Subscribe to the control topic
4. Start executing scheduled jobs

### Creating Scheduled Jobs

Send a JSON message to the control topic (`myhome/scheduler/submit_job`) with the following structure:

#### Daily Job Example
Publish a message every day at a specific time:
```json
{
    "type": "daily",
    "topic": "esp8266/command",
    "payload": "ON",
    "time": "08:00"
}
```

#### Interval Job Example
Publish a message every N seconds:
```json
{
    "type": "interval",
    "topic": "sensor/status",
    "payload": "CHECK",
    "time": 300
}
```
*Note: For interval jobs, `time` is in seconds*

#### One-Time Job Example
Publish a message once at a specific time (auto-cancels after execution):
```json
{
    "type": "once",
    "topic": "notification/alert",
    "payload": "REMINDER",
    "time": "15:30"
}
```

### Job Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Schedule type: `"daily"`, `"interval"`, or `"once"` |
| `topic` | string | MQTT topic to publish to |
| `payload` | string | Message payload to publish |
| `time` | string/int | Time in `"HH:MM"` format for daily/once jobs, or seconds for interval jobs |

## Example Use Cases

### Home Automation
```json
{
    "type": "daily",
    "topic": "esp8266/command",
    "payload": "OFF",
    "time": "22:00"
}
```
Turn off lights every night at 10 PM

### Periodic Status Checks
```json
{
    "type": "interval",
    "topic": "devices/ping",
    "payload": "PING",
    "time": 60
}
```
Send a ping message every 60 seconds

### Reminder Notifications
```json
{
    "type": "once",
    "topic": "notification/reminder",
    "payload": "Take medication",
    "time": "14:00"
}
```
Send a one-time reminder at 2 PM

## Persistence

All scheduled jobs are automatically saved to `schedules.json`. When the scheduler restarts:
- It loads all previously saved jobs
- Recreates the schedules
- Continues executing them as configured

**Note**: One-time jobs that have already executed are automatically removed from the persistence file.

## Logging

The scheduler provides detailed logging:
- Connection status
- Job creation and scheduling
- Message publishing (success/failure)
- Job cancellation (for one-time jobs)
- Persistence operations

Example log output:
```
[2025-12-14 14:50:00] PUBLISHED: 'OFF' to Topic: esp8266/command
[PERSISTENCE] Scheduler state saved to schedules.json.
```

## Testing with MQTT Client

You can test the scheduler using any MQTT client (e.g., MQTT Explorer, mosquitto_pub):

```bash
# Using mosquitto_pub
mosquitto_pub -h broker.hivemq.com -t "myhome/scheduler/submit_job" -m '{"type":"daily","topic":"test/topic","payload":"Hello","time":"10:00"}'
```

## Troubleshooting

### Scheduler not connecting to broker
- Verify the `BROKER_ADDRESS` and `PORT` are correct
- Check if authentication is required (set `USERNAME` and `PASSWORD`)
- Ensure network connectivity to the broker

### Jobs not executing
- Check system time is correct
- Verify the time format is `"HH:MM"` for daily/once jobs
- Check the scheduler logs for errors

### Jobs not persisting
- Ensure write permissions for `schedules.json`
- Check for JSON formatting errors in the file

## Project Structure

```
mqtt-scheduler/
├── mqtt_scheduler.py    # Main scheduler application
├── persistence.py       # Persistence management module
├── schedules.json       # Persistent job storage
└── README.md           # This file
```

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Author

Created for home automation and IoT scheduling needs.
