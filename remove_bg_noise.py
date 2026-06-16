import sys
import subprocess
import os
import uuid
import numpy as np

def install_deps():
    required = {
        'scipy': 'scipy',
        'noisereduce': 'noisereduce', 
        'imageio_ffmpeg': 'imageio-ffmpeg',
        'flask': 'flask',
        'torch': 'torch',
        'demucs': 'demucs',
    }
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print(f"Installing: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

install_deps()

import torch
torch.set_num_threads(2) # Limit CPU threads to prevent Flask server from hanging
import torchaudio
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import noisereduce as nr
import imageio_ffmpeg


def normalize_audio(audio_data, target_peak=0.95):
    """Normalize audio to target peak level"""
    max_amp = np.max(np.abs(audio_data))
    if max_amp == 0:
        return audio_data
    # Scale to target peak (0.95 to avoid clipping)
    normalized = (audio_data / max_amp) * target_peak
    return normalized


def separate_vocals_demucs(audio_path, output_vocals_path):
    """Use Meta's Demucs AI model to isolate vocals (speech) from background noise"""
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    
    print("Loading Demucs AI model (htdemucs)...")
    model = get_model('htdemucs')
    model.eval()
    
    print("Loading audio file...")
    wav, sr = torchaudio.load(audio_path, backend="soundfile")
    
    # Demucs expects specific sample rate
    if sr != model.samplerate:
        print(f"Resampling from {sr}Hz to {model.samplerate}Hz...")
        resampler = torchaudio.transforms.Resample(sr, model.samplerate)
        wav = resampler(wav)
        sr = model.samplerate
    
    # Ensure stereo
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)
    
    # Add batch dimension
    wav = wav.unsqueeze(0)
    
    print("Separating vocals from background using AI...")
    with torch.no_grad():
        sources = apply_model(model, wav, shifts=0, split=True, overlap=0.1, device='cpu', progress=True)
    
    # Demucs htdemucs outputs: drums, bass, other, vocals
    # We want the vocals (index 3)
    vocals = sources[0, 3]  # Shape: [channels, samples]
    
    # Demucs already provides clean vocals, skip redundant and slow noisereduce
    vocals_np = vocals.numpy()
    
    # Normalize volume to make voice louder and clearer
    vocals_np = normalize_audio(vocals_np)
    
    # Convert back to tensor and save
    vocals_tensor = torch.from_numpy(vocals_np).float()
    
    print(f"Saving isolated vocals to {output_vocals_path}")
    torchaudio.save(output_vocals_path, vocals_tensor, sr, backend="soundfile")
    
    return sr


def remove_noise(video_path, output_path=None):
    """Main function: Extract audio, isolate speech, replace in video"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File not found: {video_path}")

    if output_path is None:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_clean.mp4"
        
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    unique_id = str(uuid.uuid4())[:8]
    temp_audio_path = os.path.join(os.path.dirname(video_path), f"temp_audio_{unique_id}.wav")
    temp_vocals_path = os.path.join(os.path.dirname(video_path), f"temp_vocals_{unique_id}.wav")
    
    try:
        # Step 1: Extract audio from video
        print("=" * 50)
        print("STEP 1: Extracting audio from video...")
        print("=" * 50)
        subprocess.check_call([
            ffmpeg_exe, "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            temp_audio_path
        ], stderr=subprocess.DEVNULL)
        
        # Step 2: Separate vocals using Demucs AI
        print("=" * 50)
        print("STEP 2: AI Speech Isolation (Demucs)...")
        print("=" * 50)
        output_sr = separate_vocals_demucs(temp_audio_path, temp_vocals_path)
        
        # Step 3: Replace audio in video
        print("=" * 50)
        print("STEP 3: Replacing audio in video...")
        print("=" * 50)
        
        # Ensure output is .mp4
        if not output_path.lower().endswith('.mp4'):
            output_path = os.path.splitext(output_path)[0] + '.mp4'
        
        # Try copy mode first (fast, preserves original quality)
        try:
            print("Trying fast copy mode...")
            result = subprocess.run([
                ffmpeg_exe, "-y",
                "-i", video_path,
                "-i", temp_vocals_path,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                "-movflags", "+faststart",
                output_path
            ], stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=120)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, "ffmpeg", stderr=result.stderr)
            print("Fast copy mode succeeded!")
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Copy mode failed ({e}), trying re-encode mode...")
            # Fallback: re-encode with libx264
            result = subprocess.run([
                ffmpeg_exe, "-y",
                "-i", video_path,
                "-i", temp_vocals_path,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                "-movflags", "+faststart",
                output_path
            ], stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=300)
            
            if result.returncode != 0:
                stderr_msg = result.stderr.decode('utf-8', errors='replace') if result.stderr else 'Unknown error'
                print(f"FFmpeg re-encode error: {stderr_msg}")
                raise RuntimeError(f"FFmpeg failed: {stderr_msg}")
            print("Re-encode mode succeeded!")
        
    finally:
        # Cleanup temp files
        for f in [temp_audio_path, temp_vocals_path]:
            if os.path.exists(f):
                os.remove(f)
            
    print("=" * 50)
    print(f"SUCCESS! Clean video saved to: {output_path}")
    print("=" * 50)
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Video Background Noise Remover - Speech Isolation")
    parser.add_argument("--video", type=str, default=r"C:\Users\User\Downloads\reel\VID_20260611_175021.mp4",
                        help="Path to the input video file")
    args = parser.parse_args()
    remove_noise(args.video)
