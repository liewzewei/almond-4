# Highway Vehicle Hazard Detection AI

Robust, modular, real-time hazard detection for high-angle highway CCTV footage.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment (Windows with Python 3.11)
py -3.11 -m venv venv

# Activate environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Data
Place your video file at `./data/sample_highway.mov` (supports `.mp4`, `.mov`, `.avi`).

### 3. Run Pipeline (CLI)
```bash
python main.py --video ./data/sample_highway.mp4 --mode run
```

### 4. Launch Dashboard (Streamlit)
```bash
streamlit run app/streamlit_app.py
```

### 5. Launch Highway Risk Dashboard (Web Frontend)
The system includes a new Bootstrap 5-based professional web dashboard that communicates with the Flask backend.

```bash
# Start the Flask server (serves both API and Frontend)
python app.py
```
After starting the server, open your browser and navigate to:
**http://127.0.0.1:5000/** or **http://127.0.0.1:5000/camera/1**

### 6. Flask API (Real-time Integration)
The system includes a Flask-based API for integration with other services and handles real-time processing via a background worker.

```bash
# Start the Flask server
python app.py
```

#### Key API Endpoints:
- `GET /health`: Health check endpoint.
- `GET /camera/<id>`: Simple HTML dashboard for a specific camera.
- `GET /camera/<id>/stream`: MJPEG video stream with real-time AI annotations.
- `GET /camera/<id>/status`: JSON status (mode, risk score, alert count).
- `GET /alerts`: List of all recent high-risk alerts.
- `POST /camera/<id>/upload`: Upload a video file to switch processing to that file.
- `POST /camera/<id>/switch/live`: Switch a camera worker back to live stream (index 0).

#### Implementation Architecture:
- **`app.py`**: Initializes the Flask app and starts the `CameraWorker`.
- **`CameraWorker`**: A background thread that captures frames, runs the AI pipeline, and manages state.
- **`api/routes.py`**: RESTful endpoints to query the `CameraWorker`'s state.

## 🛠️ Calibration & Tuning
- **Warm-up**: The system requires ~8 seconds of video to infer lane directions and baseline motion metrics.
- **Config**: Thresholds, weights, and cropping can be adjusted in `config.yaml`.
- **Alerts**: Triggered alerts are stored in `tmp/alerts_queue.json` along with blurred thumbnails.

## ⚖️ Limitations & Ethics
- **Experimental**: This is a rule-based risk detector, not a definitive tool for accident prediction or intoxication inference.
- **Privacy**: The system automatically generates heavily blurred (64x64) thumbnails for alerts to protect identity.
- **Human-in-the-Loop**: Recommended for verification in any real-world deployment.

## 📊 Performance
- Target FPS: >10 FPS on RTX 3050.
- Resolution: Processed at 1280x720.
