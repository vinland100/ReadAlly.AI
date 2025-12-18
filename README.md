# ReadAlly.AI

ReadAlly.AI: AI-Powered Immersive Reading. Stop searching, start reading. Real-time AI context analysis and instant insights to help you master English reading with ease.

## Project Overview

ReadAlly.AI is a platform designed to enhance the English reading experience using artificial intelligence. It leverages advanced AI models to analyze article context in real-time, providing instant difficulty analysis and learning aids, helping users focus on reading itself and overcome language barriers.

## Tech Stack

This project uses a separate frontend and backend architecture:

### Frontend
- **Framework**: [Next.js](https://nextjs.org/) (React)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Package Manager**: [pnpm](https://pnpm.io/)
- **UI/Tools**: Lucide React, Framer Motion

### Backend
- **Language**: Python
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Environment Management**: [uv](https://github.com/astral-sh/uv)
- **Database**: SQLite (default `readally.db`) / SQLModel
- **AI/LLM Integration**: DashScope (Qwen), LangChain

## Development Guide

### Prerequisites
- [Node.js](https://nodejs.org/) (LTS recommended)
- [Python](https://www.python.org/) (>= 3.12)
- [pnpm](https://pnpm.io/installation)
- [uv](https://github.com/astral-sh/uv)

### 1. Backend Setup

The backend uses `uv` for ultra-fast dependency management.

```bash
# Enter backend directory
cd backend

# (Optional) Create and activate venv, or simply use uv run
# uv handles virtual environments automatically

# Install/Sync dependencies
uv sync

# Start development server
# Default port: 8000
uv run uvicorn main:app --reload
```

Backend API Documentation (after start): `http://localhost:8000/docs`

### 2. Frontend Setup

The frontend uses `pnpm` for dependency management.

```bash
# Enter frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
# Default port: 3000
pnpm run dev
```

Frontend URL: `http://localhost:3000`

## Directory Structure

```
/root/ReadAlly.AI/
├── backend/            # Python FastAPI Backend
│   ├── main.py        # Entry point
│   ├── pyproject.toml # Dependencies
│   ├── .venv/         # Virtual Environment (Auto-generated)
│   └── ...
├── frontend/           # Next.js Frontend
│   ├── src/           # Source code
│   ├── package.json   # Dependencies
│   └── ...
└── README.md          # Project Documentation
```

## Notes

- Ensure the backend service is running before starting the frontend to avoid API errors.
- On the first run, the backend will automatically generate the SQLite database file.
