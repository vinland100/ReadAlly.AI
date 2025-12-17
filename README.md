# ReadAlly.AI

ReadAlly.AI: AI-Powered Immersive Reading. Stop searching, start reading. Real-time AI context analysis and instant insights to help you master English reading with ease.
(ReadAlly.AI：AI 驱动的沉浸式阅读。告别频繁查词，专注纯粹阅读。AI 实时语境解析与精炼要点，助您轻松提高英语阅读能力。)

## 项目介绍 (Project Overview)

ReadAlly.AI 是一个旨在通过人工智能技术提升英语阅读体验的平台。它利用先进的 AI 模型实时分析文章语境，提供即时的难点解析和内容摘要，帮助用户专注于阅读本身，克服语言障碍。

## 技术栈 (Tech Stack)

本项目采用前后端分离的架构：

### 前端 (Frontend)
- **框架**: [Next.js](https://nextjs.org/) (React)
- **样式**: [Tailwind CSS](https://tailwindcss.com/)
- **包管理器**: [pnpm](https://pnpm.io/)
- **组件库/工具**: Lucide React, Framer Motion (根据 `package.json`)

### 后端 (Backend)
- **语言**: Python
- **框架**: [FastAPI](https://fastapi.tiangolo.com/)
- **包管理器/环境管理**: [uv](https://github.com/astral-sh/uv)
- **数据库**: SQLite (默认 `readally.db`) / SQLModel
- **AI/LLM 集成**: DashScope (通义千问), LangChain (潜在相关库)

## 开发指南 (Development Guide)

### 环境要求 (Prerequisites)
- [Node.js](https://nodejs.org/) (建议 LTS 版本)
- [Python](https://www.python.org/) (>= 3.12)
- [pnpm](https://pnpm.io/installation)
- [uv](https://github.com/astral-sh/uv)

### 1. 后端开发 (Backend Setup)

后端使用 `uv` 进行极速的依赖管理和环境配置。

```bash
# 进入后端目录
cd backend

# (可选) 创建并激活虚拟环境，或者直接使用 uv run
# uv 会自动处理虚拟环境

# 安装/同步依赖
uv sync

# 启动开发服务器
# 默认端口: 8000
uv run uvicorn main:app --reload
```

后端 API 文档地址 (启动后): `http://localhost:8000/docs`

### 2. 前端开发 (Frontend Setup)

前端使用 `pnpm` 进行依赖管理。

```bash
# 进入前端目录
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
# 默认端口: 3000
pnpm run dev
```

前端访问地址: `http://localhost:3000`

## 目录结构 (Directory Structure)

```
/root/ReadAlly.AI/
├── backend/            # Python FastAPI 后端
│   ├── main.py        # 入口文件
│   ├── pyproject.toml # 依赖配置
│   ├── .venv/         # 虚拟环境 (自动生成)
│   └── ...
├── frontend/           # Next.js 前端
│   ├── src/           # 源代码
│   ├── package.json   # 依赖配置
│   └── ...
└── README.md          # 项目文档
```

## 注意事项 (Notes)

- 确保后端服务启动后再运行前端进行联调，否则 API 请求会失败。
- 首次运行时，后端可能会自动生成 SQLite 数据库文件。
