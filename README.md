# Police Department Case Management System

Full-stack project: **backend** (Django REST Framework) and **frontend** (React + TypeScript + Vite) for digitized police operations — cases, complaints, evidence, suspects, interrogations, captain/chief decisions, trials & verdicts, tips & rewards, and payments.

## Structure

- **`backend/`** — Django REST API (port 8000). See [backend/README.md](backend/README.md).
- **`frontend/`** — React SPA (port 3000). See [frontend/README.md](frontend/README.md).
- **`SCENARIO.md`** — Step-by-step testing scenario (complaints, cases, evidence, suspects, reports, trials).

## Quick start

1. **Backend** (terminal 1):

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_roles
   python manage.py createsuperuser
   python manage.py assign_superuser_as_admin
   python manage.py runserver 8000
   ```

   Or use the run script: `./run.sh` (from the backend directory).
   ```

2. **Frontend** (terminal 2):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **http://localhost:3000**. The frontend calls the API at **http://localhost:8000/api** in development.

4. **First login:** Log in with your superuser. If you see “No roles assigned”, run in the backend:
   ```bash
   ./venv/bin/python manage.py assign_superuser_as_admin
   ```
   then log out and log in again. You will see the **Admin Panel** (header and sidebar) and can assign roles to users.

## Main features

- **Auth:** Register, login (identifier + password), JWT refresh. Role-based access (System Administrator, Detective, Sergeant, Captain, Police Chief, Judge, etc.).
- **Cases:** Create from complaint (trainee → officer) or directly; assign detective; submit suspects to sergeant.
- **Complaints:** Submit (Complainant), trainee review (Intern), officer review (Officer) → case creation.
- **Evidence:** Add evidence by case; Detective Board with draggable cards and connections; biological evidence review.
- **Suspects:** Detective proposes → Sergeant approves/rejects. Interrogation: detective and sergeant scores (1–10) + notes. Captain decision (GUILTY/NOT GUILTY); CRITICAL cases require Chief approval. Case referred to court on GUILTY.
- **Most Wanted:** Approved suspects only. Score = crime degree (1–4) × days; reward = score × 20,000,000 Rials. Sorted by score (public and dashboard).
- **Trials:** Judge sees trials (created when captain decides GUILTY). Full case view: arrested person, interrogations (detective/sergeant comments), captain decisions, evidence, personnel. Judge records verdict (guilty/innocent) and punishment.
- **Tips & rewards:** Public submit tip; officer/detective review; reward lookup, verify, redeem (national ID + code).
- **Payments:** Bail (level 2–3; level 3 supervisor approval), fines, payment callback.
- **Admin Panel:** User list, assign roles, statistics (System Administrator only).

## Testing

See [SCENARIO.md](SCENARIO.md) for a full testing flow (complaints → case → evidence → suspects → captain decision → trials) and a 0%–100% feature checklist.

## Notes

- Backend must run on **port 8000** for the default frontend dev config (or set `VITE_API_BASE_URL` in `frontend/.env`).
- CORS allows all origins when the backend is in DEBUG mode.
- **API docs:** After starting the backend, open **http://localhost:8000/api/docs/** (Swagger) or **http://localhost:8000/api/redoc/** (ReDoc).