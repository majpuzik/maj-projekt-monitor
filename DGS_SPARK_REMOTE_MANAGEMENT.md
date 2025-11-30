# DGS Spark Remote Management Guide

## Installation Date
2025-11-17

## Installed Components

### 1. Hardware Watchdog Timer
**Service:** `watchdog.service`  
**Status:** ✅ Active and enabled  
**Configuration:** `/etc/watchdog.conf`

**Features:**
- Monitors system load (max 1-min average: 24)
- Monitors memory (min free: 1GB)
- Monitors temperature (max: 85°C)
- Auto-reboots system on freeze/hang
- Watchdog timeout: 60 seconds

**Check Status:**
```bash
systemctl status watchdog.service
```

### 2. Memory Pressure Guard
**Service:** `memory-pressure-guard.service`  
**Status:** ✅ Active and enabled  
**Script:** `/usr/local/bin/memory_pressure_guard.sh`

**Features:**
- Monitors RAM usage every 30 seconds
- Kills largest non-root process when RAM > 90%
- Logs actions to syslog (check with: `journalctl -t memory_pressure`)

**Check Status:**
```bash
systemctl status memory-pressure-guard.service
```

**View Logs:**
```bash
journalctl -u memory-pressure-guard.service -n 50
```

### 3. Trigger File Reboot Monitor
**Service:** `trigger-reboot-monitor.service`  
**Status:** ✅ Active and enabled  
**Script:** `/usr/local/bin/trigger_reboot_monitor.sh`

**Features:**
- Checks for `/tmp/REBOOT_NOW` file every 10 seconds
- Triggers safe system reboot when file exists
- File is automatically removed before reboot

**Remote Reboot from Anywhere:**
```bash
# From Mac/local machine:
sshpass -p "Dasa_beda2208n" ssh puzik@192.168.10.200 "touch /tmp/REBOOT_NOW"

# Or with regular SSH:
ssh puzik@192.168.10.200
touch /tmp/REBOOT_NOW
exit
# System will reboot within 10 seconds
```

**Check Status:**
```bash
systemctl status trigger-reboot-monitor.service
```

### 4. SSH Keepalive Configuration
**Status:** ✅ Configured and active  
**Configuration:** `/etc/ssh/sshd_config`

**Settings:**
- ClientAliveInterval: 60 seconds
- ClientAliveCountMax: 3 attempts
- TCPKeepAlive: yes

**Effect:**
- SSH connections stay alive during high system load
- Server sends keepalive every 60 seconds
- Connection drops after 3 missed keepalives (3 minutes)

## Usage Examples

### Trigger Remote Reboot
```bash
# Quick one-liner from Mac:
sshpass -p "Dasa_beda2208n" ssh -o StrictHostKeyChecking=no puzik@192.168.10.200 "touch /tmp/REBOOT_NOW && echo Reboot triggered!"
```

### Check System Health
```bash
ssh puzik@192.168.10.200
free -h              # Check memory usage
uptime               # Check load average
systemctl status watchdog memory-pressure-guard trigger-reboot-monitor
```

### Monitor Memory Pressure Events
```bash
ssh puzik@192.168.10.200
journalctl -t memory_pressure -f     # Follow live
journalctl -t memory_pressure -n 100 # Last 100 events
```

### Check Watchdog Logs
```bash
ssh puzik@192.168.10.200
journalctl -u watchdog.service -n 50
```

## Troubleshooting

### Service Not Running
```bash
# Check status
sudo systemctl status <service-name>

# Restart service
sudo systemctl restart <service-name>

# View recent logs
sudo journalctl -u <service-name> -n 50
```

### Disable Services (if needed)
```bash
sudo systemctl stop watchdog.service
sudo systemctl disable watchdog.service

sudo systemctl stop memory-pressure-guard.service
sudo systemctl disable memory-pressure-guard.service

sudo systemctl stop trigger-reboot-monitor.service
sudo systemctl disable trigger-reboot-monitor.service
```

### Re-enable Services
```bash
sudo systemctl enable watchdog.service
sudo systemctl start watchdog.service

sudo systemctl enable memory-pressure-guard.service
sudo systemctl start memory-pressure-guard.service

sudo systemctl enable trigger-reboot-monitor.service
sudo systemctl start trigger-reboot-monitor.service
```

## Files and Locations

**Configuration Files:**
- `/etc/watchdog.conf` - Hardware watchdog configuration
- `/etc/ssh/sshd_config` - SSH server configuration
- `/etc/systemd/system/memory-pressure-guard.service` - Memory guard service
- `/etc/systemd/system/trigger-reboot-monitor.service` - Trigger reboot service

**Scripts:**
- `/usr/local/bin/memory_pressure_guard.sh` - Memory monitoring script
- `/usr/local/bin/trigger_reboot_monitor.sh` - Reboot trigger monitor

**Backups:**
- `/etc/watchdog.conf.backup` - Original watchdog config
- `/etc/ssh/sshd_config.backup` - Original SSH config

## Recovery from Memory Leak

The ingestion.py memory leak issue that occurred on 2025-11-17 will now be automatically handled:

1. **Prevention:** Use safe ingestion pipeline (`ingestion_safe.py`) with 5GB RAM usage
2. **Detection:** Memory pressure guard monitors RAM every 30 seconds
3. **Automatic Recovery:** Process killed automatically at >90% RAM
4. **System Protection:** Watchdog will reboot system if it freezes
5. **Manual Intervention:** Trigger remote reboot with `/tmp/REBOOT_NOW` file

## IPMI / Remote Management

**Note:** Nvidia Jetson Orin AGX does not have traditional IPMI (Intelligent Platform Management Interface) as it is not a server platform. However, the implemented software-based remote management provides equivalent functionality:

- ✅ Remote reboot capability (trigger file method)
- ✅ Automatic recovery from hangs (watchdog)
- ✅ Memory overload protection
- ✅ Reliable SSH access (keepalive)
- ✅ System monitoring and logging

For hardware-level remote power control, consider:
- Smart PDU (Power Distribution Unit) with network control
- Tailscale or other VPN for remote access from anywhere
- KVM over IP device for console access

## Questions?

Contact: M.A.J. Puzik  
Documentation created: 2025-11-17  
Last updated: 2025-11-17
