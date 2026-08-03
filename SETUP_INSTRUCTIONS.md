# Scimly — Phase 1 Setup Instructions

Follow these steps in order. Everything here is copy-paste, no coding needed.

## 1. Install tools (one-time only)

Install these if you don't already have them:

- **Node.js** (v18 or newer) → https://nodejs.org (choose the LTS version)
- **Python** (v3.11 or newer) → https://www.python.org/downloads/
- **Docker Desktop** → https://www.docker.com/products/docker-desktop
- **Git** → https://git-scm.com/downloads

After installing, confirm each one works by opening a terminal and running:
```
node -v
python3 --version
docker -v
git --version
```
Each should print a version number.

## 2. Unzip the project

Unzip the `Scimly.zip` file I gave you anywhere on your computer (e.g. Desktop).
Open a terminal **inside that `Scimly` folder**.

## 3. Start the database (Docker)

```
cd docker
docker compose up -d
```
This starts PostgreSQL in the background. Leave it running — you only need to do this once per work session (or set Docker to start automatically).

To check it's running: `docker ps` — you should see `scimly_postgres` in the list.

## 4. Start the backend (FastAPI)

Open a **new terminal window**, then:
```
cd Scimly/backend
python3 -m venv venv
```

Activate the virtual environment:
- **Mac/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

Then install dependencies and copy the env file:
```
pip install -r requirements.txt
cp .env.example .env
```
(Windows: use `copy .env.example .env` instead of `cp`)

Now start the server:
```
uvicorn app.main:app --reload
```
You should see something like `Uvicorn running on http://127.0.0.1:8000`.

**Test it:** open http://localhost:8000/api/health in your browser. You should see:
```json
{"status":"ok","api":"running","database":"connected"}
```
If you see this, the backend + database are working. Leave this terminal running.

## 5. Start the frontend (React)

Open a **third terminal window**, then:
```
cd Scimly/frontend
npm install
npm run dev
```
You should see `Local: http://localhost:5173/`.

**Test it:** open http://localhost:5173 in your browser. You should see the Scimly page with a "System status" box showing:
- API: running
- Database: connected

## 6. Initialize Git (optional but recommended)

Back in the root `Scimly` folder:
```
git init
git add .
git commit -m "Phase 1: Project setup"
```

---

## ✅ Phase 1 is working when:
- `docker ps` shows `scimly_postgres` running
- http://localhost:8000/api/health returns a JSON success response
- http://localhost:5173 shows the Scimly page with "API: running" and "Database: connected"

## 7. Test Phases 2–4 (Upload → Analysis → Chart Recommendations)

On the home page (http://localhost:5173), click **"Go to Upload →"**, or go directly to
http://localhost:5173/upload

Upload any CSV file (a sales spreadsheet, expense list, anything with a mix of
numbers, categories, and dates works best). You should see, in order:
1. An upload progress bar
2. A **Dataset summary** box — row/column counts and each column's detected type
   (numeric, categorical, datetime, text, boolean)
3. A **Recommended charts** box — KPI/Line/Pie/Bar suggestions based on your data
4. Your file appears under **Recent uploads** — click any past upload to reload its analysis

If you don't have a CSV handy, here's a quick one to test with — save this as `sample_sales.csv`:
```csv
date,country,category,revenue,quantity
2024-01-01,India,Electronics,15000,12
2024-01-02,USA,Clothing,8000,20
2024-01-03,India,Electronics,12000,10
2024-01-04,UK,Electronics,9500,8
2024-01-05,USA,Clothing,7000,18
```

## 8. Test Phase 5 (Dashboard UI)

From the Upload page, after your file's recommendations appear, click
**"View full dashboard →"** — or go directly to
http://localhost:5173/dashboard/1 (replace `1` with your file's ID).

You should see actual charts rendered:
- **KPI cards** — total revenue, total quantity, etc.
- **Line chart** — the numeric column plotted over time
- **Pie chart** — category breakdowns (country, category, etc.)
- **Bar chart** — distribution of any remaining numeric columns

There's no editing yet (that's Phase 7) — the dashboard just auto-renders
based on what the backend recommends.

## 9. Test Phase 6 (Dynamic Widget System)

Phase 6 is mostly a robustness upgrade — the dashboard now works reliably
for *any* dataset shape, not just clean sales data. Try uploading a few
different kinds of files and confirm nothing breaks:

- A file with only numeric columns and no dates
- A file with a single row
- A file with a column of long free-text notes (should show no chart for
  that column, instead of a broken pie chart of full sentences)
- A file where every value in a column is identical

In each case the dashboard should either show relevant charts or a clean
"Not enough data to show this chart" message — never a blank screen or crash.

## 10. Test Phase 7 (Dashboard Editing)

On any dashboard page, click **"Edit dashboard"** in the top right. Every
widget now shows a small toolbar above it. Try each of these:

