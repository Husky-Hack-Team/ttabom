# ttabom

A small banking-style dashboard: a Nuxt frontend and a FastAPI backend backed by Supabase PostgreSQL, deployed as two Vercel projects from this one repo.

## Project structure

```
ttabom/
├── analysis/                 # Data replay (pandas; runs locally, never deployed)
│   ├── engine.py, config.py  # Verified Contact Payment check (pure Python)
│   ├── oracle.py             # The only reader of the Member Key (scoring + simulated answers)
│   ├── overlay.py            # Seeded overlay → data/overlay/
│   ├── replay.py             # Scores the check → analysis/out/
│   ├── load_supabase.py      # Upserts the replay into the sim_* tables
│   ├── pilot.md              # 90-day pilot plan
│   └── tests/                # pytest
├── data/
│   ├── raw/                  # HuskyHack v2 events, Member Key, data dictionary (.xlsx)
│   └── overlay/              # Synthetic contacts, accounts, channels, stated recipients (+ README of assumptions)
├── docs/                     # Challenge docs and design resolutions
├── backend/                  # Python + FastAPI (Vercel project, preset "Other")
│   ├── api/index.py          # FastAPI app; every route is under /api
│   ├── vcp/                  # Copy of the engine + read-only replay routes (kept in sync by a test)
│   ├── requirements.txt      # Deps Vercel installs (fastapi, supabase, python-dotenv)
│   ├── schema.sql            # One-file copy of the migration + seed, for the SQL Editor
│   └── .env.example          # Backend env var template
├── supabase/                 # Supabase CLI project
│   ├── config.toml           # CLI config (local stack settings)
│   ├── migrations/           # Database schema, applied with `supabase db push`
│   └── seed.sql              # Sample transactions
├── frontend/                 # Nuxt 4 + Vue + Tailwind CSS v4 (Vercel project, preset "Nuxt")
│   ├── app/app.vue
│   ├── app/pages/index.vue   # Dashboard: balance, add-transaction form, recent activity
│   ├── app/pages/demo.vue    # Demo mode: links to the employee screens
│   ├── app/pages/replay.vue  # Data Replay: member picker, timeline, metrics
│   ├── app/pages/case.vue    # Employee case screen (Linda's wire, hold timer)
│   ├── app/assets/css/main.css
│   ├── nuxt.config.ts
│   └── .env.example          # Frontend env var template
└── .vscode/settings.json     # Points VS Code at backend/.venv
```

### API

| Method | Path                | Description                                   |
| ------ | ------------------- | --------------------------------------------- |
| GET    | `/api/health`       | `{"ok": true}`, needs no database             |
| GET    | `/api/transactions` | Transactions, newest first                    |
| POST   | `/api/transactions` | Body `{"description": str, "amount": number}` |
| GET    | `/api/balance`      | `{"balance": number}`, the sum of all amounts |
| GET    | `/api/replay/metrics` | Replay headline metrics and walkthroughs |
| GET    | `/api/replay/members?filter=all\|anchor\|lookalike\|scam\|routine` | Members for the picker |
| GET    | `/api/replay/members/{id}` | One member's events, our decisions, and summary |
| GET    | `/api/replay/cases` | Held payments for the employee case screen (engine output only) |
| POST   | `/api/vcp/check` | Run the check on one payment: body `{"event", "history", "ctx"}` |

Negative amounts are debits and positive amounts are credits.

## Local setup

Requirements: Python 3.12+, Node.js 22+ (npm 11.21+ recommended; see Troubleshooting), and a Supabase project.

