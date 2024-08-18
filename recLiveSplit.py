import os
import subprocess
import sys
from datetime import datetime
import time
import json

# Generate date. Needs fixed, seems time too here.
dateNow = datetime.now().strftime("%Y%m%d")

# Prompt for the duration of each part (in minutes)
part_duration = int(input("Enter the duration for each part (in minutes): ")) * 60  # Convert to seconds

# Prompt for the total duration to run the script (in hours and minutes)
total_hours = int(input("Enter the total hours to run the script: "))
total_minutes = int(input("Enter the additional minutes to run the script: "))
total_duration = (total_hours * 3600) + (total_minutes * 60)  # Convert to seconds

# Check if the correct number of arguments is provided
if len(sys.argv) != 3:
    print("Usage: python3 recLiveSplit.py <RESOLUTION> <LIVE_STREAM_URL>")
    sys.exit(1)

# Assign arguments to variables to run the script
# Argument 1 is video resoluton e.g. 360 or 720
video_resolution = sys.argv[1]
# Argument 2 is the URL
LIVE_STREAM_URL = sys.argv[2]

# Command to get video metadata using yt-dlp (including channel name)
yt_dlp_info_command = [
    "yt-dlp",
    "--cookies-from-browser", "chrome",
    "--dump-json",
    "--skip-download",
    LIVE_STREAM_URL	
]

try:
    # Extract metadata
    metadata = subprocess.check_output(yt_dlp_info_command).strip().decode('utf-8')
    metadata_json = json.loads(metadata)
    channel_name = metadata_json.get('uploader', 'unknown_channel').replace(" ", "_")
    title = metadata_json.get('title', 'unknown_title')

    # Sanitize and limit the title to 64 characters
    yt_dlp_sanitize_command = [
    	"yt-dlp",
    	"--cookies-from-browser", "chrome",
    	"--restrict-filenames",  # Ensure filename safety
    	"--windows-filenames",   # Force windows filename safety
    	"--get-filename",
    	"-o", "%(title).64s.%(ext)s",
    	LIVE_STREAM_URL
    ]

    # Make sure output filenamn is restricted to normal characters
    sanitized_title = subprocess.check_output(yt_dlp_sanitize_command).strip().decode('utf-8').rsplit('.', 1)[0]

    # Output dir using channel name and date.
    # NOTE: CHANGE DIR TO WHERE YOU WANT DLs
    base_output_dir = f"/home/anon/Videos/{channel_name}/{dateNow}"
    OUTPUT_DIR = base_output_dir

    # Find a unique directory name
    counter = 1
    while os.path.exists(OUTPUT_DIR):
        OUTPUT_DIR = f"{base_output_dir}_{counter}"
        counter += 1

    # Create the unique output directory
    os.makedirs(OUTPUT_DIR)

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Command to get the direct stream URL using yt-dlp
    # NOTE: Right now YouTube is making it difficult to download.
    # Using --cookies-from-browser <BROWSER> 
    # In order to not get error 
    # (must be signed in to YouTube on that browser)
    yt_dlp_command = [
        "yt-dlp",
        f"-f best[height<={video_resolution}]",
        "--cookies-from-browser", "chrome",
        "--hls-use-mpegts",
        "--ignore-config",
        "-g", LIVE_STREAM_URL
    ]

    # Get the direct stream URL
    stream_url = subprocess.check_output(yt_dlp_command).strip().decode('utf-8')
    
    part = 1
    remaining_duration = total_duration
    while remaining_duration > 0:
        current_duration = min(remaining_duration, part_duration)
        timeNow = datetime.now().strftime("%H%M_%S")
        output_file = os.path.join(OUTPUT_DIR, f"{part:03d}{sanitized_title}{dateNow}_{timeNow}.mp4")

        # Command to record the live stream using ffmpeg
        ffmpeg_command = [
            "ffmpeg",
            "-i", stream_url,
            "-t", str(current_duration),
            "-c", "copy",
            output_file
        ]

        # Run the ffmpeg command
        subprocess.run(ffmpeg_command)

        # Update remaining duration and part counter
        remaining_duration -= current_duration
        part += 1

except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
