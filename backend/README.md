# DiscoveryHub Backend (FastAPI)

## Setup

Requires Python 3.14 (the project's version).

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Layout

```
backend/
├── app/
│   ├── __init__.py
│   └── main.py        # FastAPI app, CORS, routes
├── requirements.txt   # pinned dependencies
└── .gitignore
```

Add new routes in `app/` (for example `app/routers/`) and include them in `app/main.py`.

## Adding dependencies

```powershell
pip install <package>
pip freeze | findstr /i "^<package>=="   # copy the pinned line into requirements.txt
```

Keep `requirements.txt` limited to the packages you import directly, with exact versions.
