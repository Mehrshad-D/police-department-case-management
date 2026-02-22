# Police Department Case Management System

Full-stack project: **backend** (Django REST Framework) and **frontend** (React + TypeScript + Vite).

## Structure

- **`backend/`** — Django API (port 8000). See [backend/README.md](backend/README.md).
- **`frontend/`** — React SPA (port 3000). See [frontend/README.md](frontend/README.md).

## Quick start

1. **Backend** (terminal 1):

   ```bash
   cd backend
   source venv/bin/activate   # or create: python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_roles
   python manage.py runserver 8000
   ```

2. **Frontend** (terminal 2):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **http://localhost:3000**. The frontend is configured to call the API at **http://localhost:8000/api** in development.

## Notes

- Backend must run on **port 8000** for the default frontend dev config (or set `VITE_API_BASE_URL` in `frontend/.env.development`).
- CORS is enabled for all origins when the backend is in DEBUG mode so the frontend on 3000 can call the backend on 8000.
