# AI Collaboration Attestation

This document records the use of AI-assisted tools during the development of this assignment, per the course policy requiring attestation of AI collaboration.

## Tools Used

- **OpenCode (powered by kimi-k2.6)** — Interactive coding agent / conversational assistant
- **GitHub Copilot** *(if used, toggle as applicable)* — Inline code completion in VS Code
- **ChatGPT / Claude / Gemini** *(if used, toggle as applicable)* — General Q&A and debugging

## How AI Was Used

| Phase | Task | AI Assistance | My Own Work |
|-------|------|---------------|-------------|
| **Architecture & Planning** | Designing system layout (FastAPI + React + PostgreSQL + Docker), choosing MediaPipe over OpenCV | AI suggested architecture patterns, endpoint design, and DB schema ideas | I reviewed, modified, and approved all architectural decisions; I chose the specific libraries and data flow |
| **Project Scaffolding** | Initial file/directory structure, `docker-compose.yml`, Dockerfiles, `.gitignore`, `README.md` | AI generated boilerplate scaffolding files | I reviewed every file, made edits, and customized configurations to fit the assignment requirements |
| **Code Templates** | FastAPI endpoint stubs, SQLAlchemy models, React component skeleton | AI wrote starter code with `TODO` comments marking unimplemented logic | I am responsible for implementing all business logic, frame processing, streaming, and ROI storage |
| **Face Detection Research** | Finding OpenCV-free face detection alternatives | AI explained MediaPipe, Pillow, and ONNX-based options | I evaluated trade-offs and selected MediaPipe + Pillow as the implementation path |
| **Debugging & Review** | *(planned / ongoing)* Fixing bugs, reviewing edge cases, interpreting error messages | AI will act as a teaching assistant — asking clarifying questions, suggesting debugging steps, reviewing my code | I write all fixes and tests myself; AI does not write complete solutions |
| **Documentation** | `README.md`, inline code comments, this `AI_ATTRIBUTION.md` file | AI assisted in drafting documentation and explaining design decisions | I reviewed, fact-checked, and edited all documentation for accuracy |

## What AI Did **NOT** Do

To maintain academic integrity and ensure I actually learn from this assignment, the following were completed **without** AI-generated solutions:

- No AI tool wrote the complete implementation of video frame extraction, face detection pipeline, or ROI database writes
- No AI tool wrote the WebSocket streaming logic or the frontend video player integration
- No AI tool wrote tests or test cases
- No AI tool generated the architecture diagram image (I will create this manually using a diagramming tool)
- All final debugging, edge-case handling, and integration testing is my own work

## Verification

If asked to explain any part of this codebase, I can walk through:

1. Why MediaPipe was chosen and how its bounding-box coordinates are mapped to pixel values
2. How the async SQLAlchemy session lifecycle works in FastAPI dependency injection
3. The frame-by-frame data flow from upload → detection → DB storage → API response
4. The Docker networking and service dependency model in `docker-compose.yml`

## Statement

I attest that this document accurately reflects the scope of AI assistance used in this project. All core logic, integration work, testing, and final verification is my own.

**Signed:** Sankeerth  
**Date:** 2026-05-09

---

*Instructor note: This repo's commit history and `git log` can be cross-referenced with this attestation to verify that implementation commits (post-scaffold) reflect iterative human-authored development.*
