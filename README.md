# Weersverwachtingetjes

Automated Dutch weather forecast video generator using KNMI Open Data API.

## Setup Instructions

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yborolvest/weerberichtjes.git
cd weerberichtjes
```

### 2. Install Python Dependencies

Make sure you have Python 3.8+ installed, then install the required packages:

```bash
pip3 install -r requirements.txt
```

**Note:** On some systems, you may need to install additional system dependencies:
- **macOS**: `brew install ffmpeg` (required for MoviePy)
- **Linux (Ubuntu/Debian)**: `sudo apt-get install ffmpeg python3-dev`
- **Linux (Fedora)**: `sudo dnf install ffmpeg python3-devel`

### 3. Required Files and Directories

Ensure you have the following directory structure with the necessary media files:

```
Weersverwachtingetjes/
├── weather_video.py          # Main script
├── avatar.png                # Avatar image (optional)
├── voice_timing.json         # Voice timing data
├── music/                    # Music files
│   ├── cold.mp3
│   ├── hot.mp3
│   ├── normal.mp3
│   ├── rainy.mp3
│   └── warm.mp3
├── video_parts/
│   ├── backgrounds/          # Background videos
│   │   ├── cold.mp4
│   │   ├── hot.mp4
│   │   ├── normal.mp4
│   │   ├── rainy.mp4
│   │   └── warm.mp4
│   └── icons/256w/           # Weather icons (PNG files)
│       ├── clouded.png
│       ├── cloudy.png
│       ├── rain.png
│       ├── snow.png
│       ├── snowrain.png
│       ├── storm.png
│       ├── sunny.png
│       └── windy.png
└── voice/jeroen/clips/       # Voice clips
    ├── ee.wav
    ├── ja.wav
    ├── oe.wav
    └── uh.wav
```

**Important:** These media files are not included in the repository (they're in `.gitignore`). You'll need to add them manually to your local setup.

### 4. Environment Variables (Optional)

The script uses a default anonymous KNMI API key, but you can set your own:

```bash
export KNMI_API_KEY="your_api_key_here"
```

To get a registered API key, visit: https://developer.dataplatform.knmi.nl/

### 5. Discord Webhook (Optional)

If you want to automatically post videos to Discord, set up a webhook:

1. Create a Discord webhook (see `DISCORD_SETUP.md` for details)
2. Set the environment variable:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

### 6. Run the Script

```bash
python3 weather_video.py
```

The video will be generated as `weer_vandaag.mp4` in the current directory.

To disable Discord posting:
```bash
python3 weather_video.py --no-discord
```

---

## Ramadan version

A Ramadan variant generates a daily video with a **random Quran verse in Arabic** and a **random background** (from 5), using the same S3/MinIO setup for backgrounds. Ramadan start date: **17 February 2025**.

- **Quran API**: [quranapi.pages.dev](https://quranapi.pages.dev/) — no auth, no rate limit. Verses are fetched at random (surah + ayah).
- **Backgrounds**: One of 5 backgrounds is chosen at random. Same S3 bucket/credentials as weather; keys are `backgrounds/1.mp4` … `backgrounds/5.mp4`. Upload 5 background videos to S3 under those names.

### Run Ramadan video

```bash
python3 ramadan_video.py
```

Output: `ramadan_vandaag.mp4` (Arabic verse overlay, Dutch intro voice + subtitles, optional avatar, random background).

To disable Discord posting:
```bash
python3 ramadan_video.py --no-discord
```

### Ramadan config

- **Start date**: Script only runs on or after 17 February 2025 (configurable in `ramadan_video.py`: `RAMADAN_START_DATE`).
- **Music**: Looks for `music/ramadan.mp3`, then `music/normal.mp3`.
- **Discord**: Uses `RAMADAN_DISCORD_WEBHOOK_URL` if set, otherwise `DISCORD_WEBHOOK_URL`.

### Run at sunrise and sundown during Ramadan

To post the video **at sunrise and sundown** for the whole of Ramadan, use the scheduler:

```bash
pip install astral
python3 ramadan_scheduler.py
```

The scheduler uses your location (default: Amsterdam) to compute sunrise/sunset and runs `ramadan_video.py` twice per day.

**Ubuntu / Linux:** One-command setup: `chmod +x setup_ubuntu.sh && ./setup_ubuntu.sh` (installs deps, venv, systemd service). See **[RAMADAN_SCHEDULING.md](RAMADAN_SCHEDULING.md)** for details and macOS.

---

## Configuration

You can modify these settings at the top of `weather_video.py`:

- `CITY`: City name (default: "De Bilt")
- `COUNTRY`: Country name (default: "Netherlands")
- `NORMAL_TEXT_FONT_SIZE`: Font size for subtitles (default: 40)
- `TEMPERATURE_TEXT_FONT_SIZE`: Font size for temperature (default: 140)
- `SUBTITLE_BORDER_WIDTH`: Border width for subtitle box (default: 3)
- `TEMPERATURE_OVERLAY_BORDER_WIDTH`: Border width for temperature box (default: 2)
- `FORECAST_OVERLAY_BORDER_WIDTH`: Border width for forecast box (default: 2)

## Troubleshooting

### MoviePy/FFmpeg Issues

If you get errors about missing codecs or FFmpeg:
- Make sure FFmpeg is installed: `ffmpeg -version`
- On macOS: `brew install ffmpeg`
- On Linux: Install via your package manager

### NetCDF4 Installation Issues

If `netCDF4` fails to install:
- **macOS**: `brew install hdf5 netcdf` then `pip install netCDF4`
- **Linux**: `sudo apt-get install libhdf5-dev libnetcdf-dev` then `pip install netCDF4`

### Missing Media Files

If you get errors about missing files:
- Check that all required media files are in the correct directories
- Verify file paths match the structure shown above

### Font Issues

If fonts don't load correctly:
- The script uses system fonts (Arial). Make sure Arial is installed, or modify the font paths in the code.

## Scheduling (macOS)

See `DISCORD_SETUP.md` for instructions on setting up automatic daily posts using launchd.

## License

This project uses weather data from the KNMI Open Data API.
