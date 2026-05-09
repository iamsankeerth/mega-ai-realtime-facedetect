import React, { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

/* ─── Camera Icon SVG ─── */
function CameraIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  )
}

/* ─── Face Icon SVG ─── */
function FaceIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <circle cx="9" cy="10" r="1" fill="currentColor" stroke="none" />
      <circle cx="15" cy="10" r="1" fill="currentColor" stroke="none" />
      <path d="M9 15c.5 1.5 1.8 2.5 3 2.5s2.5-1 3-2.5" />
    </svg>
  )
}

function App() {
  /* ─── Form State ─── */
  const streamId = 'demo-stream'
  const apiKey = 'demo-key-change-me'

  /* ─── Connection State ─── */
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [streamActive, setStreamActive] = useState(false)
  const [framesReady, setFramesReady] = useState(false)

  /* ─── Data State ─── */
  const [roi, setRoi] = useState(null)
  const [roiHistory, setRoiHistory] = useState([])

  /* ─── Metrics State ─── */
  const [fps, setFps] = useState(0)
  const [latency, setLatency] = useState(0)
  const [sessionDuration, setSessionDuration] = useState(0)
  const [totalFrames, setTotalFrames] = useState(0)
  const [detectedFrames, setDetectedFrames] = useState(0)
  const [droppedFrames, setDroppedFrames] = useState(0)

  /* ─── Refs ─── */
  const ws = useRef(null)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const roiPollRef = useRef(null)
  const frameIntervalRef = useRef(null)
  const sessionStartRef = useRef(null)
  const ackTimestampsRef = useRef([])
  const latencyWindowRef = useRef([])
  const sendTimestampRef = useRef(0)

  /* ─── Health Check ─── */
  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then(r => r.ok ? setStatus('backend-ready') : setStatus('backend-error'))
      .catch(() => setStatus('backend-error'))
  }, [])

  /* ─── Session Duration Timer ─── */
  useEffect(() => {
    if (!streamActive) {
      setSessionDuration(0)
      return
    }
    sessionStartRef.current = Date.now()
    const interval = setInterval(() => {
      setSessionDuration(Math.floor((Date.now() - sessionStartRef.current) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [streamActive])

  /* ─── Cleanup ─── */
  const cleanup = useCallback(() => {
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
    if (roiPollRef.current) {
      clearInterval(roiPollRef.current)
      roiPollRef.current = null
    }
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current)
      frameIntervalRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
  }, [])

  /* ─── Synthetic Frame ─── */
  const sendSyntheticFrame = useCallback((socket) => {
    const canvas = document.createElement('canvas')
    canvas.width = 640
    canvas.height = 480
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = `hsl(${Math.random() * 360}, 60%, 70%)`
    ctx.fillRect(0, 0, 640, 480)
    ctx.fillStyle = '#f0c0a0'
    ctx.fillRect(220, 140, 200, 200)
    canvas.toBlob(blob => {
      if (blob && socket.readyState === WebSocket.OPEN) {
        sendTimestampRef.current = Date.now()
        socket.send(blob)
      }
    }, 'image/jpeg')
  }, [])

  /* ─── Start Stream ─── */
  const startStream = useCallback(async () => {
    cleanup()

    /* Reset state */
    setError(null)
    setRoi(null)
    setRoiHistory([])
    setFramesReady(false)
    setStreamActive(true)
    setFps(0)
    setLatency(0)
    setTotalFrames(0)
    setDetectedFrames(0)
    setDroppedFrames(0)
    ackTimestampsRef.current = []
    latencyWindowRef.current = []

    const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/streams/${streamId}/ingest?api_key=${apiKey}`
    const socket = new WebSocket(wsUrl)
    ws.current = socket

    socket.onopen = () => {
      setStatus('connected')
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setFramesReady(true)

        /* Update frame counters */
        setTotalFrames(prev => prev + 1)
        if (data.detected) setDetectedFrames(prev => prev + 1)
        if (data.dropped) setDroppedFrames(prev => prev + 1)

        /* Update ROI in real-time from WebSocket ack */
        if (data.detected && data.roi) {
          setRoi(data.roi)
        } else {
          setRoi(null)
        }

        /* FPS calculation */
        ackTimestampsRef.current.push(Date.now())
        if (ackTimestampsRef.current.length > 10) {
          ackTimestampsRef.current.shift()
        }
        if (ackTimestampsRef.current.length >= 2) {
          const span = ackTimestampsRef.current[ackTimestampsRef.current.length - 1] - ackTimestampsRef.current[0]
          if (span > 0) {
            setFps(Number(((ackTimestampsRef.current.length - 1) / span * 1000).toFixed(1)))
          }
        }

        /* Latency calculation */
        if (sendTimestampRef.current > 0) {
          const lat = Date.now() - sendTimestampRef.current
          latencyWindowRef.current.push(lat)
          if (latencyWindowRef.current.length > 5) latencyWindowRef.current.shift()
          const avgLat = latencyWindowRef.current.reduce((a, b) => a + b, 0) / latencyWindowRef.current.length
          setLatency(Math.round(avgLat))
        }

        /* Status */
        if (data.detected) {
          setStatus('detecting')
        } else if (data.dropped) {
          setStatus('no-face')
        } else {
          setStatus('connected')
        }
      } catch {
        // binary frames not expected here
      }
    }

    socket.onerror = () => {
      setStatus('error')
      setError('WebSocket error — check API key')
      setStreamActive(false)
      setFramesReady(false)
    }

    socket.onclose = () => {
      setStatus('disconnected')
      setStreamActive(false)
      setFramesReady(false)
    }

    /* ROI Polling — updates history only; live ROI comes from WebSocket */
    roiPollRef.current = setInterval(() => {
      fetch(`${BACKEND_URL}/streams/${streamId}/rois?limit=10`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data && data.events.length > 0) {
            setRoiHistory(data.events)
          }
        })
        .catch(() => {})
    }, 500)

    /* Frame Capture — always try webcam first */
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      })
      streamRef.current = mediaStream
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        await videoRef.current.play()
      }

      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')

      frameIntervalRef.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN && videoRef.current) {
          ctx.drawImage(videoRef.current, 0, 0, 640, 480)
          canvas.toBlob(blob => {
            if (blob && socket.readyState === WebSocket.OPEN) {
              sendTimestampRef.current = Date.now()
              socket.send(blob)
            }
          }, 'image/jpeg', 0.85)
        }
      }, 200)
    } catch (err) {
      console.warn('Camera access failed, falling back to synthetic frames:', err)
      setError('Camera access denied — using synthetic test pattern')
      frameIntervalRef.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          sendSyntheticFrame(socket)
        }
      }, 200)
    }
  }, [streamId, apiKey, cleanup, sendSyntheticFrame])

  /* ─── Stop Stream ─── */
  const stopStream = useCallback(() => {
    cleanup()
    setStatus('stopped')
    setRoi(null)
    setFramesReady(false)
    setStreamActive(false)
    setFps(0)
    setLatency(0)
  }, [cleanup])

  /* ─── Derived Values ─── */
  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0')
    const s = (seconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const mjpegUrl = `${BACKEND_URL}/streams/${streamId}/video`

  /* ─── Render ─── */
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <FaceIcon className="header-icon" />
          <h1 className="header-title">Mega AI — Face Detection</h1>
        </div>
        <div className="header-status">
          <span className={`status-dot ${status}`} />
          <span>{status.replace(/-/g, ' ')}</span>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">{error}</div>
      )}

      {/* Dashboard */}
      <div className="dashboard">
        {/* Left: Video Panel */}
        <div className="video-panel">
          <div className="video-card">
            <div className="video-header">
              <span className="video-header-label">Live Feed</span>
            </div>
            <div className="video-container">
              {streamActive && framesReady ? (
                <img
                  key={streamId}
                  src={mjpegUrl}
                  alt="Video stream"
                  className="video-feed"
                  onError={() => setStatus('stream-error')}
                />
              ) : (
                <div className="video-placeholder">
                  <CameraIcon className="placeholder-icon" />
                  <p className="placeholder-text">
                    {streamActive
                      ? 'Waiting for first frame...'
                      : 'Click "Start Stream" to begin face detection'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Controls below video */}
          <div className="video-controls">
            <button
              className="btn"
              onClick={startStream}
              disabled={streamActive}
            >
              Start Stream
            </button>
            <button
              className="btn btn-danger"
              onClick={stopStream}
              disabled={!streamActive}
            >
              Stop Stream
            </button>
          </div>
        </div>

        {/* Right: Metrics Panel */}
        <div className="metrics-panel">
          {/* Live Metrics */}
          <div className="card">
            <div className="card-title">Live Metrics</div>
            <div className="metrics-row">
              <div className="metric-item">
                <div className="metric-value">{fps.toFixed(1)}</div>
                <div className="metric-label">FPS</div>
              </div>
              <div className="metric-item">
                <div className="metric-value">{latency}</div>
                <div className="metric-label">ms</div>
              </div>
              <div className="metric-item">
                <div className="metric-value">{formatDuration(sessionDuration)}</div>
                <div className="metric-label">Duration</div>
              </div>
            </div>
          </div>

          {/* Session Stats */}
          <div className="card">
            <div className="card-title">Session Stats</div>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{totalFrames}</div>
                <div className="stat-label">Total Frames</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{detectedFrames}</div>
                <div className="stat-label">Detected</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{droppedFrames}</div>
                <div className="stat-label">Dropped</div>
              </div>
            </div>

          </div>

          {/* Current ROI — Real-time values from WebSocket */}
          <div className="card">
            <div className="card-title">Current ROI</div>
            {roi ? (
              <div className="roi-code">
                x:{roi.x.toFixed(1)}<br />
                y:{roi.y.toFixed(1)}<br />
                w:{roi.w.toFixed(1)}<br />
                h:{roi.h.toFixed(1)}<br />
                conf:{roi.confidence.toFixed(3)}
              </div>
            ) : (
              <div className="roi-code" style={{ color: 'var(--text-secondary)' }}>
                No face detected
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Hidden elements for webcam capture */}
      <video ref={videoRef} style={{ display: 'none' }} playsInline muted />
      <canvas ref={canvasRef} width={640} height={480} style={{ display: 'none' }} />
    </div>
  )
}

export default App
