from flask import Flask, request, jsonify, render_template, send_file
import os
from werkzeug.utils import secure_filename
from remove_bg_noise import remove_noise
import uuid
import threading

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# To store job statuses
jobs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

def process_video_job(job_id, input_path, output_path):
    try:
        remove_noise(input_path, output_path)
        jobs[job_id] = {'status': 'completed', 'output_file': os.path.basename(output_path)}
    except Exception as e:
        jobs[job_id] = {'status': 'error', 'error': str(e)}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        job_id = str(uuid.uuid4())
        
        # Save original
        base, ext = os.path.splitext(filename)
        input_filename = f"{base}_{job_id}{ext}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)
        
        # Output path
        output_filename = f"{base}_denoised{ext}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        jobs[job_id] = {'status': 'processing'}
        
        # Run background thread
        thread = threading.Thread(target=process_video_job, args=(job_id, input_path, output_path))
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Upload successful, processing started.'})

@app.route('/status/<job_id>')
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
