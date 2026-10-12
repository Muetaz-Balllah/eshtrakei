# Run the system

Eshtrakei needs three processes at the same time: Redis, the API, and the website.

Run the commands from the project root unless a step says otherwise.

## First time only

Install Python, Node.js, and Redis. Redis must listen on `localhost:6379`.

With Docker:

```powershell
docker run --name eshtrakei-redis -p 6379:6379 -d redis
```

Then prepare the API and the site:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend\.env.example backend\.env
```

Open `backend/.env` and set `JWT_SECRET` and `PLATFORM_ADMIN_PASSWORD`.

```powershell
alembic upgrade head
python -m backend.scripts.seed_admin
cd frontend
Copy-Item .env.example .env.local
npm install
```

The platform admin email is `admin@eshtrakei.local`. The password is the value you put in `PLATFORM_ADMIN_PASSWORD`.

## Every time you start

Use a separate terminal for each process.

**1. Redis**, if it is not already running:

```powershell
docker start eshtrakei-redis
```

**2. API:**

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

**3. Website:**

```powershell
cd frontend
npm run dev
```

Open http://localhost:3000.

The API is at http://127.0.0.1:8000. Check it with http://127.0.0.1:8000/api/health. Both `database` and `redis` should be `true`.

Stop a process with Ctrl+C in its terminal.
