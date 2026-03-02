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

### 4. Launch Dashboard
```bash
streamlit run app/streamlit_app.py
```

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
