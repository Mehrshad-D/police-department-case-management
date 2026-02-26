# Police Department Case Management System — Backend

Django REST Framework API for the digitized police operations system: cases, complaints, evidence, suspects, interrogations, captain/chief decisions, trials & verdicts, tips & rewards, and payments.

## Tech Stack

- **Framework:** Django 4.2 + Django REST Framework
- **Auth:** JWT (Simple JWT)
- **API docs:** drf-spectacular (OpenAPI 3 / Swagger, ReDoc)
- **Database:** SQLite (default), PostgreSQL (optional via env)

## Setup

From the **backend** directory:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```


Run migrations and seed roles:

```bash
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_roles
./venv/bin/python manage.py createsuperuser
./venv/bin/python manage.py assign_superuser_as_admin
```

The last command gives your superuser the **System Administrator** role so you can use the app’s **Admin Panel** (user and role management) after logging in.

Run server (port 8000):

```bash
# Option A: use the run script (uses venv’s Python automatically)
./run.sh

# Option B: activate venv then run
source venv/bin/activate
./venv/bin/python manage.py runserver 8000
```

The frontend (when run on port 3000) calls `http://localhost:8000/api/` in development. CORS allows all origins when `DEBUG=True`.

## API Base URL

- **API root:** `http://localhost:8000/api/`
- **Auth:** `http://localhost:8000/api/auth/`
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/redoc/`

## Auth

- **Register:** `POST /api/auth/register/` — body: `username`, `password`, `email`, `phone`, `full_name`, `national_id` (all unique).
- **Login:** `POST /api/auth/login/` — body: `identifier` (username, national_id, phone, or email) + `password`. Returns JWT tokens.
- **Refresh:** `POST /api/auth/token/refresh/` — body: `{ "refresh": "<refresh_token>" }`.

## Project Structure

```
config/          # Django project settings and root URLs
accounts/        # User, Role, auth, permissions
cases/           # Case, Complaint, CrimeSceneReport, CaseComplainant
evidence/        # Evidence (all types), EvidenceLink
suspects/        # Suspect, Interrogation, ArrestOrder
judiciary/       # Trial, Verdict
tips_rewards/    # Tip, Reward
payments/        # BailPayment, FinePayment
core/            # AuditLog, Notification, statistics
```

## License

University project — Semester 7 Web Course.
