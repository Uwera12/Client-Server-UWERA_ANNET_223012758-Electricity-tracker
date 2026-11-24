# Build and test log: what was done, what went wrong, what changed

This is the story of the project in order. Each problem has a cause and a fix, which is what shows that the project was tested properly.

## Stage 1: Planning
- The project was chosen from the lecturer's topic sheet (topic 106, Electricity Usage Tracker) and its guidelines were followed.
- The VUBA-VUBA case study showed the pattern to copy: the client shows, the server decides, the database remembers, and the server checks a login token on every request.
- The lecturer's slides on the three stacks listed what a good project must contain. The project was checked against them (brief, data model, security, Git).

## Stage 2: Database (Supabase)
- `schema.sql` was run in the Supabase SQL Editor and created four tables: `profiles`, `meters`, `readings`, `tariff_bands`.
- **Problem:** the editor showed "Unable to reach the server". **Cause:** the new project was still starting up. **Fix:** waited, refreshed, and ran it again.
- **Problem:** only the first 30 lines had been pasted. **Fix:** copied the whole file (Ctrl+A, Ctrl+C) and checked the last line was the `tariffs readable` policy.
- Result: "Success. No rows returned" and four tables in the Table Editor.
- `seed.sql` added 2 meters and 8 readings (10 sample rows) to the first user who signed up.

## Stage 3: Server (Django)
- Endpoints for meters and readings (list, create, view, edit, delete), the monthly usage, the bill, the estimate and the tariffs.
- The main rule: a new reading cannot be lower than the previous one (and a back-dated reading cannot be higher than a later one).
- Errors are consistent: `{"error": "clear message"}`. Messages name the field, for example `name: This field may not be blank.`
- The terminal prints one log line per request, for example `Reading accepted` or `400 A new reading cannot be lower...`.

## Stage 4: Automatic tests
- Tests use a fake login and a temporary database, so they never touch real data.
- First version: 22 tests. After the length limits were added: **25 tests**.
- They cover: no token (401), fake token (401), wrong role (403), missing meter (404), someone else's meter (404), good reading (201), lower reading (400), future date (400), duplicate date (400), negative or huge number (400), too-long text (400), script text stored as plain text, sorting and paging, the bill calculation, and monthly usage.

## Stage 5: Client (Next.js)
- Pages: login and sign-up, dashboard with chart, meter list, add meter, meter detail with readings, bill estimator.
- Each page has a loading state, an empty state and an error state.
- The menu is chosen by role (only `household` exists today).

## Setup problems met on the computer, and how each was solved
| Problem | Cause | Fix |
|---|---|---|
| Node.js download page offered fnm / 0install | Extra tools not needed | Used `winget install OpenJS.NodeJS.LTS` |
| `npm` "running scripts is disabled" | PowerShell blocks scripts by default | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `cd` path did not exist | The zip had been extracted into a folder inside a folder | Searched with `Get-ChildItem` and used the inner `electricity-tracker` folder |
| Which key to copy | Supabase now has Publishable and Secret keys | Used the **publishable** key (public). The **secret** key is never used. |
| Where to find the connection string | It is not on the Framework tab | Connect → Direct tab → Session pooler (port 5432) |
| Database password contains `@` | `@` marks the end of the password in the connection string | Reset to a simple password, or write `@` as `%40` |
| `next` is not recognized | Packages were not installed | Ran `npm install` in the client folder, then `npm run dev` |
| Computer shut down by accident | Running programs stopped | Re-ran the same start commands. Files and database were safe. |

## Problems found while testing, and the changes made
1. **Tests were slow (312 seconds) and ended with an error** (`database "test_postgres" is being accessed by other users`).
   - Cause: with the Supabase address in `.env`, the test command tried to make its temporary database on Supabase.
   - Fix: one line in `server/config/settings.py` (`RUNNING_TESTS`) makes tests always use a local temporary database.
   - Result: 25 tests pass in **0.229 seconds**, and the real data is never touched.
2. **Length limits were missing** (the lecturer's security slide says to validate type, length and required).
   - Fix: name 100, meter number 50, location 200 characters, enforced in the server, in the database and in the form. Three new tests were added.
3. **A meter with one month of data showed one very wide bar.**
   - Cause: the chart divides its width by the number of bars.
   - Fix: a maximum bar width of 70 in `UsageChart.js`.
4. **Interface touches:** the sample-rates note was removed from the estimator page, and a footer with the student's name and registration number was added to every page.

## Checks done by hand (to prove the results are right)
| Case | Usage | Calculation | Bill |
|---|---|---|---|
| August, all meters | 64.25 kWh | 20×89 + 30×310 + 14.25×369 | 16,338 RWF |
| A November reading | 33.25 kWh | 20×89 + 13.25×310 = 1,780 + 4,107.50 | 5,888 RWF |
| Shop meter, October | 92.5 kWh | 20×89 + 30×310 + 42.5×369 | 26,763 RWF |
| Estimator, 70 kWh | 70 kWh | 20×89 + 30×310 + 20×369 | 18,460 RWF |

## What the working system showed
- Sign-up and login worked, and the role showed as `household`.
- The sample data loaded and the chart and bill box worked together.
- A lower reading was rejected with a red message, and the server log showed the `400` line.
- Sorting by date and by kWh, and paging, worked.

## Still to do
- Put the project on GitHub (small commits, no secrets).
- Deployment on Vercel, with the small changes it needs (allowed hosts, CORS address, API address, environment variables).
- Update to a safe Next.js version before deploying, and re-test.
