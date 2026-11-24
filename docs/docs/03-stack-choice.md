# Why this stack? Next.js + Django + Supabase

| Layer | Tool | Language |
|---|---|---|
| Client (what the user sees) | Next.js (React) | JavaScript |
| Server (rules and logic) | Django + Django REST Framework | Python |
| Database and login | Supabase (Postgres + Auth) | SQL |

## Three reasons
1. **The data fits a relational database.** Households own meters and meters own readings. Rules such as "one reading per day" and "kWh cannot be negative" fit a database with keys and constraints. The lecturer's comparison slide lists this stack as best for apps with data and logins.
2. **Login is ready-made and secure.** Supabase Auth handles sign-up, hashed passwords and tokens, so no password code had to be written. Django only asks Supabase "who owns this token?".
3. **The server is separate and testable.** The rules sit in Django where users cannot change them. They can be tested without any web page (25 automatic tests and curl). This also matches the module's goal: client, server and database each doing their own job.

## The honest trade-off
Three tools means more setup than one all-in-one framework. This was accepted because separate layers make it easy to see and explain what each part does.
