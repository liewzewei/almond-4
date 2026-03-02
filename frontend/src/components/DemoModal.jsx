import { useState, useRef } from 'react';
import './DemoModal.css'; // Add a basic css for modal

export default function DemoModal({ isOpen, onClose, onRunDetection }) {
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!file) {
      alert("Please select an MP4 file.");
      return;
    }
    onRunDetection(file);
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Upload Demo Video</h2>
        <input 
          type="file" 
          accept="video/mp4,video/quicktime,video/x-msvideo"
          onChange={(e) => setFile(e.target.files[0])}
          ref={fileInputRef}
          style={{ marginBottom: '20px', display: 'block' }}
        />
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleRun}>Run Detection</button>
        </div>
      </div>
    </div>
  );
}