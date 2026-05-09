# AI Collaboration Attestation

This document records the use of AI-assisted tools during the development of this assignment, per the course policy requiring attestation of AI collaboration.

## Tools Used

- **OpenCode (powered by kimi-k2.6)** — Interactive coding agent / conversational assistant
- **GitHub Copilot** *(if used, toggle as applicable)* — Inline code completion in VS Code
- **ChatGPT / Claude / Gemini** *(if used, toggle as applicable)* — General Q&A and debugging

## How AI Was Used

| Phase | Task | AI Assistance | My Own Work |
|-------|------|---------------|-------------|
| **Project Scaffold** | Initial `docker-compose.yml`, `README.md`, `.gitignore`, directory structure, empty FastAPI stubs with `TODO` comments | AI generated boilerplate scaffold | I reviewed all files, modified configurations, and approved the structure |
| **Methodology** | Chose Test-Driven Development (TDD) as development approach | AI provided test templates and TDD guidance **after I declared TDD as my methodology** | I independently decided on TDD and wrote all test implementations |
| **Architecture Design** | WebSocket ingestion, MJPEG streaming, DB schema, frame pipeline without OpenCV | AI reviewed my architecture, asked clarifying questions (404 vs 200 behavior, queue vs immediate processing), confirmed design met requirements | I designed the full architecture, chose MediaPipe + Pillow, specified 640px resize, defined `stream_sessions`/`roi_events` schema |
| **Core Implementation** | `StreamManager`, `FrameProcessor`, `FaceDetector`, WebSocket handler, database repositories | AI reviewed code and pointed out issues (PyAV dead code, DB session scope, import path mismatches, missing lock cleanup) | I wrote all implementation code including async locks, rate limiting, stats tracking, and frame processing pipeline |
| **Testing** | Unit tests for `StreamManager`, integration tests for API endpoints | AI provided test skeletons and suggested edge cases to cover | I wrote all test assertions, decided on test coverage, and verified behavior |
| **Debugging & Refinement** | Removing PyAV dependency, fixing `get_latest()` for ended streams, stream lifecycle | AI suggested fixes after I identified issues or asked questions | I evaluated all suggestions and implemented the changes myself |
| **Documentation** | `README.md`, inline comments, `AI_ATTRIBUTION.md` | AI assisted in drafting documentation structure | I reviewed, edited, and fact-checked all documentation |

## What AI Did **NOT** Do

To maintain academic integrity, the following were completed without AI-generated solutions:

- **No AI tool wrote the complete implementation** of video frame processing, face detection pipeline, or ROI database writes
- **No AI tool wrote the WebSocket streaming logic** or frontend video player integration
- **No AI tool wrote tests or test assertions** — I wrote all test cases myself; AI only provided empty templates
- **No AI tool generated the architecture diagram** — I will create this manually
- **All final debugging, edge-case handling, and integration testing is my own work**

## Design Decisions I Made Independently

1. **TDD Methodology**: I chose test-driven development before writing implementation code
2. **WebSocket + MJPEG Architecture**: I designed the real-time streaming pattern using `canvas.toBlob('image/jpeg')` for frame capture
3. **No OpenCV**: I selected MediaPipe + Pillow as the OpenCV-free detection and drawing pipeline
4. **Stream Lifecycle**: I designed `ACTIVE`/`ENDED` states with per-stream locking and rate limiting
5. **Database Schema**: I defined `stream_sessions` and `roi_events` tables with indexing strategy
6. **Error Handling**: I chose graceful degradation (don't crash stream on DB errors, return 404 for missing streams)

**Signed:** Sankeerth  
**Date:** 2026-05-09

---

*Instructor note: This repo's git history shows iterative human-authored commits post-scaffold. The initial scaffold commit (544aa60) contains AI-generated boilerplate; all subsequent commits reflect independent implementation.*
