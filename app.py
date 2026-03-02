import logging
import os
from flask import Flask, send_from_directory
from config import config
from workers.camera_worker import CameraWorker
from api.routes import api_bp

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def create_app():
    # Serve static files from the React dist directory
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
    # Increase max upload size to 1GB to accommodate large CCTV video clips
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024
    
    # Store config and worker on app for route access
    app.config_obj = config
    
    # Initialize and start the background worker
    # Default to camera index 0
    worker = CameraWorker(camera_id=1, source=0, config_obj=config)
    worker.start()
    
    app.camera_worker = worker
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
            
    return app

if __name__ == "__main__":
    app = create_app()
    logging.info(f"Starting Flask application on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, threaded=True)
