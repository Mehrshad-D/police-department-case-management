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

- **Register:** `POST /api/auth/register/` — body: `username`, `password`, `email`, `phone`, `full_name`, `national_id` (optional `role_ids`).
- **Login:** `POST /api/auth/login/` — body: `identifier` (username, national_id, phone, or email) + `password`. Returns JWT tokens and user (with `role_names`).
- **Refresh:** `POST /api/auth/token/refresh/` — body: `{ "refresh": "<refresh_token>" }`.
- **Users:** `GET /api/auth/users/`, `GET /api/auth/users/detectives/`, `GET /api/auth/users/suspect-candidates/`, `PATCH /api/auth/users/<id>/` (admin).
- **Roles:** `GET /api/auth/roles/`, CRUD for role management.

## Project Structure

| App | Description |
|-----|-------------|
| **config/** | Django project settings and root URLs |
| **accounts/** | User, Role, auth (login/register), permissions (Detective, Sergeant, Captain, Police Chief, Judge, etc.) |
| **cases/** | Case, Complaint, CrimeSceneReport, CaseComplainant; complaint flow (trainee → officer → case) |
| **evidence/** | Evidence (all types), EvidenceLink, biological evidence review |
| **suspects/** | Suspect (propose → sergeant approve/reject), Interrogation (detective/sergeant scores), ArrestOrder, CaptainDecision, ChiefApproval; Most Wanted (approved suspects, score = crime_degree × days, reward = score × 20M Rials) |
| **judiciary/** | Trial (created when captain decides GUILTY; chief approval for CRITICAL), Verdict (judge records guilty/innocent + punishment) |
| **tips_rewards/** | Tip (submit → officer review → detective confirm), Reward (lookup, verify, redeem) |
| **payments/** | BailPayment (level 2–3 suspects; level 3 supervisor approval), FinePayment, payment callback |
| **core/** | AuditLog, Notification, statistics |

## Main API Endpoints (prefix `/api/`)

- **Cases:** `GET/POST cases/`, `GET/PATCH cases/<id>/`, `POST cases/<id>/submit-suspects-to-sergeant/`, `GET/POST cases/<case_pk>/complainants/`
- **Complaints:** `GET/POST complaints/`, `GET complaints/<id>/`, `POST complaints/<id>/correct/`, `POST complaints/<id>/trainee-review/`, `POST complaints/<id>/officer-review/`
- **Crime scene:** `POST cases/crime-scene/`, `GET/POST crime-scene-reports/`, `POST crime-scene-reports/<id>/approve/`
- **Evidence:** `GET/POST evidence/`, `GET/PATCH evidence/<id>/`, biological review/image; `GET/POST cases/<case_pk>/evidence-links/`
- **Suspects:** `GET/POST suspects/`, `GET suspects/<id>/`, `POST suspects/<id>/supervisor-review/`, `GET suspects/high-priority/`, `GET most-wanted/` (public)
- **Interrogations:** `GET/POST interrogations/`, `POST interrogations/<id>/submit-detective-score/`, `POST interrogations/<id>/submit-sergeant-score/`, `POST interrogations/<id>/captain-decision/`, `POST interrogations/<id>/chief-confirm/`
- **Captain / Chief:** `GET/POST captain-decisions/`, `POST captain-decisions/<id>/chief-approval/`
- **Arrest orders:** `GET/POST arrest-orders/`
- **Trials:** `GET trials/` (Judge), `GET trials/<id>/`, `GET trials/<id>/full/` (full case + arrested suspect + interrogations + captain decisions), `GET trials/full-by-case/<case_id>/`, `POST verdicts/`
- **Tips & rewards:** `GET/POST tips/`, `POST tips/<id>/officer-review/`, `POST tips/<id>/detective-confirm/`, `POST rewards/lookup/`, `POST rewards/verify/`, `POST rewards/redeem/`
- **Payments:** `GET/POST bail/`, `POST bail/<id>/approve/`, `GET/POST fines/`, `GET callback/` (payment gateway callback)
- **Core:** `GET statistics/`, `GET notifications/`, `POST notifications/<id>/read/`

