# KeeperKit

KeeperKit is a local-first TRPG assistant project. The first module, KeeperKit Rules, is a rulebook RAG service for Keepers and GMs.

## Current Scope

- Import Markdown or TXT rule notes from `backend/data/raw`.
- Split documents into searchable chunks with metadata.
- Build a lightweight local index for development.
- Ask rule questions through FastAPI.
- Show a small React chat interface.

## Project Layout

```text
keeperkit/
├── backend/              # FastAPI + RAG service
├── frontend/             # Vite + React chat UI
└── docs/                 # Project design and development docs
```

## Backend Quick Start

```powershell
cd keeperkit
.\keeperkit.ps1 backend
```

Then open:

```text
http://127.0.0.1:8000/docs
```

For development reload:

```powershell
.\keeperkit.ps1 backend -Reload
```

The backend launcher uses the local `keeperkit` conda environment and cached Hugging Face models by default.

## Frontend Quick Start

```powershell
cd keeperkit\frontend
npm install
npm run dev
```

The frontend expects the backend at:

```text
http://127.0.0.1:8000
```

## Development Guide

Read `docs/development_guide.md` first. It explains the V1 architecture, module boundaries, data flow, and next implementation milestones.
