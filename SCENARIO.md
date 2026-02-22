# Testing scenario: Police Case Management System

Use this flow to check case creation, complaints, evidence, and the Admin Panel.

---

## 1. First-time setup

### Backend
```bash
cd backend
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_roles
./venv/bin/python manage.py createsuperuser   # create your admin user (e.g. admin / your@email.com / password)
./venv/bin/python manage.py assign_superuser_as_admin   # gives your superuser the "System Administrator" role
./run.sh   # or: ./venv/bin/python manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Log in with the superuser account. You should see the **Dashboard** with an **Admin Panel** link in the header and in the sidebar.

---

## 2. Admin Panel (custom app admin, not Django admin)

- Go to **Dashboard** → **Admin Panel** (or click **Admin Panel** in the header).
- You’ll see **User management** and **system stats** (users, cases, complaints, evidence).
- Use **Assign roles** on a user to give them roles (e.g. Detective, Police Officer, Intern).
- Create a second user (e.g. register from the app or via Django admin) and assign them roles like **Complainant / Witness** or **Intern** for the next steps.

---

## 3. Create a case (two ways)

### Option A: From a complaint (complaint → trainee → officer → case)

1. **Register or use a user with role "Complainant / Witness".** Assign that role in Admin Panel if needed.
2. Go to **Dashboard** → **Complaints**. Click (or use the flow that) **submits a new complaint** – create one with title and description.
3. **Log in as an Intern** (assign yourself or another user the "Intern" role). Go to **Complaints**, open the complaint, and use **Approve (forward to officer)** or **Return for correction** (with a message).
4. **Log in as a Police Officer**. Go to **Complaints**, open the same complaint, and use **Approve (create case)**. A **case** is created and linked to the complaint.
5. Go to **Dashboard** → **Cases**. You should see the new case.

### Option B: Create a case directly (as Officer or Admin)

1. Log in as a user with **Police Officer** or **System Administrator** (or another role that can create cases).
2. Go to **Dashboard** → **Cases**. Use the **Create case** action if the UI exposes it (e.g. button or link to a create form).
3. Fill in title, description, severity, and save. The new case appears in the list.

*(If the frontend doesn’t have a “Create case” button yet, use the API: `POST /api/cases/` with `{"title": "...", "description": "...", "severity": 3}` or create via Django admin once.)*

---

## 4. Assign detective and add evidence

1. Open the case (e.g. from **Cases** list). If the UI allows, **assign a detective** (user with Detective role). Otherwise do it via API: `PATCH /api/cases/<id>/` with `{"assigned_detective": <user_id>}`.
2. Go to **Dashboard** → **Documents & Evidence**. Enter the **case ID**, then add evidence (title, type, description). Add at least two items so you can link them on the board.
3. Go to **Dashboard** → **Detective Board**. Select the same case. You should see **draggable evidence cards**. Double‑click one card, then double‑click another to **create a connection**. Use **Export as image** to save the board.

---

## 5. Suspect and high‑priority list

1. **Propose a suspect** (as Detective): either from the case view or via API: `POST /api/suspects/` with `{"case_id": <id>, "user_id": <user_id>}` (the user_id is the person marked as suspect).
2. **Log in as Sergeant** (or a user with Sergeant role). Go to **Suspects** or the relevant flow and **approve** the suspect (arrest starts) or **reject**.
3. Go to **Dashboard** → **High Priority Suspects**. Suspects become high‑priority after more than one month; you can check the list and filters.

---

## 6. Reports and other modules

- **Reports:** Go to **Dashboard** → **Reports**. Open a case (or select a case ID if the UI asks). View the **case report** and use **Print report** for a printable layout.
- **Trials:** If your user has Judge/Captain/Chief role, use **Dashboard** → **Trials** to see trials and verdicts (data appears when cases are referred to judiciary).

---

## 7. Where is the Admin Panel?

- **In the app:** After you run `assign_superuser_as_admin` and log in with that superuser, the **Admin Panel** is available as:
  - **Header:** link **Admin Panel** (top right area).
  - **Sidebar:** **Admin Panel** under the Dashboard modules (only for users with **System Administrator** role).
- **URL:** **http://localhost:3000/dashboard/admin**
- Only users with the **System Administrator** role can open it. If you see “no roles” or can’t access it, run `./venv/bin/python manage.py assign_superuser_as_admin` in the backend and log in again.

---

## Quick checklist

| Step | What to do |
|------|------------|
| 1 | Run backend: `migrate`, `seed_roles`, `createsuperuser`, `assign_superuser_as_admin`, `run.sh` |
| 2 | Run frontend: `npm run dev`, open http://localhost:3000 |
| 3 | Log in with superuser → see Dashboard and Admin Panel |
| 4 | Admin Panel → assign roles to other users (or yourself for other roles) |
| 5 | Submit a complaint (Complainant) → review as Intern → approve as Officer → case created |
| 6 | Cases → open case; Documents & Evidence → add evidence for that case |
| 7 | Detective Board → select case → drag cards, connect evidence, export image |
| 8 | Propose suspect (Detective) → approve/reject (Sergeant) |
| 9 | Reports → view/print case report; High Priority Suspects → check list |

If statistics on the dashboard are zero at first, that’s normal until you create cases, complaints, and evidence; they update as you follow the scenario.

---

## Full feature test (0%–100%)

Use this checklist to test every major feature once. Tick each box as you complete it; when all are done, you’ve covered the system 0%–100%.

### Setup (do once)
- [ ] Backend: `migrate`, `seed_roles`, `createsuperuser`, `assign_superuser_as_admin`, then `run.sh`
- [ ] Frontend: `npm run dev`, open http://localhost:3000
- [ ] Log in as superuser and confirm **Dashboard** and **Admin Panel** appear in header/sidebar

### Auth & users
- [ ] **Login:** Log out and log in again with identifier (username or email) + password
- [ ] **Register:** Register a second user (e.g. complainant) and confirm they appear in Admin Panel
- [ ] **No-roles message:** Log in as a user with no roles; confirm dashboard shows “no roles” message and no modules

### Admin Panel
- [ ] **Assign roles:** Open Admin Panel → User management → click **Assign roles** on a user. Confirm the **list of roles** (e.g. System Administrator, Complainant / Witness, Intern, Police Officer, Detective) appears with checkboxes. Select/deselect roles and click **Save**; confirm the user’s roles update in the table.
- [ ] **Stats cards:** Confirm Admin Panel shows stats (Users, Cases, Complaints, Evidence)

### Complaints flow
- [ ] **New complaint:** As Complainant (or user with that role), go to Complaints and create a new complaint (title + description)
- [ ] **Trainee review:** As Intern, open the complaint and use **Approve (forward to officer)** or **Return for correction**
- [ ] **Officer review:** As Police Officer, open the complaint and use **Approve (create case)** so a case is created and linked

### Cases
- [ ] **Cases list:** Open Dashboard → Cases and see at least one case
- [ ] **Create case:** As Officer/Admin, use **Create case** (if available) and create a case with title, description, severity
- [ ] **Assign detective:** Open a case and assign a detective (if the UI allows)

### Evidence & Detective Board
- [ ] **Add evidence:** Dashboard → Documents & Evidence → add at least two evidence items for a case (title, type, description)
- [ ] **Detective Board:** Open Detective Board, select the case, confirm evidence cards appear; double‑click two cards to create a link; use **Export as image**

### Suspects
- [ ] **Propose suspect:** As Detective, propose a suspect for a case (from case view or API)
- [ ] **Supervisor review:** As Sergeant, approve or reject the suspect
- [ ] **High Priority Suspects:** Open High Priority Suspects list and confirm it loads (and shows suspects after 1+ month if any)

### Reports & other
- [ ] **Reports:** Dashboard → Reports → open/select a case and view report; use **Print report**
- [ ] **Trials / Verdicts:** If your user has Judge/Captain/Chief role, open Trials and Verdicts and confirm pages load

### Final check
- [ ] Log in again as admin; Admin Panel → Assign roles still shows roles and saves correctly
- [ ] All sidebar modules you have access to open without errors

When every item above is checked, you have run a 0%–100% pass over the main features of the system.
