# Ramadan video: run at sunrise and sundown

The Ramadan video is meant to run **twice per day** during Ramadan: once around **sunrise** and once around **sundown**. The best approach is the **long-running scheduler** that uses real sunrise/sunset times for your location.

---

## Ubuntu / Linux (recommended)

### Quick setup (one script)

From the project directory:

```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

The script will:
- Install system packages (python3, python3-venv, ffmpeg)
- Create a virtualenv and install Python dependencies
- Optionally ask for Discord webhook and location (or use env vars, see below)
- Install and start the systemd user service

Optional env vars (for non-interactive runs):

```bash
DISCORD_WEBHOOK_URL=https://... RAMADAN_LATITUDE=52.37 RAMADAN_LONGITUDE=4.9 RAMADAN_TIMEZONE=Europe/Amsterdam ./setup_ubuntu.sh
```

---

### Manual setup

#### 1. Install dependencies

On the Ubuntu machine:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg
cd /path/to/RamadanOeroen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(FFmpeg is required for MoviePy to render the video.)

#### 2. Configure location (optional)

By default the scheduler uses **Amsterdam** (52.37°N, 4.90°E, Europe/Amsterdam). Override with environment variables:

| Variable | Default | Description |
|----------|---------|--------------|
| `RAMADAN_LATITUDE` | 52.3676 | Latitude |
| `RAMADAN_LONGITUDE` | 4.9041 | Longitude |
| `RAMADAN_TIMEZONE` | Europe/Amsterdam | Timezone (e.g. Europe/Amsterdam, Europe/London) |
| `RAMADAN_OFFSET_AFTER_SUNRISE` | 5 | Minutes after sunrise to run |
| `RAMADAN_OFFSET_BEFORE_SUNSET` | 5 | Minutes before sunset to run |

Example for a different city:

```bash
export RAMADAN_LATITUDE=51.5074
export RAMADAN_LONGITUDE=-0.1278
export RAMADAN_TIMEZONE=Europe/London
```

#### 3. Discord webhook

Set the webhook so the video is posted to Discord:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
# or for Ramadan-only channel:
export RAMADAN_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

#### 4. Run the scheduler as a systemd service (Ubuntu)

So the scheduler starts on boot and restarts if it crashes:

**4.1** Copy and edit the service file**

```bash
mkdir -p ~/.config/systemd/user
cp ramadan-scheduler.service.example ~/.config/systemd/user/ramadan-scheduler.service
nano ~/.config/systemd/user/ramadan-scheduler.service
```

Replace `/path/to/RamadanOeroen` with the real path (e.g. `/home/ubuntu/RamadanOeroen`). If you use a venv, set `ExecStart` to:

```
ExecStart=/path/to/RamadanOeroen/.venv/bin/python /path/to/RamadanOeroen/ramadan_scheduler.py
```

**4.2** Optional: env file for webhook and location**

Create `/path/to/RamadanOeroen/ramadan.env`:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
RAMADAN_LATITUDE=52.3676
RAMADAN_LONGITUDE=4.9041
RAMADAN_TIMEZONE=Europe/Amsterdam
```

In the service file, add:

```
EnvironmentFile=/path/to/RamadanOeroen/ramadan.env
```

**4.3** Enable and start**

```bash
systemctl --user daemon-reload
systemctl --user enable ramadan-scheduler
systemctl --user start ramadan-scheduler
```

**4.4** Check status and logs**

```bash
systemctl --user status ramadan-scheduler
journalctl --user -u ramadan-scheduler -f
```

**4.5** Stop or disable**

```bash
systemctl --user stop ramadan-scheduler
systemctl --user disable ramadan-scheduler
```

---

### Alternative: run in background (no systemd)

If you prefer not to use systemd (e.g. one-off on a server):

```bash
cd /path/to/RamadanOeroen
source .venv/bin/activate
nohup python3 ramadan_scheduler.py >> ramadan_scheduler.log 2>&1 &
```

Or run inside `screen` or `tmux` so you can reattach:

```bash
screen -S ramadan
cd /path/to/RamadanOeroen && source .venv/bin/activate && python3 ramadan_scheduler.py
# Detach: Ctrl+A, D. Reattach: screen -r ramadan
```

---

### When it runs

- Start the scheduler **once** at or before Ramadan start (e.g. 17 February 2025).
- It runs at **sunrise + 5 min** and **sundown − 5 min** every day until Ramadan end (start + 29 days), then it exits.
- No need to stop it manually after Ramadan.

---

## macOS (optional)

On macOS you can use **launchd** to start the scheduler at login and keep it running:

1. Copy `com.ramadan.scheduler.plist.example` to `~/Library/LaunchAgents/com.ramadan.scheduler.plist`.
2. Replace `ABSOLUTE_PATH_TO_RamadanOeroen` with your project path.
3. Run: `launchctl load ~/Library/LaunchAgents/com.ramadan.scheduler.plist`
4. Logs: `tail -f /path/to/RamadanOeroen/ramadan_scheduler.log`

---

## Summary

| Environment | Recommended approach |
|-------------|------------------------|
| **Ubuntu / Linux** | systemd user service (`ramadan-scheduler.service`) – starts on login, restarts on failure |
| **macOS** | launchd plist (`com.ramadan.scheduler.plist`) |
| **Any** | Manual: `nohup python3 ramadan_scheduler.py >> ramadan_scheduler.log 2>&1 &` or inside `screen`/`tmux` |

The scheduler uses **astral** for real sunrise/sunset at your location, so post times follow the actual sun for your timezone.
