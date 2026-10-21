from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import TicketPermission
from .models import Ticket
from .serializers import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [TicketPermission]
    filterset_fields = ["status", "priority", "category", "assigned_to"]

    ordering_fields = ["created_at", "updated_at", "priority"]
        
    
    search_fields = ["title", "description"]
   
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Ticket.objects.all().select_related(
                "created_by", "assigned_to"
            )

        profile = getattr(user, "profile", None)

        if profile and profile.role == "admin":
            return Ticket.objects.all().select_related(
                "created_by", "assigned_to"
            )

        if profile and profile.role == "support_agent":
            return Ticket.objects.filter(
                Q(assigned_to=user) | Q(status="open")
            ).select_related("created_by", "assigned_to")

        return Ticket.objects.filter(
            created_by=user
        ).select_related("created_by", "assigned_to")

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            status="open",
            assigned_to=None,
        )

    def _require_support_access(self):
        user = self.request.user
        profile = getattr(user, "profile", None)

        if not (
            user.is_superuser
            or (profile and profile.role in ["support_agent", "admin"])
        ):
            raise PermissionDenied(
                "Only support agents and admins can perform this action."
            )

    
    @action(detail=True, methods=["patch"], url_path="assign")
    def assign(self, request, pk=None):
        self._require_support_access()
        ticket = self.get_object()

        user = request.user
        profile = getattr(user, "profile", None)

        # Support agents can assign only tickets assigned to them
        # or tickets that are still unassigned.
        is_admin = user.is_superuser or (
            profile and profile.role == "admin"
        )

        if not is_admin and ticket.assigned_to_id not in (None, user.id):
            raise PermissionDenied(
                "You can assign only unassigned tickets "
                "or tickets assigned to you."
            )

        agent_id = request.data.get("assigned_to")

        if agent_id in (None, ""):
            ticket.assigned_to = None
        else:
            try:
                agent = User.objects.select_related("profile").get(
                    pk=agent_id
                )
            except (User.DoesNotExist, ValueError, TypeError):
                raise ValidationError({
                    "assigned_to": "A valid user ID is required."
                })

            agent_profile = getattr(agent, "profile", None)

            if not agent.is_active or not (
                agent.is_superuser
                or (
                    agent_profile
                    and agent_profile.role == "support_agent"
                )
            ):
                raise ValidationError({
                    "assigned_to": "Select an active support agent."
                })

            ticket.assigned_to = agent

        ticket.save()
        return Response(TicketSerializer(ticket).data)

    
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        self._require_support_access()

        ticket = self.get_object()
        user = request.user
        profile = getattr(user, "profile", None)

        # Admins can update any ticket.
        # Support agents can update only their assigned tickets.
        if not (user.is_superuser or (profile and profile.role == "admin")):
            if ticket.assigned_to_id != user.id:
                raise PermissionDenied(
                    "You can update only tickets assigned to you."
                )

        new_status = request.data.get("status")
        valid_statuses = Ticket.Status.values

        if new_status not in valid_statuses:
            raise ValidationError({
                "status": f"Choose one of: {', '.join(valid_statuses)}"
            })

        ticket.status = new_status
        ticket.save()

        return Response(TicketSerializer(ticket).data)

        return Response(TicketSerializer(ticket).data)
