import { useState, useEffect } from 'react';
import SingaporeMap from './components/SingaporeMap';
import DemoModal from './components/DemoModal';
import VideoViewer from './components/VideoViewer';
import { scenarioB } from './data/demoScenarios';
import './App.css';

function App() {
  // Flow states: IDLE -> MODAL_OPEN -> WAITING_A -> SCENARIO_A -> VIEWING_A -> WAITING_B -> SCENARIO_B -> VIEWING_B
  const [demoState, setDemoState] = useState('IDLE');
  const [videoTitle, setVideoTitle] = useState('');
  const [eventSourceUrl, setEventSourceUrl] = useState(null);
  const [visibleDots, setVisibleDots] = useState(0);

  // Scenario A timeout
  useEffect(() => {
    if (demoState === 'WAITING_A') {
      const timer = setTimeout(() => {
        setDemoState('SCENARIO_A');
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [demoState]);

  // Scenario B timeout
  useEffect(() => {
    if (demoState === 'WAITING_B') {
      const timer = setTimeout(() => {
        setDemoState('SCENARIO_B');
        setVisibleDots(1);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [demoState]);

  // Scenario B dot interval
  useEffect(() => {
    if (demoState === 'SCENARIO_B' || demoState === 'VIEWING_B') {
      const interval = setInterval(() => {
        setVisibleDots(prev => {
          if (prev >= scenarioB.points.length) {
            clearInterval(interval);
            return prev;
          }
          return prev + 1;
        });
      }, 700); // adjusted speed for the longer cross-country route
      return () => clearInterval(interval);
    }
  }, [demoState]);

  const handleModalClose = () => {
    if (demoState === 'MODAL_OPEN') {
      setDemoState('WAITING_A');
    }
  };

  const handleRunDetection = async (file) => {
    setVideoTitle('Custom Upload Processing');
    setEventSourceUrl(null);
    setDemoState('VIEWING_CUSTOM');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setEventSourceUrl(`/api/process/${data.video_id}`);
    } catch (err) {
      console.error(err);
      alert('Failed to start processing');
    }
  };

  const handleViewClick = async (title, scenarioType) => {
    setVideoTitle(title);
    setEventSourceUrl(null); // No stream for mock

    if (scenarioType === 'A') {
      setDemoState('VIEWING_A');
      await triggerVideoProcessing(scenarioA.videoPath);
    } else if (scenarioType === 'B') {
      setDemoState('VIEWING_B');
      await triggerVideoProcessing(scenarioB.videoPath);
    }
  };

  const triggerVideoProcessing = async (videoPath) => {
    try {
      // 1. Fetch the local video file as a Blob
      const response = await fetch(videoPath);
      if (!response.ok) {
        console.warn("No pre-recorded video found at " + videoPath + " yet.");
        return;
      }
      const blob = await response.blob();

      // 2. Create a file from the blob to upload to FastAPI
      const file = new File([blob], "demo.mp4", { type: "video/mp4" });

      // 3. Re-use the existing detection logic
      const formData = new FormData();
      formData.append('file', file);

      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadRes.ok) throw new Error('Upload failed');

      const data = await uploadRes.json();
      setEventSourceUrl(`/api/process/${data.video_id}`);
    } catch (err) {
      console.error("Error processing pre-recorded video:", err);
    }
  };

  const handleViewerClose = () => {
    if (demoState === 'VIEWING_A') {
      // Go to WAITING_B immediately to clear the map, the MapController handles the zoom out
      setDemoState('WAITING_B');
    } else if (demoState === 'VIEWING_B') {
      setDemoState('IDLE');
      setVisibleDots(0);
    } else if (demoState === 'VIEWING_CUSTOM') {
      setDemoState('WAITING_A');
    }
  };

  // When we go to WAITING_B, we clear the map of Scenario A's dot and popup
  const currentScenario =
    demoState === 'SCENARIO_A' || demoState === 'VIEWING_A' ? 'A' :
      demoState === 'SCENARIO_B' || demoState === 'VIEWING_B' ? 'B' :
        null;

  const isViewerOpen = demoState === 'VIEWING_A' || demoState === 'VIEWING_B' || demoState === 'VIEWING_CUSTOM';

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>SPF Hazard Detection Dashboard</h1>
      </header>

      <main className="map-container">
        <SingaporeMap
          scenario={currentScenario}
          visibleDots={visibleDots}
          onViewClick={handleViewClick}
          isViewerOpen={isViewerOpen}
        />
      </main>

      <div className="floating-controls">
        <button className="btn-primary" onClick={() => setDemoState('MODAL_OPEN')}>
          Model Demo
        </button>
      </div>

      <DemoModal
        isOpen={demoState === 'MODAL_OPEN'}
        onClose={handleModalClose}
        onRunDetection={handleRunDetection}
      />

      <VideoViewer
        isOpen={isViewerOpen}
        title={videoTitle}
        onClose={handleViewerClose}
        eventSourceUrl={eventSourceUrl}
      />
    </div>
  );
}

export default App;