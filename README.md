# DiscoveryHub

Monorepo with a Next.js frontend and a FastAPI backend.

```
DiscoveryHub/
├── backend/     # FastAPI API (see backend/README.md)
├── frontend/    # Next.js app (see frontend/README.md)
│   └── docs/    # design-system.md: the UI token reference
└── .claude/     # Claude Code skills (UI work follows the design system)
```

## Getting started

**Backend** (Python 3.14)

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs
```

**Frontend** (Node.js)

```powershell
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

The backend allows CORS from `http://localhost:3000`.

## UI guidelines

All UI work uses the C5i design system tokens in [frontend/docs/design-system.md](frontend/docs/design-system.md). Do not hard-code colors, type sizes, spacing or radius values.
