from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Allow authenticated users to read, but restrict writes to admins.

    This matches the product rule: regular users can access learning resources,
    while admins manage content/datasets.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return bool(user.is_staff or user.is_superuser)

