"""Print a Supabase access token so you can test the API with curl.
Usage (PowerShell):  python get_token.py you@example.com YourPassword
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
if len(sys.argv) != 3:
    sys.exit("Usage: python get_token.py <email> <password>")

resp = requests.post(
    f"{os.environ['SUPABASE_URL'].rstrip('/')}/auth/v1/token?grant_type=password",
    headers={"apikey": os.environ["SUPABASE_ANON_KEY"], "Content-Type": "application/json"},
    json={"email": sys.argv[1], "password": sys.argv[2]},
    timeout=10,
)
if resp.status_code != 200:
    sys.exit(f"Login failed ({resp.status_code}): {resp.text}")
print(resp.json()["access_token"])
