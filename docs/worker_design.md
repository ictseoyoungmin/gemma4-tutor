# Background Worker Design

The worker is intentionally split from the FastAPI process.

## Current responsibilities
- Poll queued jobs from SQLite
- Process placeholder prebuild quiz jobs
- Save ready quiz packs for the frontend dashboard
- Mark job status transitions

## Planned responsibilities
- Agentic quiz prebuild using Pydantic-AI
- Session reflection and long-term memory compression
- Dashboard analytics refresh
- Achievement unlocking
- Curriculum retrieval refresh
