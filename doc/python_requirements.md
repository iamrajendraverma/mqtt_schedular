# Python Libraries Required for MQTT Scheduler

This document lists all the Python libraries required to run the MQTT Scheduler project, along with their purposes and installation instructions.

## Required Libraries

### 1. **paho-mqtt**

- **Purpose**: MQTT client library for Python
- **Used for**: Connecting to MQTT brokers, publishing messages, and subscribing to topics
- **Version**: Latest stable (recommended: >= 1.6.1)
- **Documentation**: <https://pypi.org/project/paho-mqtt/>

**Usage in project:**

- Connecting to MQTT broker (HiveMQ or custom broker)
- Publishing scheduled messages to specified topics
- Subscribing to control topic for receiving job commands

### 2. **schedule**

- **Purpose**: Job scheduling library for Python
- **Used for**: Creating and managing scheduled tasks
- **Version**: Latest stable (recommended: >= 1.1.0)
- **Documentation**: <https://pypi.org/project/schedule/>

**Usage in project:**

- Scheduling daily jobs at specific times
- Scheduling interval-based jobs (every N seconds)
- Scheduling one-time jobs
- Managing and canceling scheduled tasks

### 3. **Standard Library Modules**

The following modules are part of Python's standard library and don't require installation:

- **json**: For parsing and creating JSON data
- **time**: For time-related operations and sleep functionality
- **datetime**: For working with dates and timestamps
- **os**: For file system operations (checking file existence)

## Installation

### Method 1: Using pip (Individual Installation)

Install each library separately:

```bash
pip install paho-mqtt
pip install schedule
```

### Method 2: Using requirements.txt (Recommended)

Create a `requirements.txt` file in the project root with the following content:

```txt
paho-mqtt>=1.6.1
schedule>=1.1.0
```

Then install all dependencies at once:

```bash
pip install -r requirements.txt
```

### Method 3: For Termux (Android)

If you're running this on Android using Termux:

```bash
pkg install python
pip install paho-mqtt schedule
```

## Installation on Different Platforms

### Linux/macOS

```bash
# Using system Python
pip3 install paho-mqtt schedule

# Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt schedule
```

### Windows

```cmd
# Using pip
pip install paho-mqtt schedule

# Using virtual environment (recommended)
python -m venv venv
venv\Scripts\activate
pip install paho-mqtt schedule
```

### Termux (Android)

```bash
# Update packages first
pkg update && pkg upgrade

# Install Python if not already installed
pkg install python

# Install required libraries
pip install paho-mqtt schedule
```

## Verifying Installation

To verify that all libraries are installed correctly, run:

```bash
python -c "import paho.mqtt.client as mqtt; import schedule; print('All libraries installed successfully!')"
```

Or create a test script `test_imports.py`:

```python
#!/usr/bin/env python3

try:
    import paho.mqtt.client as mqtt
    print("✓ paho-mqtt installed")
except ImportError:
    print("✗ paho-mqtt NOT installed")

try:
    import schedule
    print("✓ schedule installed")
except ImportError:
    print("✗ schedule NOT installed")

try:
    import json
    import time
    import os
    from datetime import datetime
    print("✓ Standard library modules available")
except ImportError:
    print("✗ Standard library modules NOT available")

print("\nAll checks complete!")
```

Run it with:

```bash
python test_imports.py
```

## Library Details

### paho-mqtt

**Key Features:**

- MQTT 3.1 and 3.1.1 protocol support
- Automatic reconnection
- QoS 0, 1, and 2 support
- TLS/SSL support
- Callback-based API

**Common Methods Used:**

- `mqtt.Client()`: Create MQTT client instance
- `client.connect()`: Connect to broker
- `client.publish()`: Publish message to topic
- `client.subscribe()`: Subscribe to topic
- `client.loop_start()`: Start background thread for network loop
- `client.on_connect`: Connection callback
- `client.on_message`: Message received callback

### schedule

**Key Features:**

- Simple, human-friendly syntax
- Job scheduling at specific times
- Interval-based scheduling
- Job tagging and cancellation
- No daemon or service required

**Common Methods Used:**

- `schedule.every().day.at()`: Schedule daily job
- `schedule.every(n).seconds.do()`: Schedule interval job
- `schedule.run_pending()`: Run pending scheduled jobs
- `schedule.cancel_job()`: Cancel a specific job
- `schedule.get_jobs()`: Get list of scheduled jobs

## Dependency Tree

```
mqtt-scheduler/
├── paho-mqtt (external)
│   └── Used for MQTT communication
├── schedule (external)
│   └── Used for job scheduling
└── Standard Library
    ├── json (data serialization)
    ├── time (delays and timing)
    ├── datetime (timestamps)
    └── os (file operations)
```

## Version Compatibility

### Python Version

- **Minimum**: Python 3.7
- **Recommended**: Python 3.8 or higher
- **Tested on**: Python 3.9+

### Library Versions

| Library | Minimum Version | Recommended Version |
|---------|----------------|---------------------|
| paho-mqtt | 1.5.0 | 1.6.1 or later |
| schedule | 1.0.0 | 1.1.0 or later |

## Troubleshooting

### Issue: "No module named 'paho'"

**Solution:**

```bash
pip install paho-mqtt
```

### Issue: "No module named 'schedule'"

**Solution:**

```bash
pip install schedule
```

### Issue: Permission denied when installing

**Solution (Linux/macOS):**

```bash
pip install --user paho-mqtt schedule
```

Or use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt schedule
```

### Issue: pip not found

**Solution:**

```bash
# On Debian/Ubuntu
sudo apt install python3-pip

# On macOS
python3 -m ensurepip

# On Termux
pkg install python
```

### Issue: Old version of pip

**Solution:**

```bash
pip install --upgrade pip
```

## Creating requirements.txt

To generate a `requirements.txt` file from your current environment:

```bash
pip freeze > requirements.txt
```

To create a minimal requirements file (recommended):

Create a file named `requirements.txt` with:

```txt
# MQTT Client Library
paho-mqtt>=1.6.1

# Job Scheduling Library
schedule>=1.1.0
```

## Virtual Environment Setup (Best Practice)

Using a virtual environment is recommended to avoid conflicts with system packages:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

## Additional Resources

- **paho-mqtt GitHub**: <https://github.com/eclipse/paho.mqtt.python>
- **schedule GitHub**: <https://github.com/dbader/schedule>
- **Python Package Index (PyPI)**: <https://pypi.org/>
- **pip Documentation**: <https://pip.pypa.io/>

## Summary

For a quick setup, run these commands:

```bash
# Install required libraries
pip install paho-mqtt schedule

# Verify installation
python -c "import paho.mqtt.client; import schedule; print('Ready to go!')"

# Run the scheduler
python mqtt_scheduler.py
```
