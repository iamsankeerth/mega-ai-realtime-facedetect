# Mega AI - Real-Time Face Detection Video Streaming System

## Overview
Containerized backend API that accepts a video feed, detects faces without OpenCV, stores ROIs in PostgreSQL, and streams annotated video to a React frontend.

## Architecture

```
┌─────────────┐      WebSocket/HTTP      ┌─────────────────┐
│   React.js  │ ◄──────────────────────► │   FastAPI App   │
│  Frontend   │   (video stream + ROI)   │   (Python)      │
└─────────────┘                          └────────┬────────┘
                                                  │
                                         ┌────────▼────────┐
                                         │   PostgreSQL    │
                                         │   (store ROIs)  │
                                         └─────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Run Locally
```bash
git clone https://github.com/YOUR_USERNAME/mega-ai-face-detection.git
cd mega-ai-face-detection
docker-compose up --build
```

The app will be available at `http://localhost:3000` (frontend) and `http://localhost:8000` (backend API docs at `/docs`).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload video file for processing |
| GET | `/stream` | Stream processed video with ROI overlay |
| GET | `/roi` | Get ROI data (bounding boxes) per frame |

## Tech Stack
- **Backend**: Python, FastAPI, MediaPipe (face detection), SQLAlchemy, asyncpg
- **Frontend**: React.js, HTML5 Video/WebSocket
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Docker Compose

## AI Collaboration Attestation
AI assistants were used for architectural guidance, debugging, and code review during development.

## License
MIT
