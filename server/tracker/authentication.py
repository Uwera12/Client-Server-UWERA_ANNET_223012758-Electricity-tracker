"""Step 1 of every protected request: who is calling? Ask Supabase Auth."""
import hashlib
import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed

from .models import Profile

log = logging.getLogger("tracker")


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Could not reach Supabase Auth. Try again."


@dataclass
class AuthUser:
    id: str
    email: str
    role: str
    is_authenticated: bool = True


def fetch_supabase_user(token: str) -> dict:
    """Ask Supabase Auth whether this access token is valid. Returns the user JSON."""
    key = "sb-user-" + hashlib.sha256(token.encode()).hexdigest()
    cached = cache.get(key)
    if cached:
        return cached
    try:
        resp = requests.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {token}"},
            timeout=8,
        )
    except requests.RequestException as exc:
        log.error("Supabase Auth unreachable: %s", exc)
        raise ServiceUnavailable()
    if resp.status_code != 200:
        raise AuthenticationFailed("Invalid or expired login token. Please log in again.")
    user = resp.json()
    cache.set(key, user, 30)          # remember for 30 s to avoid one Auth call per request
    return user


class SupabaseAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"               # makes DRF answer 401 (not 403) when no token is sent

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationFailed("Authorization header must look like: Bearer <token>")
        data = fetch_supabase_user(parts[1])
        profile, _ = Profile.objects.get_or_create(id=data["id"], defaults={"role": "household"})
        user = AuthUser(id=str(profile.id), email=data.get("email", ""), role=profile.role)
        return (user, parts[1])
