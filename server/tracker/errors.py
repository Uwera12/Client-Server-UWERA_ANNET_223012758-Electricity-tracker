"""One error shape for every failure: {"error": "<clear message>", "details": {...}}"""
import logging

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

log = logging.getLogger("tracker")


GENERIC = ("This field is required.", "This field may not be blank.", "This field may not be null.",
           "A valid number is required.", "A valid integer is required.")


def _first_message(detail, field=None):
    if isinstance(detail, dict):
        for key, value in detail.items():
            return _first_message(value, None if key == "non_field_errors" else key)
    if isinstance(detail, (list, tuple)) and detail:
        return _first_message(detail[0], field)
    text = str(detail)
    # Generic DRF messages do not say WHICH field, so add the field name.
    return f"{field}: {text}" if field and text in GENERIC else text


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    message = str(detail) if detail else _first_message(response.data)
    body = {"error": message}
    if isinstance(exc, ValidationError):
        body["details"] = response.data
    response.data = body
    request = context.get("request")
    log.warning("%s %s -> %s %s", getattr(request, "method", "?"), getattr(request, "path", "?"),
                response.status_code, message)
    return response
