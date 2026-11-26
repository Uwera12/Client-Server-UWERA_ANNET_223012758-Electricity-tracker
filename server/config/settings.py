import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
for name in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    host = os.getenv(name)
    if host:
        ALLOWED_HOSTS.append(host)
ALLOWED_HOSTS.extend(
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
)

# Only what this API needs. Users, passwords and sessions live in Supabase Auth,
# so Django's own auth/session apps are intentionally NOT installed.
INSTALLED_APPS = ["corsheaders", "rest_framework", "tracker"]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Africa/Kigali"

# ---- Database: Supabase Postgres (falls back to SQLite so tests run anywhere) ----
DATABASE_URL = os.getenv("DATABASE_URL", "")
RUNNING_TESTS = "test" in sys.argv
if DATABASE_URL and not RUNNING_TESTS:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=0)}
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True  # needed behind Supabase poolers
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "dev.sqlite3"}}
    
# ---- Supabase Auth ----
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# ---- CORS: let the Next.js client call this API from the browser ----
CORS_ALLOWED_ORIGINS = [os.getenv("CLIENT_ORIGIN", "http://localhost:3000")]
CORS_ALLOW_HEADERS = ["authorization", "content-type"]

# ---- Django REST Framework ----
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["tracker.authentication.SupabaseAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["tracker.permissions.IsHousehold"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_PAGINATION_CLASS": "tracker.pagination.StandardPagination",
    "EXCEPTION_HANDLER": "tracker.errors.api_exception_handler",
}

# ---- Logging: one readable line per request outcome in the Django terminal ----
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)-7s %(message)s", "datefmt": "%H:%M:%S"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "loggers": {"tracker": {"handlers": ["console"], "level": "INFO"}},
}

TEST_RUNNER = "tracker.test_runner.UnmanagedModelsRunner"
