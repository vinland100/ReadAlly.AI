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

## 🚀 Deployment & Usage

We provide three ways to run ReadAlly.AI, depending on your needs.

### 1. Production / One-Click Deployment (Recommended)
**Use Case:** Running the app on a server or locally for usage (not development). Uses pre-built optimized images.

1.  **Prereqs**: Install Docker and Docker Compose.
2.  **Setup**:
    ```bash
    cd docker
    cp .env.example .env
    # Edit .env: Set DASHSCOPE_API_KEY and SECRET_KEY
    ```
3.  **Run**:
    ```bash
    docker compose up -d
    ```
4.  **Access**:
    -   Frontend: `http://localhost:3000`
    -   Data (DB & Audio) is persisted in `./docker/data/`.

### 2. Local Development (Standard)
**Use Case:** Writing code, debugging, and contributing.

#### Backend
```bash
cd backend
cp .env.example .env  # Configure API keys
uv sync               # Install dependencies
uv run uvicorn main:app --reload
```
*Database will be created at `backend/readally.db`.*

#### Frontend
```bash
cd frontend
cp .env.example .env
pnpm install
pnpm run dev
```
*Access at `http://localhost:3000`.*

### 3. Docker Development (Build from Source)
**Use Case:** Verifying that your changes build correctly in Docker before pushing.

```bash
cd docker
# Uses docker-compose.dev.yaml which includes 'build' contexts
docker compose -f docker-compose.dev.yaml up --build
```

---

## 📂 Configuration Guide

| Scenario | Config File | Database Location | Important Notes |
| :--- | :--- | :--- | :--- |
| **Production** | `docker/docker-compose.yaml` | `./docker/data/readally.db` | Uses `ghcr.io` images. No build required. |
| **Local Dev** | `backend/.env` | `backend/readally.db` | Manual start. Best for coding. |
| **Docker Dev** | `docker/docker-compose.dev.yaml` | `./docker/data/readally.db` | Builds from local source. Slower start. |

### Environment Variables
Check the `.env.example` files in each directory for detailed comments on required variables.
- `docker/.env.example`: For Docker Compose setups.
- `backend/.env.example`: For manual backend execution.
- `frontend/.env.example`: For manual frontend execution.

---

## Tech Stack

### Frontend
- **Framework**: [Next.js](https://nextjs.org/) (React)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Package Manager**: [pnpm](https://pnpm.io/)
- **UI/Tools**: Lucide React, Framer Motion

### Backend
- **Language**: Python
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Environment Management**: [uv](https://github.com/astral-sh/uv)
- **Database**: SQLite / SQLModel
- **AI/LLM Integration**: DashScope (Qwen), LangChain

## Directory Structure
```
/root/ReadAlly.AI/
├── backend/            # Python FastAPI Backend
├── frontend/           # Next.js Frontend
├── docker/             # Docker Configuration (Compose files)
└── .github/            # CI/CD Workflows
```
