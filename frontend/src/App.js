import React, { useEffect, useRef, useState } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [roiData, setRoiData] = useState([]);
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    // TODO: open WebSocket to /ws/stream and display frames
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    setStatus('uploaded: ' + data.filename);
  };

  const fetchROI = async () => {
    const res = await fetch(`${API_BASE}/roi`);
    const data = await res.json();
    setRoiData(data);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Mega AI Face Detection</h1>
      <input type="file" accept="video/*" onChange={handleUpload} />
      <p>Status: {status}</p>
      <button onClick={fetchROI}>Fetch ROI Data</button>
      <pre>{JSON.stringify(roiData, null, 2)}</pre>
      <video ref={videoRef} controls style={{ maxWidth: '100%' }} />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}

export default App;
