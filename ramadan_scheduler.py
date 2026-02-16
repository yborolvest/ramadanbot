"""
Ramadan scheduler: run ramadan_video.py at sunrise and sundown for the duration of Ramadan.
Uses the astral library for location-based sunrise/sunset times.
Run as a long-running process (e.g. started by launchd at Ramadan start).
"""
import os
import sys
import time
import datetime
from typing import Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

# Add project root so we can import ramadan_video
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ramadan_video import RAMADAN_START_DATE, main as run_ramadan_video

try:
    from astral import LocationInfo
    from astral.sun import sun
    HAS_ASTRAL = True
except ImportError:
    HAS_ASTRAL = False

# ---------- CONFIG ----------

# Ramadan end: ~29 days after start (configurable; lunar calendar varies)
RAMADAN_DAYS = 29
RAMADAN_END_DATE = RAMADAN_START_DATE + datetime.timedelta(days=RAMADAN_DAYS)

# Location for sunrise/sunset (default: Amsterdam)
# Override with env: RAMADAN_LATITUDE, RAMADAN_LONGITUDE, RAMADAN_TIMEZONE
LOCATION_NAME = os.environ.get("RAMADAN_LOCATION_NAME", "Amsterdam")
LOCATION_REGION = os.environ.get("RAMADAN_LOCATION_REGION", "Netherlands")
LOCATION_TIMEZONE = os.environ.get("RAMADAN_TIMEZONE", "Europe/Amsterdam")
LOCATION_LATITUDE = float(os.environ.get("RAMADAN_LATITUDE", "52.3676"))
LOCATION_LONGITUDE = float(os.environ.get("RAMADAN_LONGITUDE", "4.9041"))

# How many minutes after sunrise / before sunset to run (e.g. 5 = run 5 min after sunrise, 5 min before sunset)
RUN_OFFSET_MINUTES_AFTER_SUNRISE = int(os.environ.get("RAMADAN_OFFSET_AFTER_SUNRISE", "5"))
RUN_OFFSET_MINUTES_BEFORE_SUNSET = int(os.environ.get("RAMADAN_OFFSET_BEFORE_SUNSET", "5"))


def get_location():
    """Build LocationInfo from config."""
    return LocationInfo(
        LOCATION_NAME,
        LOCATION_REGION,
        LOCATION_TIMEZONE,
        LOCATION_LATITUDE,
        LOCATION_LONGITUDE,
    )


def get_sun_times(location, day: datetime.date):
    """Return (sunrise, sunset) as timezone-aware datetimes in location timezone."""
    tz = ZoneInfo(location.timezone)
    s = sun(location.observer, date=day, tzinfo=tz)
    return s["sunrise"], s["sunset"]


def next_run_time(location) -> Tuple[Optional[datetime.datetime], str]:
    """
    Return (next_run_datetime, "sunrise"|"sunset") for the next scheduled run in the future.
    If we're outside Ramadan, return (None, "").
    """
    tz = ZoneInfo(location.timezone)
    now = datetime.datetime.now(tz)
    today = now.date()

    if today < RAMADAN_START_DATE:
        return None, ""
    if today > RAMADAN_END_DATE:
        return None, ""

    sunrise, sunset = get_sun_times(location, today)

    # Apply offsets: run a few minutes after sunrise, a few minutes before sunset
    run_sunrise = sunrise + datetime.timedelta(minutes=RUN_OFFSET_MINUTES_AFTER_SUNRISE)
    run_sunset = sunset - datetime.timedelta(minutes=RUN_OFFSET_MINUTES_BEFORE_SUNSET)

    # If run_sunset is before run_sunrise (short day), use midpoint or just sunrise
    if run_sunset <= run_sunrise:
        run_sunset = run_sunrise + datetime.timedelta(minutes=1)

    if now < run_sunrise:
        return run_sunrise, "sunrise"
    if now < run_sunset:
        return run_sunset, "sunset"
    # After today's sunset: next is tomorrow's sunrise
    tomorrow = today + datetime.timedelta(days=1)
    if tomorrow > RAMADAN_END_DATE:
        return None, ""
    sunrise_tomorrow, _ = get_sun_times(location, tomorrow)
    run_tomorrow = sunrise_tomorrow + datetime.timedelta(minutes=RUN_OFFSET_MINUTES_AFTER_SUNRISE)
    return run_tomorrow, "sunrise"


def sleep_until(target: datetime.datetime):
    """Sleep until target (timezone-aware datetime)."""
    now = datetime.datetime.now(target.tzinfo)
    delta = (target - now).total_seconds()
    if delta <= 0:
        return
    print(f"Sleeping until {target.strftime('%Y-%m-%d %H:%M %Z')} ({delta / 60:.0f} minutes)")
    time.sleep(delta)


def run_scheduler(no_discord: bool = False):
    """Main loop: wait for next sunrise/sunset, run video, repeat until Ramadan ends."""
    if not HAS_ASTRAL:
        print("Error: astral is required. Install with: pip install astral")
        sys.exit(1)

    location = get_location()
    print(f"Ramadan scheduler: {RAMADAN_START_DATE} → {RAMADAN_END_DATE}")
    print(f"Location: {location.name} ({location.latitude:.2f}, {location.longitude:.2f}) {location.timezone}")
    print("Run at: sunrise + {} min, sunset - {} min".format(
        RUN_OFFSET_MINUTES_AFTER_SUNRISE, RUN_OFFSET_MINUTES_BEFORE_SUNSET))
    print("Post to Discord:", not no_discord)
    print("---")

    while True:
        next_run, event = next_run_time(location)
        if next_run is None:
            print("Ramadan period ended or not started. Exiting.")
            break

        sleep_until(next_run)

        print(f"\n[{datetime.datetime.now().isoformat()}] Running at {event} — generating video...")
        try:
            run_ramadan_video(post_to_discord_enabled=not no_discord)
        except Exception as e:
            print(f"Error running ramadan_video: {e}")
            import traceback
            traceback.print_exc()
        print("Done. Waiting for next run.\n")


def main():
    no_discord = "--no-discord" in sys.argv
    run_scheduler(no_discord=no_discord)


if __name__ == "__main__":
    main()