- **Rename** — click the pencil, type a new title, press Enter
- **Change chart type** — use the dropdown to switch a widget between KPI/Line/Pie/Bar
- **Change column / axis** — pick a different column (or X/Y axis for line charts)
- **Change color** — click any color dot to recolor that widget
- **Resize** — click the resize button to cycle Small → Wide → Full width
- **Delete** — click the trash icon to remove a widget

Click **"Done editing"** to hide the toolbars and see the clean result.
Your changes are saved in the browser automatically — refresh the page and
they should still be there. Click **"Reset changes"** (visible in edit mode)
to discard all edits and go back to the auto-generated dashboard.

Note: edits are stored in your browser for now, not on the server — that's
intentional, since Phase 10 introduces proper saved dashboards in the database.

## 11. Test Phase 8 (Dashboard Layout)

With **"Edit dashboard"** still on, try:

- **Drag** — click and hold anywhere on a widget (not on its toolbar) and
  move it to a new position. Other widgets shift out of the way automatically.
- **Resize** — hover over the bottom-right corner of a widget until you see
  a resize handle, then drag to make it bigger or smaller.

Click **"Done editing"** — your layout stays exactly as you left it. Refresh
the page — it's still there (saved in your browser). Click **"Reset layout"**
(visible in edit mode) to go back to the automatic layout.

Try this on a small browser window too — the grid adapts to a single column
on narrow screens.

## 12. Test Phase 11 (Export)

On any dashboard page, click the **"Export"** button (top right, where
"Download PDF" used to be). You'll see five options:

- **PDF** — a printable report: one section per widget, with real data
  tables for table widgets and a value summary for charts.
- **PNG** — a single image screenshot of the dashboard exactly as it's
  laid out on screen right now (works in both edit and view mode).
- **CSV** — a plain-text file with each widget's data written out as
  its own labeled section.
- **Excel** — a `.xlsx` workbook with one sheet per widget, named after
  the widget's title.
- **JSON** — the raw widget list (chart type, title, columns, and the
  live data behind each one) plus the file ID and any active filters —
  useful for piping a dashboard's data into another tool.

All five are generated entirely in the browser (no server round-trip),
so they reflect whatever filters are currently active and whatever
edits you've made. Try applying a filter first and confirm the
exported files only contain the filtered data.

**Note:** Phase 11 adds a new frontend dependency (`xlsx`, for the
Excel export). If you pull this update, re-run `npm install` in the
`frontend` folder before starting the dev server again.

## 13. Test Phase 12 (Authentication)

**One-time setup after pulling this update:**

1. Backend deps changed — from `backend` (with your venv activated):
   ```
   pip install -r requirements.txt
   ```
2. The `users` and `uploaded_files` tables both gained new columns, and
   `create_all()` only ever *adds* new tables — it won't alter one that
   already exists. Since this is dev data, the simplest fix is to drop
   and let the backend recreate them:
   ```
   docker exec -it <your-postgres-container> psql -U scimly_user -d scimly_db \
     -c "DROP TABLE IF EXISTS saved_dashboards, uploaded_files, users CASCADE;"
   ```
   Then just start the backend as usual — `Base.metadata.create_all()`
   recreates all three with the new columns. (You'll lose any saved
   dashboards from earlier testing, which is expected.)
3. Copy the new variables from `.env.example` into your `.env` if you
   don't already have them — the defaults are enough to test
   email/password login right away. Google/GitHub login stay disabled
   (with a clear error message if you click them) until you fill in
   real OAuth credentials — see the comments in `.env.example` for
   where to create those and which redirect URIs to register.

**Try it:**

- Go to **Upload** or **Home** — you'll see a **"Log in"** link in the
  top corner.
- Click it, then **"Sign up"** — create an account with an email and
  password. You're immediately logged in and redirected to
  **My Account**, which shows your recent uploads and saved
  dashboards.
- Before signing up, try uploading a file or saving a dashboard while
  logged out, *then* register — that anonymous data should reappear
  under your new account instead of disappearing. That's the
  device-to-account "claiming" behavior.
- Log out (button on the Account page), then log back in with the
  same email/password — your data should still be there.
- If you've filled in Google or GitHub OAuth credentials, try
  **"Continue with Google"** / **"Continue with GitHub"** from the
  login or register page — it's a normal redirect flow (you'll briefly
  leave the app and come back logged in).
- Everything that worked anonymously before (Upload, dashboards,
  saving) still works exactly the same if you never log in at all —
  logging in is optional, not required.

## Daily workflow going forward
Each time you want to work on the project, you need **3 things running**:
1. `docker compose up -d` (from the `docker` folder) — only if not already running
2. `uvicorn app.main:app --reload` (from `backend`, with venv activated)
3. `npm run dev` (from `frontend`)

Once you've confirmed sign up, log in/out, and device-data claiming feel
right, tell me and we'll move to **Phase 13: Large Dataset Support** —
background processing (Celery + Redis) for files too big to handle in a
single request.
