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

## Pages

- **Home** — intro, stats from API
- **Auth** — login (identifier + password), register
- **Dashboard** — role-based modules (cases, complaints, board, high-priority, reports, documents, trials, admin)
- **Detective Board** — draggable evidence cards, SVG connections, export as image
- **High Priority** — suspects list and detail
- **Cases & Complaints** — list, detail, approve/reject flows
- **Reports** — case report, printable
- **Documents** — evidence list/upload by case
- **Admin** — user list, role assignment, stats

## Tests

At least 5 tests are included: `Button.test.tsx`, `authStore.test.ts`, `dashboardModules.test.ts`, `cn.test.ts`, `HomePage.test.tsx`. Run with `npm run test`.
