import { useEffect, useState } from 'react';
import './VideoViewer.css';

export default function VideoViewer({ isOpen, title, onClose, eventSourceUrl }) {
  const [status, setStatus] = useState('Idle');
  const [annotatedFrame, setAnnotatedFrame] = useState(null);

  useEffect(() => {
    let eventSource = null;
    if (isOpen && eventSourceUrl) {
      setStatus('Processing...');
      setAnnotatedFrame(null);

      eventSource = new EventSource(eventSourceUrl);

      eventSource.onmessage = (event) => {
        const result = JSON.parse(event.data);
        if (result.status === 'completed') {
          setStatus('Completed');
          eventSource.close();
          return;
        }

        if (result.annotated_frame) {
          setAnnotatedFrame("data:image/jpeg;base64," + result.annotated_frame);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE Error:', err);
        setStatus('Error or connection closed.');
        eventSource.close();
      };
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [isOpen, eventSourceUrl]);

  return (
    <div className={`demo-panel ${isOpen ? 'open' : ''}`}>
      <div className="demo-panel-header">
        <h3>Live Detection Feed</h3>
      </div>
      <div className="demo-panel-content">
        <div className="panel-title" style={{ 
          marginBottom: '16px', 
          fontWeight: '600', 
          color: '#c41e3a', 
          fontSize: '0.9rem', 
          textTransform: 'uppercase', 
          letterSpacing: '1px' 
        }}>{title}</div>
        
        <div className="video-container" style={{ maxHeight: 'calc(100vh - 400px)' }}>
          {annotatedFrame ? (
            <img src={annotatedFrame} alt="Annotated frame" />
          ) : (
            <div className="placeholder-text">Waiting for feed...</div>
          )}
        </div>

        <div className="metrics-container" style={{ flexShrink: 0 }}>
          <p>Status: <span>{status}</span></p>
        </div>
      </div>
      <div className="demo-panel-footer">
        <button className="btn-dismiss" onClick={onClose}>Dismiss Alert</button>
      </div>
    </div>
  );
}