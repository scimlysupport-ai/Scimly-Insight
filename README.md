# Scimly

An AI-assisted, self-serve BI dashboard tool. Upload a CSV/Excel file and
Scimly automatically analyzes it and builds an editable dashboard.

## Status
- ✅ Phase 1 — Project Setup
- ✅ Phase 2 — File Upload Module (drag & drop, validation, recent uploads)
- ✅ Phase 3 — Dataset Analysis Engine (clean data, detect types, generate stats)
- ✅ Phase 4 — Dashboard Recommendation Engine (auto-suggest KPI/Line/Pie/Bar charts)
- ✅ Phase 5 — Dashboard UI (auto-rendered KPI/Line/Pie/Bar charts with real data)
- ✅ Phase 6 — Dynamic Widget System (registry-based renderer, works across arbitrary datasets)
- ✅ Phase 7 — Dashboard Editing (rename, delete, resize, change chart type/axes/colors)
- ✅ Phase 8 — Dashboard Layout (drag, resize, and reposition widgets freely; layout persists)
- ✅ Phase 9 — Global Filters (date/country/product/department filters update every chart)
- ✅ Phase 10 — Save Dashboard (save, open, duplicate, delete named dashboards)
- ✅ Phase 11 — Export (PDF, PNG, CSV, Excel, JSON — all generated client-side from the dashboard's live widgets)
- ✅ Phase 12 — Authentication (email/password + Google/GitHub OAuth login, per-user uploads and dashboards, anonymous data claiming)

## API endpoints so far
- `POST /api/upload` — upload a CSV/XLSX file (scoped to the current user)
- `GET  /api/uploads` — list the current user's recent uploads
- `GET  /api/dataset/{file_id}` — analyze (or retrieve cached analysis) for a file
- `GET  /api/dataset/{file_id}/recommendations` — get recommended chart types
- `GET  /api/dataset/{file_id}/dashboard` — get recommended charts + real chart data
- `POST /api/dataset/{file_id}/chart-preview` — compute data for a user-edited chart config
- `POST /api/dashboards` / `GET /api/dashboards` / `GET|PUT|DELETE /api/dashboards/{id}` / `POST /api/dashboards/{id}/duplicate` — saved dashboards
- `POST /api/auth/register` — email/password sign up
- `POST /api/auth/login` — email/password log in
- `GET  /api/auth/me` — the logged-in user's profile
- `GET  /api/auth/google/login` / `GET /api/auth/google/callback` — Google OAuth
- `GET  /api/auth/github/login` / `GET /api/auth/github/callback` — GitHub OAuth
- `GET  /api/health` — confirms API + database are up

## Stack
- **Frontend:** React + Vite + TypeScript + Tailwind CSS + React Router + Zustand + React Query
- **Backend:** FastAPI + PostgreSQL + SQLAlchemy
- **Infra:** Docker (for Postgres in dev)

## Local setup

See `SETUP_INSTRUCTIONS.md` in this folder for full step-by-step setup.
