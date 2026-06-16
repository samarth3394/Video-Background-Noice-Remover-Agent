import os
import traceback
from werkzeug.utils import secure_filename
import uuid
from flask import Flask, request, jsonify, render_template, send_file
from tasks import process_video_task

app = Flask(__name__)

# Security: Max file size 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

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
        output_filename = f"{base}_denoised.mp4"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Send job to Celery background queue
        task = process_video_task.delay(input_path, output_path)
        
        return jsonify({'job_id': task.id, 'message': 'Upload successful, processing queued via Celery.'})

@app.route('/status/<job_id>')
def get_status(job_id):
    # Retrieve task from Celery
    task = process_video_task.AsyncResult(job_id)
    
    response = {
        'status': task.state, # PENDING, STARTED, SUCCESS, FAILURE, PROCESSING
    }
    
    if task.state == 'SUCCESS':
        response['output_file'] = task.info.get('output_file')
    elif task.state == 'FAILURE':
        response['error'] = str(task.info)
    
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
