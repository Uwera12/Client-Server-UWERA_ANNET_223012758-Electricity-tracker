"""Step 2: what role does the caller have? Only 'household' users may use this API."""
from rest_framework.permissions import BasePermission


class IsHousehold(BasePermission):
    message = "Your account role is not allowed to do this. Only 'household' users can."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "household")
