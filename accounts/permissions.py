
from rest_framework.permissions import BasePermission, SAFE_METHODS


class TicketPermission(BasePermission):
    """
    Employees can create tickets.
    Authenticated users can read tickets permitted by the queryset.
    Support agents, admins, and superusers can update/delete tickets.
    """

    def has_permission(self, request, view):
        user = request.user

        # Require authentication
        if not user or not user.is_authenticated:
            return False

        # Allow GET, HEAD, and OPTIONS requests
        if request.method in SAFE_METHODS:
            return True

        # Allow authenticated users to create tickets
        if request.method == "POST":
            return True

        # Allow superusers to modify tickets
        if user.is_superuser:
            return True

        # Allow support agents and admins to modify tickets
        profile = getattr(user, "profile", None)

        return bool(
            profile
            and profile.role in ["support_agent", "admin"]
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Allow safe requests; queryset controls visibility
        if request.method in SAFE_METHODS:
            return True

        # Superusers can modify any ticket
        if user.is_superuser:
            return True

        # Only support agents and admins can modify existing tickets
        profile = getattr(user, "profile", None)

        return bool(
            profile
            and profile.role in ["support_agent", "admin"]
        )
