# Electricity Usage Tracker (Topic 106): Client-Server project

A household enters its electricity meter readings, sees monthly usage as a bar chart, and gets a bill estimate calculated with tariff bands.

```
 Browser (Next.js)  ──token + JSON──►  Django REST API  ──SQL──►  Supabase Postgres
   client/                              server/                    supabase/
   screens, forms, chart                rules, validation,         tables, keys, RLS,
   (never decides anything)             ownership, billing         sample data
          └────────── login only ──────► Supabase Auth ◄── Django asks "who is this token?"
```

| Part     | Folder      | Does                                                                              |
| -------- | ----------- | --------------------------------------------------------------------------------- |
| Database | `supabase/` | Tables, keys, constraints, tariff bands, Row Level Security, sample rows          |
| Server   | `server/`   | Django REST Framework: endpoints, the business rules, bills, analytics, 25 tests  |
| Client   | `client/`   | Next.js: login, meter list, create form, detail page, usage chart + bill estimate |

Hosting and payments are intentionally **not** included.

**Project documents (in `docs/docs/`):** [brief with user stories and screens](docs/docs/01-project-brief.md) · [data model](docs/docs/02-data-model.md) (drawing: `docs/docs/data-model.svg`) · [stack choice, 3 reasons](docs/docs/03-stack-choice.md) · [security checklist](docs/docs/06-security-checklist.md)

---

## 1. Requirements (Windows)

- **Python 3.11+** (python.org: tick "Add python.exe to PATH")
- **Node.js 18+ LTS** (nodejs.org)
- A free **Supabase** project (supabase.com)

Check in PowerShell: `python --version` and `node --version`.

## 2. Supabase (database)

1. Create a project. Save the **database password**.
2. **SQL Editor → New query**, paste `supabase/schema.sql`, **Run**. (Creates tables, tariff bands, RLS.)
3. **Authentication → Providers → Email**: turn **Confirm email OFF** (easier for development).
4. Sign up once in the web app (step 5), then run `supabase/seed.sql` in the SQL Editor. It adds 2 meters + 8 readings (10 sample rows) to the first user.
5. Copy these three things:
   - **Project Settings → API**: the _Project URL_ and the _anon / publishable key_
   - **Connect → Session pooler**: the connection string (works over IPv4)

## 3. Django server

```powershell
cd server
python -m venv venv
venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env             # then edit .env with your 3 values
python manage.py test              # 25 tests, no internet needed
python manage.py runserver         # http://localhost:8000
```

Check: open <http://localhost:8000/api/health/> → `{"status":"ok"}`. **Keep this terminal visible**: it prints one log line per request (needed for the class activities).

## 4. Next.js client

```powershell
cd client
copy .env.local.example .env.local   # edit with your Supabase URL + anon key
npm install
npm run dev                          # http://localhost:3000
```

Sign up → run `seed.sql` (step 2.4) → refresh → you see the sample usage chart.

---

## API reference (all under `/api`, all except `health` need `Authorization: Bearer <token>`)

| Method               | Path                               | Purpose                                                           | Success         | Failures |
| -------------------- | ---------------------------------- | ----------------------------------------------------------------- | --------------- | -------- |
| GET                  | `/health/`                         | Is the server up?                                                 | 200             |          |
| GET                  | `/me/`                             | Who am I, and my role                                             | 200             | 401      |
| GET                  | `/meters/`                         | List my meters (`?ordering=name`, `?page=`)                       | 200             | 401, 403 |
| POST                 | `/meters/`                         | Create a meter `{name, meter_number, location}`                   | 201             | 400      |
| GET / PATCH / DELETE | `/meters/<id>/`                    | One meter                                                         | 200 / 200 / 204 | 404      |
| GET                  | `/meters/<id>/readings/`           | Readings (`?ordering=-read_date`, `kwh`, `?page=`, `?page_size=`) | 200             | 404      |
| POST                 | `/meters/<id>/readings/`           | Add `{kwh, read_date}` **(business rule here)**                   | 201             | 400, 404 |
| GET / PATCH / DELETE | `/readings/<id>/`                  | One reading (PATCH uses the same rule)                            | 200 / 200 / 204 | 400, 404 |
| GET                  | `/meters/<id>/bill/?month=2026-10` | Bill for a month, band by band                                    | 200             | 400, 404 |
| GET                  | `/analytics/monthly/?meter=<id>`   | **Monthly consumption** + bill per month (all meters if omitted)  | 200             | 404      |
| GET                  | `/bill/estimate/?kwh=120`          | "What if" bill for any usage                                      | 200             | 400      |
| GET                  | `/tariffs/`                        | The tariff bands                                                  | 200             |          |

