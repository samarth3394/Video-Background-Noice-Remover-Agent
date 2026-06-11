# ClearVoice - AI Video Background Noise Remover

A modern web application that automatically removes background noise from videos using AI, while **preserving 100% of the original video quality and size**.

## Features

- **Advanced Noise Reduction**: Uses `noisereduce` to intelligently profile and eliminate background noise from the audio track.
- **Zero Video Quality Loss**: Uses `ffmpeg -c:v copy` to mux the cleaned audio back into the original video container without re-encoding the video stream.
- **Modern Web Interface**: A sleek, dark-themed UI built with Glassmorphism, CSS gradients, and fluid animations.
- **Drag and Drop Support**: Easy uploading for `.mp4`, `.mov`, and `.avi` formats.
- **Real-Time Processing Status**: Dynamic loading indicators simulating progress.

## Technologies Used

- **Backend**: Python, Flask
- **Audio Processing**: `scipy`, `noisereduce`
- **Video Processing**: `imageio-ffmpeg`
- **Frontend**: Vanilla HTML5, CSS3, JavaScript

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samarth3394/Video-Background-Noice-Remover-Agent.git
   cd Video-Background-Noice-Remover-Agent
   ```

2. **Install dependencies:**
   The application will automatically try to install required dependencies on first run. To install them manually:
   ```bash
   pip install flask moviepy==1.0.3 noisereduce scipy imageio-ffmpeg
   ```

3. **Run the Application:**
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`.

## Usage

1. Open `http://localhost:5000` in your web browser.
2. Drag and drop your noisy video into the upload area.
3. Click on **Remove Noise**.
4. Wait for the processing to finish.
5. Click **Download Video** to get your crystal-clear video file!
