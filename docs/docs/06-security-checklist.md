# Security checklist: "try to break it"

Each row is an attack, what should happen, and where the app defends itself.
To test with curl, first get a token:
```powershell
cd server
$T = python get_token.py your@email.com YourPassword
```

| # | Attack | How to try it | Expected result | Defended in |
|---|---|---|---|---|
| 1 | Not logged in | `curl.exe -i http://localhost:8000/api/meters/` | **401** | `authentication.py` |
| 2 | Fake token | add `-H "Authorization: Bearer abc"` | **401** | the Supabase check in `authentication.py` |
| 3 | Someone else's data | use another user's meter id in the address | **404**, never 200 | `views.py` (`get_my_meter`) |
| 4 | Lower reading | send a kWh lower than the previous one | **400** with message | `serializers.py` (`validate`) |
| 5 | Empty value | send an empty name | **400** | serializer |
| 6 | Very long text | a name of 101+ characters | **400** | serializer and database rule |
| 7 | Huge number | `kwh` of 1000000000000 | **400** | serializer |
| 8 | Script in a text field | name `<script>alert(1)</script>` | stored as plain text, shown as text, never runs | React escapes output |
| 9 | Pretend to be another owner | send someone else's `household_id` in the body | ignored: the owner always comes from the token | `views.py` (`perform_create`) |
| 10 | Another website calls the API | request from a different address | blocked by the browser (CORS) | `settings.py` |

## Other protections
- **Passwords:** never stored by this app. Supabase stores them hashed.
- **Secrets:** kept in `.env` and `.env.local`, which Git ignores.
- **Database access:** all queries use Django's tools, not hand-written SQL text.
- **Row Level Security:** the database itself only shows a user their own rows.
- **Length limits and number limits:** stop oversized input.
- **Debug mode off when live:** `DJANGO_DEBUG=False` (to set when deploying).
- **HTTPS:** applies when deployed.

## Where the proof is
`python manage.py test` runs 25 tests that cover rows 1 to 9. Write down what each curl test returns and keep the notes as evidence.
