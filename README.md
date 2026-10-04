# Eshtrakei

An internet subscription marketplace: one client account, many internet companies, one manager per company, and one platform admin.

The website UI is Arabic and right-to-left. This repository contains the frontend and the backend together.

| Part | Stack | Folder |
| --- | --- | --- |
| Frontend | Next.js 16, React 19, Tailwind CSS 4 | `frontend/` |
| Backend | FastAPI, SQLAlchemy, Alembic | `backend/` |
| Development database | SQLite | Created locally and not committed |
| Sessions | Redis | Required while the API is running |
| Design drafts | HTML | `UI/` |

## Local setup

Run these commands from the project root, except when the steps enter `frontend`.

### 1. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` and set `JWT_SECRET` and `PLATFORM_ADMIN_PASSWORD`. Then:

```powershell
alembic upgrade head
python -m backend.scripts.seed_admin
uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Health check: `GET /api/health`.

Redis must be available at `redis://localhost:6379/0`.

### 2. Frontend

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

The site runs at `http://localhost:3000` and proxies `/api` requests to the backend.

## Tests

```powershell
pytest backend/tests
```

From the frontend folder:

```powershell
npm run lint
```

## What stays local

`.env` files, the virtual environment, `node_modules`, `dev.db`, and uploaded files stay on your machine. The safe templates are `backend/.env.example` and `frontend/.env.example`.
