import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import yaml
import numpy as np
import time
from core.video_processor import VideoProcessor
from core.tracker import Tracker
from core.alert_writer import AlertWriter

st.set_page_config(page_title="Highway Hazard Detection AI", layout="wide")

def load_config():
    with open("config.yaml", 'r') as f:
        return yaml.safe_load(f)

def main():
    st.title("🛣️ Highway vehicle Hazard Detection AI")
    st.sidebar.header("Settings")
    
    config = load_config()
    
    video_path = st.sidebar.text_input("Video Path", "./data/sample_highway.mov")
    start_btn = st.sidebar.button("🚀 Start Pipeline")
    
    # Advanced Settings
    with st.sidebar.expander("Advanced Settings"):
        alert_thresh = st.slider("Alert Risk Threshold", 0.1, 1.0, float(config.get('alert_risk_threshold', 0.85)))
        config['alert_risk_threshold'] = alert_thresh
    
    if start_btn:
        if not os.path.exists(video_path):
            st.error(f"File not found: {video_path}")
            return
            
        # Initialize components
        from core.engine import RiskEngine
        vp = VideoProcessor(video_path)
        tracker = Tracker(config['yolo_model'], config['tracker_type'], config['yolo_conf_threshold'])
        config['fps'] = vp.fps
        engine = RiskEngine(config)
        aw = AlertWriter(config['alert_queue_path'], config['camera_id'])
        
        # Layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Perspective View")
            frame_placeholder = st.empty()
            st.subheader("Bird's Eye View (BEV)")
            bev_placeholder = st.empty()
            
        with col2:
            st.subheader("Live Metrics")
            metrics_placeholder = st.empty()
            st.subheader("Probabilistic Risks")
            probs_placeholder = st.empty()
            st.subheader("Recent Alerts")
            alert_placeholder = st.empty()
            
        frame_idx = 0
        all_alerts = []
        
        try:
            while True:
                raw_frame = vp.get_frame()
                if raw_frame is None:
                    break
                    
                timestamp = frame_idx / vp.fps
                
                # 1. Pipeline execution
                tracks = tracker.track(raw_frame)
                results = engine.process_frame(raw_frame, tracks, frame_idx, timestamp)
                
                # 2. Visualization
                annotated = raw_frame.copy()
                bev_img = np.zeros((engine.homography_estimator.bev_height, engine.homography_estimator.bev_width, 3), dtype=np.uint8)
                
                for res in results:
                    tid = res['track_id']
                    bbox = res['bbox']
                    risk_score = res['risk_score']
                    is_alert = res['is_alert']
                    
                    color = (0, 0, 255) if is_alert else (0, 255, 0)
                    
                    # Draw on perspective
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated, f"ID:{tid} P:{risk_score:.2f}", (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    # Draw on BEV
                    traj = engine.trajectory_manager.get_trajectory(tid)
                    if traj:
                        last_pt = traj[-1]
                        bx, by = int(last_pt['bev_x']), int(last_pt['bev_y'])
                        if 0 <= bx < engine.homography_estimator.bev_width and 0 <= by < engine.homography_estimator.bev_height:
                            cv2.circle(bev_img, (bx, by), 15, color, -1)
                            cv2.putText(bev_img, f"{tid}", (bx+20, by), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
                    
                    if is_alert:
                        all_alerts.insert(0, {"tid": tid, "risk": risk_score, "time": timestamp})

                # Update UI elements
                img_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(img_rgb, channels="RGB", use_container_width=True)
                
                # Resize BEV for display
                bev_display = cv2.resize(bev_img, (0, 0), fx=0.4, fy=0.4)
                bev_placeholder.image(bev_display, caption="Road Transformation", use_container_width=False)
                
                with metrics_placeholder.container():
                    st.metric("Processed Frames", frame_idx)
                    st.metric("Active Tracks", len(tracks))
                    h_conf = engine.homography_estimator.confidence_score
                    st.write(f"Homography Confidence: {h_conf:.2f}")
                    
                with probs_placeholder.container():
                    if results:
                        top_res = sorted(results, key=lambda x: x['risk_score'], reverse=True)[0]
                        st.write(f"Track {top_res['track_id']} Breakdown:")
                        for f_name, p_val in top_res['probabilities'].items():
                            st.progress(p_val, text=f"{f_name}: {p_val:.2f}")
                            
                with alert_placeholder.container():
                    for a in all_alerts[:5]:
                        st.error(f"⚠️ HIGH RISK: ID {a['tid']} (R={a['risk']:.2f})")
                        
                frame_idx += 1
                
        finally:
            vp.release()

if __name__ == "__main__":
    main()