Every error looks like `{"error": "clear message", "details": {...}}`.

### The rules enforced on the server

1. **A new reading cannot be lower than the previous one** (by date). A backdated reading also cannot be higher than a later one.
2. Reading date cannot be in the future; one reading per meter per day; kWh must be a number ≥ 0 and fit the column size. Names (100), meter numbers (50) and locations (200) have length limits.
3. **Bill uses tariff bands**: each slice of kWh is charged at its own band's rate (`server/tracker/billing.py`). Example: 70 kWh = 20×89 + 30×310 + 20×369 = **18,460 RWF**.
4. Ownership: you only ever see your own meters and readings (others get 404).
5. Roles: Django asks Supabase Auth to validate the token, reads the role from `profiles`, and returns 401 (no/bad token) or 403 (wrong role).

> **Tariff rates are SAMPLE values for teaching.** Edit the `tariff_bands` table in Supabase to match your utility's real tariff.

**Consumption** of a reading = its kWh minus the previous reading's kWh, counted in the month of the reading's date. Take readings at the end of each month.

---

## Testing with curl (Windows PowerShell)

Use `curl.exe` (not `curl`, which is a PowerShell alias). Get a token first:

```powershell
cd server
$T = python get_token.py you@example.com YourPassword
curl.exe http://localhost:8000/api/meters/ -H "Authorization: Bearer $T"
```

**Success (201):**

```powershell
curl.exe -i -X POST http://localhost:8000/api/meters/1/readings/ -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{\"kwh\": 1500, \"read_date\": \"2026-11-15\"}"
```

**Failure 1, lower reading (400):**

```powershell
curl.exe -i -X POST http://localhost:8000/api/meters/1/readings/ -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{\"kwh\": 900, \"read_date\": \"2026-11-16\"}"
```

**Failure 2, missing meter (404):**

```powershell
curl.exe -i http://localhost:8000/api/meters/9999/ -H "Authorization: Bearer $T"
```

**No token (401):** `curl.exe -i http://localhost:8000/api/meters/`

---

## Checkpoints (matches the sheet's weekly plan and rubric)

| Week | Show                                                                   | Where in this project                                              |
| ---- | ---------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1    | Tables with sample rows + a GET endpoint in browser and curl           | `schema.sql`, `seed.sql`, `/api/tariffs/` and `/api/meters/`       |
| 2    | POST/PATCH/DELETE, rule on server, 400/404                             | `serializers.py` (`validate`), `views.py`, `python manage.py test` |
| 3    | List, create form, detail page; explain one request in the Network tab | `client/app/meters/…`                                              |
| 4    | Roles end to end, Break-it fixed, demo question                        | `permissions.py`, `ReadingForm.js`                                 |

### Interactive class activities: "user submits a reading"

1. **Log reading:** keep Django's terminal visible, submit a reading in the browser, and match the lines:
   - `INFO Reading accepted: meter=1 kwh=1500.00 date=…` → success
   - `WARNING POST /api/meters/1/readings/ -> 400 A new reading cannot be lower…` → rejected
2. **Predict the status code:** before clicking, predict. Valid → **201**. Lower reading → **400**. Meter id that does not exist → **404**. Not logged in → **401**.

### Break-it challenge: lower reading than last month

Enter a lower kWh in the form. The server answers **400** with `{"error": "A new reading cannot be lower than the previous one. You entered 900.00 kWh, but the reading on 2026-10-31 was 1478.75 kWh."}`, nothing is saved, and `ReadingForm.js` shows that message in red. The fix is the `validate()` method in `server/tracker/serializers.py`, plus showing `error.message` in the client.

### Stretch goal (done)

Sorting (`?ordering=`) and pagination (`?page=`, `?page_size=`) are built in; three curl tests are above (one success, two failures).

---

## Troubleshooting

- **"Cannot reach the server"** in the browser: Django is not running, or `NEXT_PUBLIC_API_URL` is wrong.
- **CORS error:** `CLIENT_ORIGIN` in `server/.env` must be exactly `http://localhost:3000`.
- **401 on every call:** `SUPABASE_URL` / `SUPABASE_ANON_KEY` in `server/.env` don't match the project the client logs in to.
- **Database connection errors:** use the **Session pooler** string (not "Direct connection") and make sure the password has no unescaped special characters (URL-encode `@` as `%40`).
- **Signed up but cannot log in:** turn **Confirm email** off in Supabase Auth, or confirm via the email link.
- **`relation "profiles" does not exist`:** run `schema.sql` first.

## Security notes

- The client holds only the public anon key. The database password stays in `server/.env` (never commit it).
- Django connects as the database owner, which bypasses RLS, so Django enforces ownership itself. RLS still protects direct access through Supabase's API.
