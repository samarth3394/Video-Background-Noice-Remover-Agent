from waitress import serve
from app import app
import os

if __name__ == '__main__':
    # Ensure port is an integer
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting production server on port {port}...")
    serve(app, host='0.0.0.0', port=port)
