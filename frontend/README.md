# Police Case Management — Frontend

React frontend for the Police Department Case Management backend. Role-based dashboard with cases, complaints, evidence, suspects, interrogations, captain/chief decisions, trials & verdicts, tips & rewards, and admin.

## Stack

- **React 18** + **TypeScript**
- **Vite** — build tool
- **TailwindCSS** — styling
- **React Router** — routing
- **Zustand** — auth state (persisted)
- **TanStack Query** — API state and caching
- **Axios** — HTTP client (JWT, refresh)
- **Framer Motion** — animations
- **Vitest + React Testing Library** — tests

## Setup

```bash
npm install
```

Optional `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Default dev config uses this URL when `DEV` is true. Run the backend on port 8000.

## Scripts

- `npm run dev` — start dev server (port 3000)
- `npm run build` — production build
- `npm run preview` — preview production build
- `npm run test` — run tests
- `npm run test:watch` — tests in watch mode

## Docker

Build and run:

```bash
docker build -t police-frontend .
docker run -p 3000:80 police-frontend
```

**Full stack (backend + frontend):** If the backend is also Dockerized, add to your root `docker-compose.yml`:

```yaml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    environment: [DEBUG=1]
    volumes: [.:/app]
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
```

Then set the frontend to proxy `/api` to `http://backend:8000` (see Dockerfile nginx config).

## Structure

- `src/api` — axios client and API endpoints
- `src/components` — reusable UI and layout
- `src/config` — dashboard modules (role-based)
- `src/features` — (optional) feature-specific code
- `src/hooks` — React Query and custom hooks
- `src/pages` — page components
- `src/routes` — router and protected routes
- `src/store` — Zustand auth store
- `src/types` — TypeScript types
- `src/utils` — helpers

## Structure

| Folder | Purpose |
|--------|---------|
| **src/api** | Axios client, interceptors (JWT + refresh), API endpoints (auth, cases, complaints, evidence, suspects, interrogations, captain-decisions, trials, verdicts, tips, rewards, payments, statistics) |
| **src/components** | Reusable UI (Button, Card, Input, Modal, Skeleton, etc.) and layout (RootLayout, DashboardLayout) |
| **src/config** | Dashboard modules (role-based: cases, complaints, board, high-priority, reports, documents, tips, captain-decision, chief-approval, reward-verify, trials, admin) |
| **src/hooks** | React Query and custom hooks (e.g. useSuspects, useSuspectsHighPriority) |
| **src/pages** | Page components |
| **src/routes** | Router, protected routes, role-based redirects |
| **src/store** | Zustand auth store (user, tokens, hasRole, roleNames) |
| **src/types** | TypeScript interfaces (User, Case, Complaint, Evidence, Suspect, Interrogation, Trial, Verdict, etc.) |
| **src/utils** | Helpers (formatDate, formatCurrencyRials, cn) |

## Pages & Routes

| Route | Description |
|-------|-------------|
| **/** | Home — intro, link to Most Wanted and Submit Tip |
| **/login** | Login (identifier + password) |
| **/register** | Register (username, password, email, phone, full_name, national_id, optional roles) |
| **/most-wanted** | Public Most Wanted list (approved suspects, score, reward) |
| **/submit-tip** | Public submit tip form |
| **/dashboard** | Dashboard overview (role-based modules in sidebar) |
| **/dashboard/cases** | Cases list and create |
| **/dashboard/cases/:id** | Case detail: assign detective, suspects, interrogations, captain decision panel (detective/sergeant scores), submit to sergeant |
| **/dashboard/complaints** | Complaints list |
| **/dashboard/complaints/:id** | Complaint detail (trainee/officer review) |
| **/dashboard/board** | Detective Board — draggable evidence cards, connections, export as image |
| **/dashboard/high-priority** | Most Wanted (dashboard) — approved suspects, score, reward |
| **/dashboard/reports** | Case reports — select case, view report, print |
| **/dashboard/documents** | Documents & Evidence — list/add evidence by case |
| **/dashboard/tips** | Tips & Rewards — list tips, officer/detective review, redeem |
| **/dashboard/captain-decision** | Captain Decision — GUILTY/NOT GUILTY after interrogation scores (CRITICAL → chief approval) |
| **/dashboard/chief-approval** | Chief Approval — approve/reject captain decision for CRITICAL cases |
| **/dashboard/reward-verify** | Reward Verification — verify by national ID + code, mark paid |
| **/dashboard/trials** | Trials list (Judge); open trial for full case, arrested person, interrogations, captain decisions, record verdict |
| **/dashboard/trials/:id** | Trial detail — full case data, defendant, detective/sergeant comments, verdict form |
| **/dashboard/admin** | Admin Panel — users, assign roles, stats (System Administrator only) |

## Dashboard Modules (by role)

Modules shown in the sidebar depend on the user’s roles. Roles include: System Administrator, Complainant / Witness, Intern, Police Officer, Detective, Sergeant, Captain, Police Chief, Judge, Forensic Doctor. See `src/config/dashboardModules.ts` for the full list and paths.

## Docker

Build and run:

```bash
docker build -t police-frontend .
docker run -p 3000:80 police-frontend
```

For full stack (backend + frontend), add the frontend service to your root `docker-compose.yml` and point the frontend at the backend API (e.g. proxy `/api` to the backend service).

## Tests

Tests include Button, authStore, dashboardModules, cn, HomePage. Run with `npm run test`.

## License

University project — Semester 7 Web Course.
