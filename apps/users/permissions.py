from rest_framework import permissions


class IsAuthenticatedCustom(permissions.BasePermission):
    """Simple authenticated check compatible with custom User model."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user:
            return False
        # our User model has `id` field
        return bool(getattr(user, 'id', None))
