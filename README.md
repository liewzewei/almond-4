# Highway Vehicle Hazard Detection AI

Real-time traffic risk monitoring system that transforms vehicle detections into adaptive behavioral intelligence.

## 🌟 Highlights

* Real-time [YOLO](https://github.com/ultralytics/ultralytics)-based vehicle tracking
* Bird’s Eye View (BEV) homography transformation
* Adaptive statistical baseline modeling
* Behavioral risk scoring engine
* Alert snapshot generation
* [Flask](https://flask.palletsprojects.com/)-based deployment (LAN accessible)
* Live + recorded video analysis modes

## ℹ️ Overview

Traditional traffic monitoring is widely **reactive**, providing passive recording long after accidents have occurred rather than generating actionable behavioral intelligence. While standard object detection setups easily identify vehicles, they **do not assess driving behavior**. Hazardous behaviors—such as swerving, unstable steering, and lane drifting—often occur well before a collision. Authorities generally lack the tools to identify these risky vehicles in real-time before situations escalate.

Road accidents are frequently caused by impaired, fatigued, or reckless drivers. Early detection enables **preventive intervention**, transforming roadside monitoring from a reactive enforcement tool to proactive risk mitigation that optimizes emergency response and public safety. The goal is not surveillance — it is **risk mitigation and early warning**.

To achieve this, the system processes live video feeds from roadside cameras using robust vehicle detection and tracking. This raw pixel data undergoes a homography transformation into a normalized Bird’s Eye View (BEV) space to maintain metric integrity. From this BEV environment, the system extracts critical behavioral features such as lateral drift, heading instability, and position variance. These features are continuously fed into an online robust baseline model that evaluates dynamic, vehicle-specific risk scores. An alert is instantly triggered whenever a vehicle's calculated instability exceeds this adaptive threshold.

Unlike simple bounding-box applications, this system analyzes **behavior over time**. By operating in a normalized BEV space rather than raw pixel coordinates, the analytical engine remains camera-position agnostic and evaluates driver stability using statistical modeling rather than fixed thresholds. Risk is actively computed relative to contextual, rolling driving patterns. Ultimately, detection is static; this system is behavioral and temporal.

## 🧠 How It Works

The core system processes information through a streamlined real-time processing pipeline.

```plaintext
Video Frame
   ↓
Vehicle Detection + Tracking
   ↓
Homography → Bird’s Eye View
   ↓
Feature Extraction
   ↓
Adaptive Baseline Modeling
   ↓
Risk Score
   ↓
Alert Trigger
```

* **Vehicle Detection + Tracking:** Leverages object detection models to accurately identify and track vehicles across consecutive frames.
* **Homography → Bird’s Eye View:** Projects the raw camera perspective into a top-down, physically proportionate coordinate space.
* **Feature Extraction:** Calculates kinematic markers such as lateral drift and heading variance within the BEV bounds.
* **Adaptive Baseline Modeling:** Establishes a continuously rolling statistical baseline of "normal" behavior for the measured environment.
* **Risk Score:** Evaluates each vehicle’s extracted features against the established baseline to dynamically quantify anomaly levels.
* **Alert Trigger:** Notifies systems and captures visual alert snapshots when a vehicle's risk diverges from acceptable thresholds.

## 🚀 Usage

### Running the System

```bash
python app.py
```

This starts the central Flask server and automatically begins processing camera feeds. The dashboard is accessible across the LAN at:

```text
http://<local-ip>:5000/camera/1
```

### Uploading a Recording

To analyze arbitrary or pre-recorded video files, navigate to the local web dashboard and use the interface upload controls to submit your video footage for processing.

### Viewing the Model Backend (Streamlit Dashboard)

To observe how the model works under the hood—including real-time BEV transformations, geometry debugging, and tracking metrics—launch the Streamlit dashboard in a separate terminal:

```bash
streamlit run app/streamlit_app.py
```

## ⬇️ Installation

Ensure you are using Python 3.11+.

```bash
git clone <repo>
cd <repo>
pip install -r requirements.txt
```

*(Tested on Windows and standard computing environments)*

## ⚠️ Limitations

* Requires manual homography calibration
* Single-camera demo deployment
* Not production-hardened
* No authentication layer
* Risk model tuned for demonstration scale

## 📌 Future Work

* Multi-camera scaling
* Distributed processing architectures
* Persistent storage and telemetry archival
* Real-world baseline calibration improvements
* Advanced model retraining

## 👤 Team

Developed and maintained by the **enam-tujuh** team.

## � License

This software is provided under standard open-source licensing. Please refer to the repository's included license files for authorized usage boundaries.
