# Bharti Voice Cleaner

A premium, modern web application that automatically isolates human speech and removes all background noise from videos using state-of-the-art AI, while **preserving 100% of the original video quality and size**.

## Features

- **Advanced AI Voice Isolation**: Uses **Meta Demucs AI**, a deep learning neural network, to intelligently separate human vocals from environmental noise (wind, traffic, music, chatter) at the neural level.
- **Zero Video Quality Loss**: Uses `ffmpeg` to extract and remux the cleaned audio back into the original video container without re-encoding the video stream.
- **Premium Apple-Style Interface**: A sleek, pure-black UI built with Glassmorphism, 3D interactive tilt animations, and fluid CSS gradients.
- **Drag and Drop Support**: Easy uploading for `.mp4`, `.mov`, and `.avi` formats.
- **Asynchronous Processing**: Non-blocking background thread processing for heavy AI tasks with real-time UI polling.

## Technologies & Libraries Used

### Backend
- **Python 3**: Core programming language.
- **Flask**: Web framework for serving the application and handling API routes.
- **Werkzeug**: Used for secure file handling.

### AI & Audio Processing
- **Meta Demucs**: State-of-the-art music and audio source separation neural network model (PyTorch based).
- **PyTorch (torch & torchaudio)**: Deep learning framework running the Demucs model.
- **FFmpeg**: Handled via `subprocess` for lightning-fast extraction and muxing of audio/video streams without re-encoding the video.
- **SoundFile**: Audio library used as the backend for `torchaudio` to read and write audio files efficiently.

### Frontend
- **Vanilla HTML5, CSS3, JavaScript**: No heavy frontend frameworks. Pure performance.
- **CSS 3D Transforms & Glassmorphism**: For premium Apple-like interactive components.
- **IntersectionObserver API**: For smooth scroll animations.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samarth3394/Video-Background-Noice-Remover-Agent.git
   cd Video-Background-Noice-Remover-Agent
   ```

2. **Install dependencies:**
   Make sure you have FFmpeg installed on your system and added to your PATH. Then install the Python libraries:
   ```bash
   pip install flask demucs torch torchaudio soundfile
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`.

## Usage

1. Open `http://localhost:5000` in your web browser.
2. Drag and drop your noisy video into the upload area.
3. Click on **Remove Background Noise**.
4. Wait for the Meta Demucs AI processing to finish.
5. Click **Download Clean Video** to get your crystal-clear video file!
