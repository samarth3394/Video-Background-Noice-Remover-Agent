import sys
import subprocess
import os
import uuid

def install_deps():
    try:
        import moviepy
        import noisereduce
        import scipy
        import imageio_ffmpeg
        import flask
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy==1.0.3", "noisereduce", "scipy", "imageio-ffmpeg", "flask"])

install_deps()

from scipy.io import wavfile
import noisereduce as nr
import imageio_ffmpeg

def remove_noise(video_path, output_path=None):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File not found: {video_path}")

    if output_path is None:
        output_path = video_path.rsplit(".", 1)[0] + "_denoised_original." + video_path.rsplit(".", 1)[1]
        
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    unique_id = str(uuid.uuid4())[:8]
    temp_audio_path = f"temp_audio_{unique_id}.wav"
    temp_denoised_audio_path = f"temp_denoised_audio_{unique_id}.wav"
    
    try:
        print("Extracting audio using ffmpeg...")
        subprocess.check_call([
            ffmpeg_exe, "-y", "-i", video_path, "-q:a", "0", "-map", "a", temp_audio_path
        ])
        
        print("Reading audio for noise reduction...")
        rate, data = wavfile.read(temp_audio_path)
        
        print("Removing background noise...")
        if len(data.shape) == 2:
            data = data.T
            reduced_noise = nr.reduce_noise(y=data, sr=rate)
            reduced_noise = reduced_noise.T
        else:
            reduced_noise = nr.reduce_noise(y=data, sr=rate)
            
        wavfile.write(temp_denoised_audio_path, rate, reduced_noise)
        
        print("Replacing audio in video without altering video quality...")
        subprocess.check_call([
            ffmpeg_exe, "-y", "-i", video_path, "-i", temp_denoised_audio_path,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
            output_path
        ])
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists(temp_denoised_audio_path):
            os.remove(temp_denoised_audio_path)
            
    print("Done! Video size and quality is preserved.")
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default=r"C:\Users\User\Downloads\reel\VID_20260611_175021.mp4")
    args = parser.parse_args()
    remove_noise(args.video)
