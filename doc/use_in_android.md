# Using Termux from Your Laptop

This guide explains how to access and control Termux on your Android device from your laptop using SSH.

## Prerequisites

- Termux installed on your Android device
- Both your Android device and laptop connected to the same network (Wi-Fi)
- SSH client on your laptop (built-in on macOS/Linux, or use PuTTY on Windows)

## Setup on Android (Termux)

### 1. Install OpenSSH Server

Open Termux on your Android device and run:

```bash
pkg update
pkg upgrade
pkg install openssh
```

### 2. Set a Password

Set a password for your Termux user:

```bash
passwd
```

Enter and confirm your new password when prompted.

### 3. Start SSH Server

Start the SSH server in Termux:

```bash
sshd
```

The SSH server will start on port **8022** by default (not the standard port 22).

### 4. Find Your Android Device's IP Address

Get your device's local IP address:

```bash
ifconfig
```

or

```bash
ip addr show
```

Look for the IP address under `wlan0` (usually starts with `192.168.x.x` or `10.0.x.x`).

Alternatively, you can use:

```bash
ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

## Connect from Your Laptop

### On macOS/Linux

Open Terminal and connect using:

```bash
ssh -p 8022 <username>@<android-ip-address>
```

For example:

```bash
ssh -p 8022 u0_a123@192.168.1.100
```

**Note:** Your Termux username is typically shown in the Termux prompt (e.g., `u0_a123`). You can find it by running `whoami` in Termux.

### On Windows

#### Using PowerShell/Command Prompt

```cmd
ssh -p 8022 <username>@<android-ip-address>
```

#### Using PuTTY

1. Open PuTTY
2. Enter the Android device's IP address in "Host Name"
3. Change "Port" to **8022**
4. Select "SSH" as connection type
5. Click "Open"
6. Enter your Termux username and password when prompted

## SSH Key Authentication (Recommended)

For easier and more secure access without entering a password each time:

### 1. Generate SSH Key on Your Laptop (if you don't have one)

On macOS/Linux:

```bash
ssh-keygen -t rsa -b 4096
```

Press Enter to accept the default location and optionally set a passphrase.

### 2. Copy Public Key to Termux

On your laptop:

```bash
ssh-copy-id -p 8022 <username>@<android-ip-address>
```

Or manually:

```bash
cat ~/.ssh/id_rsa.pub | ssh -p 8022 <username>@<android-ip-address> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Set Correct Permissions on Termux

On your Android device (in Termux):

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Now you can connect without entering a password:

```bash
ssh -p 8022 <username>@<android-ip-address>
```

## Managing the SSH Server

### Start SSH Server

```bash
sshd
```

### Stop SSH Server

```bash
pkill sshd
```

### Check if SSH Server is Running

```bash
pgrep sshd
```

If it returns a process ID, the server is running.

### Auto-start SSH on Termux Launch

Create a startup script:

```bash
mkdir -p ~/.termux
echo "sshd" >> ~/.termux/boot/start-sshd.sh
chmod +x ~/.termux/boot/start-sshd.sh
```

Install Termux:Boot from F-Droid or Google Play Store and open it once to enable boot scripts.

## Useful Tips

### Create an SSH Alias

On your laptop, edit `~/.ssh/config`:

```bash
nano ~/.ssh/config
```

Add the following:

```
Host termux
    HostName 192.168.1.100
    Port 8022
    User u0_a123
```

Now you can connect simply with:

```bash
ssh termux
```

### Transfer Files

#### From Laptop to Android

```bash
scp -P 8022 /path/to/local/file <username>@<android-ip>:/path/to/destination/
```

#### From Android to Laptop

```bash
scp -P 8022 <username>@<android-ip>:/path/to/remote/file /path/to/local/destination/
```

#### Using rsync

```bash
rsync -avz -e "ssh -p 8022" /local/path/ <username>@<android-ip>:/remote/path/
```

### Port Forwarding

Forward a port from Termux to your laptop:

```bash
ssh -p 8022 -L 8080:localhost:8080 <username>@<android-ip>
```

This forwards port 8080 from your Android device to port 8080 on your laptop.

## Troubleshooting

### Connection Refused

- Ensure SSH server is running: `pgrep sshd`
- Check if both devices are on the same network
- Verify the IP address is correct
- Check firewall settings on your laptop

### Permission Denied

- Verify you're using the correct username (run `whoami` in Termux)
- Ensure you entered the correct password
- Check `~/.ssh/authorized_keys` permissions (should be 600)

### SSH Server Stops After Closing Termux

By default, Android may kill background processes. To prevent this:

1. Disable battery optimization for Termux in Android settings
2. Use Termux:Boot to auto-start SSH
3. Use a wakelock: `termux-wake-lock` (requires Termux:API)

### Can't Find IP Address

If your device doesn't have a Wi-Fi connection:

- Connect both devices to the same Wi-Fi network
- Alternatively, use USB tethering or create a hotspot

## Security Considerations

1. **Use strong passwords** or preferably SSH key authentication
2. **Don't expose SSH to the internet** - only use on trusted local networks
3. **Keep Termux and packages updated**: `pkg update && pkg upgrade`
4. **Disable password authentication** after setting up SSH keys (edit `$PREFIX/etc/ssh/sshd_config`)
5. **Use a firewall** if available on your Android device

## Additional Resources

- [Termux Wiki - Remote Access](https://wiki.termux.com/wiki/Remote_Access)
- [OpenSSH Documentation](https://www.openssh.com/manual.html)
- [Termux GitHub](https://github.com/termux/termux-app)

## Running MQTT Scheduler from Laptop

Once connected via SSH, you can run the MQTT scheduler on your Android device:

```bash
# Navigate to the project directory
cd /path/to/mqtt-scheduler

# Run the scheduler
python main.py
```

You can also use `screen` or `tmux` to keep the process running after disconnecting:

```bash
# Install screen
pkg install screen

# Start a new screen session
screen -S mqtt

# Run your application
python main.py

# Detach from screen: Press Ctrl+A, then D
# Reattach later: screen -r mqtt
```
