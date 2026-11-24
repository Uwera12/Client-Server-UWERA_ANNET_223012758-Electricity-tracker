# How the project works (plain language)

## 1. The big picture: three parts
Think of a restaurant.

| Part | Restaurant | In this project | Its job |
|---|---|---|---|
| **Client** | The customer and the menu | Next.js web pages (`client/`) | Shows screens and collects what the user types |
| **Server** | The waiter and manager | Django (`server/`) | Checks who you are, checks the rules, does the calculations |
| **Database** | The storage room | Supabase (`supabase/`) | Keeps the data safely |

The customer never walks into the storage room. In the same way, the web page **never talks to the database for data**. It always asks Django. (The page only talks to Supabase to log in.)

```
Browser (Next.js) ──request + token──► Django ──asks──► Supabase Auth ("who is this token?")
                                          └──reads/writes──► Supabase database
```

## 2. What a meter reading means
An electricity meter works like the **odometer in a car**. It shows the **total** electricity used since it was installed, and it only goes up.
- The unit is **kWh** (kilowatt-hour), the unit electricity is sold in.
- Usage = this reading minus the previous reading.
- Example: 1410 on 31 Oct and 1478.75 on 30 Nov means 68.75 kWh used.
- Because a meter cannot go backwards, a **lower reading is a typing mistake**, and the server refuses it.

## 3. One request, step by step: "the user submits a reading"
1. The user types 1500 and a date and clicks **Submit** (client).
2. The page sends the request to Django with a **login token** that proves who the user is.
3. Django sends the token to **Supabase Auth** and asks: "Is this real, and who owns it?"
4. Django looks up the user's **role** (`household`).
5. Django checks the **rules**: is the meter really theirs? is the reading lower than the previous one? is the date in the future? is it a valid number?
6. If everything is fine, Django **saves** the reading and answers **201 Created**. If not, it answers **400** with a clear message and saves nothing.
7. The page shows the answer: a green "Saved" or a red error message.

## 4. The key ideas

**Login and token.** Supabase handles sign-up and passwords (stored hashed, never as plain text). After login the browser holds a token and sends it with every request. No token or a fake token gives **401**.

**Roles.** Each user has a role in the `profiles` table (`household`). Django checks it. A wrong role gives **403**. Today there is only one role, but the check is in place.

**Ownership.** Every query starts with "only this user's meters". Asking for someone else's meter returns **404**, as if it did not exist. The owner's id always comes from the verified token, never from what the browser sends.

**The rules live on the server.** The browser can be bypassed (with dev tools or curl), so only the server can be trusted. The browser checks only make the page friendlier.

**The bill uses tariff bands.** Each slice of the month's usage is charged at its own band's rate, like income tax. Example for 70 kWh: first 20 × 89 + next 30 × 310 + last 20 × 369 = 18,460 RWF. The rates are in the `tariff_bands` table. They are sample values and can be edited without changing any code.

**Row Level Security (RLS).** Database rules saying "a user can only see rows that belong to them". It protects anyone who talks to Supabase directly with the public key. Django connects as the database owner, so Django also checks ownership itself.

**HTTP status codes used:** 200 OK · 201 created · 204 deleted · 400 bad input · 401 not logged in · 403 not allowed · 404 not found.

## 5. What each important file does

| File | Job |
|---|---|
| `supabase/schema.sql` | Creates the tables, keys, rules, tariff bands and security rules |
| `supabase/seed.sql` | Adds 2 meters and 8 sample readings |
| `server/tracker/models.py` | Tells Django what the tables look like |
| `server/tracker/authentication.py` | Checks the token with Supabase ("who is this?") |
| `server/tracker/permissions.py` | Checks the role ("are you allowed?") |
| `server/tracker/serializers.py` | Checks input and holds **the main rule** (reading not lower than the previous one), plus length limits |
| `server/tracker/views.py` and `urls.py` | The endpoints (the addresses the client can call) |
| `server/tracker/billing.py` | The tariff band calculation |
| `server/tracker/services.py` | Works out monthly usage from the readings |
| `server/tracker/errors.py` | Gives every error the same clear shape and logs it |
| `server/tracker/tests.py` | The 25 automatic tests |
| `client/lib/api.js` | Sends requests to Django and adds the token |
| `client/components/UsageChart.js` | The bar chart and the bill estimate box |
| `client/components/ReadingForm.js` | The form that submits a reading and shows the server's answer |
| `client/app/` | The pages: login, dashboard, meters, detail, estimator |

## 6. The endpoints (addresses the client can call)
| Action | Address |
|---|---|
| Server is up? | GET `/api/health/` |
| Who am I? | GET `/api/me/` |
| List / create meters | GET, POST `/api/meters/` |
| One meter: view / edit / delete | GET, PATCH, DELETE `/api/meters/<id>/` |
| List / add readings | GET, POST `/api/meters/<id>/readings/` |
| One reading: view / edit / delete | GET, PATCH, DELETE `/api/readings/<id>/` |
| Bill for a month | GET `/api/meters/<id>/bill/?month=2026-10` |
| Monthly usage for the chart | GET `/api/analytics/monthly/` |
| Estimate for any kWh | GET `/api/bill/estimate/?kwh=70` |
| Tariff bands | GET `/api/tariffs/` |

Readings can be sorted (`?ordering=kwh`) and paged (`?page=2`).

## 7. Daily or monthly?
A reading can be entered for any date, so daily readings work. The "Used since previous" column in the readings table shows the usage between two readings (for daily readings, that is daily usage). The chart and the bill add usage up **per month**.