1. **Database.** Apply the schema to your Supabase project with the Supabase CLI (run from the repo root; `npx` downloads the CLI, so there's nothing to install):
   ```sh
   npx supabase login                                   # opens the browser once
   npx supabase link --project-ref <your-project-ref>   # the "abcd1234" in https://abcd1234.supabase.co; asks for the DB password
   npx supabase db push --include-seed                  # creates the table and inserts the sample rows
   ```
   Later schema changes go in a new file in `supabase/migrations/` (`npx supabase migration new <name>`), followed by `npx supabase db push`.
   If you'd rather not use the CLI, open **SQL Editor** in the Supabase dashboard, paste in `backend/schema.sql`, and run it.
2. **Backend.**
   ```sh
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn supabase python-dotenv
   cp .env.example .env
   ```
   Fill in `backend/.env` with the values from Supabase **Project Settings → API**: the Project URL (just `https://<ref>.supabase.co`, without `/rest/v1/`) goes in `SUPABASE_URL` and the `service_role` key goes in `SUPABASE_SERVICE_ROLE_KEY`. The service role key is a secret. Keep it in the backend only and never commit it.
3. **Frontend.**
   ```sh
   cd frontend
   npm install
   ```
   You only need `cp .env.example .env` if your API runs somewhere other than `http://localhost:8000`.

## Data replay

Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.

```sh
python3 -m venv analysis/.venv
analysis/.venv/bin/pip install -r analysis/requirements.txt
analysis/.venv/bin/python analysis/overlay.py         # data/overlay/ (seed 2026, deterministic)
analysis/.venv/bin/python analysis/replay.py          # analysis/out/ and a metrics summary
analysis/.venv/bin/python -m pytest analysis/tests    # engine and replay tests
npx supabase db push                                  # creates the sim_* tables
analysis/.venv/bin/python analysis/load_supabase.py   # upserts the replay (uses backend/.env)
```

`analysis/engine.py` and `analysis/config.py` are copied to `backend/vcp/`. After editing them, run `cp analysis/engine.py analysis/config.py backend/vcp/`; a test fails if the copies drift.

## Running locally

Use two terminals.

```sh
# Terminal 1: backend on http://localhost:8000
cd backend
source .venv/bin/activate
uvicorn api.index:app --reload --port 8000
```

```sh
# Terminal 2: frontend on http://localhost:3000
cd frontend
npm run dev
```

Check the API at http://localhost:8000/api/health. Interactive API docs are at http://localhost:8000/docs.

## Deploying to Vercel

Create **two** Vercel projects that import this same GitHub repo.

### 1. Backend project

1. In Vercel, choose **Add New → Project** and import the repo.
2. Set **Root Directory** to `backend` and **Framework Preset** to **Other**.
3. Add these **Environment Variables**:
   - `SUPABASE_URL`: your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: your Supabase service role key
   - `FRONTEND_URL`: the frontend's production URL, for example `https://ttabom.vercel.app` (no trailing slash). You won't have this until step 2 is done, so add it afterwards and redeploy.
4. Deploy, then confirm that `https://<backend-domain>/api/health` returns `{"ok":true}`.

### 2. Frontend project

1. Choose **Add New → Project** and import the same repo again.
2. Set **Root Directory** to `frontend` and **Framework Preset** to **Nuxt.js**.
3. Add this **Environment Variable**:
   - `NUXT_PUBLIC_API_BASE`: the backend URL, for example `https://ttabom-api.vercel.app` (**no trailing slash**)
4. Deploy.

### 3. Connect the two

Go back to the backend project, set `FRONTEND_URL` to the frontend URL, and **redeploy** the backend.

| Project  | Variables                                                      |
| -------- | -------------------------------------------------------------- |
| backend  | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `FRONTEND_URL`    |
| frontend | `NUXT_PUBLIC_API_BASE`                                         |

## Troubleshooting

- **Every backend route returns `{"detail":"Not Found"}` on Vercel**: don't add a `vercel.json` with a catch-all rewrite to the backend. Vercel detects FastAPI from `api/index.py` and sends every path to the app on its own. A rewrite to `/api/index` makes the app see `/api/index` for every request.
- **`Database error: Could not find the table 'public.transactions'`**: the migration hasn't been applied to the project `SUPABASE_URL` points to. Run `npx supabase db push --include-seed` (after `link`), or paste `backend/schema.sql` into that project's SQL Editor.
- **CORS error in the browser console** ("blocked by CORS policy"): the backend allows only `http://localhost:3000` plus `FRONTEND_URL`. On Vercel, `FRONTEND_URL` must match the frontend's origin exactly: `https://`, no trailing slash, no path. Preview deployments get different URLs and won't match unless you set `FRONTEND_URL` for them too. Locally, the frontend has to run on port 3000.
- **"Server is missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"**: locally, check that `backend/.env` exists and is filled in, and restart uvicorn. On Vercel, add the variables in **Project Settings → Environment Variables** for the right environment (Production/Preview), then redeploy.
- **Frontend still calls `localhost:8000` in production**: `NUXT_PUBLIC_API_BASE` isn't set in the frontend project, or you set it without redeploying.
- **Changed an env var and nothing happened**: Vercel applies env var changes only to new deployments. Open **Deployments**, then **⋯ → Redeploy** on the latest one.
- **`npm install` crashes with `Cannot read properties of null (reading 'edgesOut')`**: this is a bug in older npm 11 releases. Run `npx npm@11.21.1 install` instead, or update npm.
