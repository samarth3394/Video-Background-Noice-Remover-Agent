import os
import traceback
from celery import Celery
from remove_bg_noise import remove_noise

# Configure Celery with Redis as broker and backend
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery('video_tasks', broker=redis_url, backend=redis_url)

@celery_app.task(bind=True, name='tasks.process_video_task')
def process_video_task(self, input_path, output_path):
    try:
        print(f"[CELERY] Starting noise removal for {input_path}...")
        
        # Update custom state if needed
        self.update_state(state='PROCESSING', meta={'progress': 'Started processing video'})
        
        # Call the actual video processing function
        final_output_path = remove_noise(input_path, output_path)
        
        print(f"[CELERY] Job completed successfully: {final_output_path}")
        return {'status': 'completed', 'output_file': os.path.basename(final_output_path)}
        
    except Exception as e:
        print(f"[CELERY] Error processing video: {e}")
        traceback.print_exc()
        # Celery will automatically mark task as FAILURE if an exception is raised
        raise Exception(f"Processing failed: {str(e)}")

if __name__ == '__main__':
    celery_app.start()
