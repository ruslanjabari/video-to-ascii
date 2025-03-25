#!/usr/bin/env python3
import os
import time
import subprocess
import datetime
import json
import requests
from pytube import YouTube, Search
import schedule

# Configuration
CHANNEL_USERNAME = 'fdotinc'
CHANNEL_URL = f'https://www.youtube.com/@{CHANNEL_USERNAME}'
VIDEOS_DIR = './videos'
CONFIG_FILE = './youtube_downloader_config.json'
# LOCAL_VIDEOS = ['./art.mp4', './art2.mp4']
LOCAL_VIDEOS = []

def ensure_dirs():
    """Ensure necessary directories exist"""
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
    
    # Create config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'last_check': '',
                'downloaded_videos': []
            }, f)

def get_latest_video_id():
    """Get the latest video ID using yt-dlp directly"""
    print(f"Checking for new videos on channel: {CHANNEL_USERNAME}")
    
    try:
        # Use yt-dlp directly since we confirmed it works correctly
        import subprocess
        
        print(f"Using yt-dlp to get latest video from: {CHANNEL_URL}/videos")
        
        # Run yt-dlp command to get title and ID of the latest video
        process = subprocess.run(
            ["yt-dlp", "--get-title", "--get-id", f"{CHANNEL_URL}/videos", "-I", "1"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get output and split into lines
        output = process.stdout.strip().split("\n")
        
        if len(output) < 2:
            print("Unexpected output format from yt-dlp")
            return None, None
            
        # First line is title, second line is video ID
        title = output[0]
        video_id = output[1]
        
        print(f"Found latest video using yt-dlp: {title} (ID: {video_id})")
        return video_id, title
        
    except subprocess.CalledProcessError as e:
        print(f"Error running yt-dlp: {e}")
        print(f"Error output: {e.stderr}")
        
        # Fall back to the original method if yt-dlp fails
        print("Falling back to pytube method...")
        
        try:
            # Use the Channel class to get videos
            from pytube import Channel
            
            channel = Channel(CHANNEL_URL)
            video_urls = channel.video_urls
            
            if not video_urls:
                print("No videos found on channel")
                return None, None
                
            video_url = video_urls[0]
            video_id = video_url.split('v=')[1]
            if '&' in video_id:
                video_id = video_id.split('&')[0]
            
            yt = YouTube(video_url)
            title = yt.title
            
            print(f"Found latest video via fallback: {title} (ID: {video_id})")
            return video_id, title
            
        except Exception as e2:
            print(f"Fallback method also failed: {e2}")
            return None, None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

def load_config():
    """Load the configuration file"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save the configuration file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def download_video(video_id, video_title):
    """Download a video from YouTube"""
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"Downloading video: {video_title} from {video_url}")
        
        # Create a safe filename from the title
        safe_title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in video_title)
        filename = f"{video_id}_{safe_title}.mp4"
        file_path = os.path.join(VIDEOS_DIR, filename)
        
        # Try using yt-dlp instead of pytube as it's more reliable
        try:
            import yt_dlp
            print("Using yt-dlp to download video...")
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': file_path,
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                print(f"Downloaded to {file_path}")
                return file_path
                
        except ImportError:
            print("yt-dlp not installed. Falling back to pytube...")
            # Fall back to pytube method
            
            yt = YouTube(video_url)
            
            # Print available streams for debugging
            print(f"Available streams count: {len(list(yt.streams))}")
            
            # Try to get a stream with both video and audio
            video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            
            if not video_stream:
                print("No suitable video stream found, trying any mp4 stream")
                video_stream = yt.streams.filter(file_extension='mp4').first()
            
            if not video_stream:
                print("No mp4 stream found, trying any stream")
                video_stream = yt.streams.first()
            
            if not video_stream:
                print("No streams available for this video")
                return None
            
            print(f"Starting download using stream: {video_stream}")
            
            # First, download to a temporary filename
            temp_file = video_stream.download(output_path=VIDEOS_DIR)
            
            # Then rename to our desired filename
            os.rename(temp_file, file_path)
            
            print(f"Downloaded to {file_path}")
            return file_path
            
    except Exception as e:
        print(f"Error downloading video: {e}")
        
        # Try download using subprocess and youtube-dl or yt-dlp if available
        try:
            print("Trying system-level download tools...")
            
            # Try yt-dlp first (it's more modern and reliable)
            download_cmd = None
            for cmd in ['yt-dlp', 'youtube-dl']:
                if subprocess.run(['which', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                    download_cmd = cmd
                    break
            
            if download_cmd:
                print(f"Using {download_cmd} to download video...")
                subprocess.run([
                    download_cmd, 
                    video_url, 
                    '-o', file_path, 
                    '-f', 'best'
                ], check=True)
                
                print(f"Downloaded to {file_path} using {download_cmd}")
                return file_path
            else:
                print("No download tools available on system.")
                return None
        
        except Exception as e2:
            print(f"System-level download also failed: {e2}")
            return None

def play_videos_loop(video_files):
    """Play videos in a loop using video-to-ascii"""
    if not video_files:
        print("No videos to play")
        return
    
    print(f"Playing {len(video_files)} videos in a loop")
    
    try:
        while True:
            for video in video_files:
                if os.path.exists(video):
                    print(f"Playing {video}")
                    subprocess.run(["video-to-ascii", "-f", video, "--strategy", "adaptive"])
                else:
                    print(f"Video not found: {video}")
    except KeyboardInterrupt:
        print("Playback stopped")

def check_and_download():
    """Check for new videos and download them"""
    ensure_dirs()
    config = load_config()
    
    # Update last check time
    now = datetime.datetime.now().isoformat()
    config['last_check'] = now
    
    video_id, video_title = get_latest_video_id()
    
    if not video_id:
        print("No videos found or error occurred")
        save_config(config)
        return None
    
    # Check if we already downloaded this video
    if 'downloaded_videos' in config and video_id in config['downloaded_videos']:
        print(f"Already downloaded video: {video_title}")
        save_config(config)
        return None
    
    # Download the video
    video_path = download_video(video_id, video_title)
    
    if video_path:
        # Update config with the new video
        if 'downloaded_videos' not in config:
            config['downloaded_videos'] = []
        config['downloaded_videos'].append(video_id)
        save_config(config)
        return video_path
    
    return None

def get_all_video_files():
    """Get all video files to play"""
    youtube_videos = []
    
    # Find all downloaded YouTube videos
    if os.path.exists(VIDEOS_DIR):
        for file in os.listdir(VIDEOS_DIR):
            if file.endswith(".mp4"):
                youtube_videos.append(os.path.join(VIDEOS_DIR, file))
    
    # Combine with local art videos
    all_videos = []
    for video in LOCAL_VIDEOS:
        if os.path.exists(video):
            all_videos.append(video)
        else:
            print(f"Warning: Local video not found: {video}")
    
    all_videos.extend(youtube_videos)
    print(f"Videos to play: {all_videos}")
    return all_videos

def run_daily_check():
    """Run the daily check as a scheduled task"""
    print(f"Running scheduled check at {datetime.datetime.now()}")
    new_video = check_and_download()
    
    # Get all videos to play
    all_videos = get_all_video_files()
    print(f"Found {len(all_videos)} videos to play")
    
    # Play videos in a loop
    return all_videos

def main():
    """Main function"""
    print("Starting YouTube video downloader and ASCII player")
    ensure_dirs()
    
    # Run immediately on startup
    all_videos = run_daily_check()
    
    # Schedule the check to run daily
    schedule.every(24).hours.do(run_daily_check)
    
    # Play videos in a loop
    try:
        if all_videos:
            play_videos_loop(all_videos)
        else:
            print("No videos to play, waiting for scheduled check")
            while True:
                schedule.run_pending()
                time.sleep(60)
    except KeyboardInterrupt:
        print("Program stopped by user")

if __name__ == "__main__":
    main()