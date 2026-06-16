import os
import traceback
from werkzeug.utils import secure_filename
import uuid
from flask import Flask, request, jsonify, render_template, send_file
from tasks import process_video_task
from models import db, VideoJob
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    default_limits=["100 per day", "20 per hour"]
)

with app.app_context():
    db.create_all()

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
@limiter.limit("5 per hour")
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
        
        # Save to DB
        job = VideoJob(id=task.id, status='PENDING', input_file=input_filename, output_file=output_filename)
        db.session.add(job)
        db.session.commit()
        
        return jsonify({'job_id': task.id, 'message': 'Upload successful, processing queued via Celery.'})

@app.route('/status/<job_id>')
def get_status(job_id):
    job = VideoJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Retrieve task from Celery
    task = process_video_task.AsyncResult(job_id)
    
    # Update DB if state changed
    if task.state != job.status and task.state in ['SUCCESS', 'FAILURE', 'PROCESSING']:
        job.status = task.state
        db.session.commit()
    
    response = {
        'status': job.status, # PENDING, STARTED, SUCCESS, FAILURE, PROCESSING
    }
    
    if job.status == 'SUCCESS':
        response['output_file'] = job.output_file
    elif job.status == 'FAILURE':
        response['error'] = str(task.info) if task.info else "Processing failed"
    
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
