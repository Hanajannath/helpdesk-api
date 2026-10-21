# Create your tests here.

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile
from .models import Ticket


class HelpDeskAPITests(APITestCase):

    def setUp(self):
        # Create employee
        self.employee = User.objects.create_user(
            username="employee_test",
            password="TestPass123!"
        )
        UserProfile.objects.get_or_create(
            user=self.employee,
            defaults={"role": "employee"}
        )

        # Create support agent
        self.agent = User.objects.create_user(
            username="agent_test",
            password="TestPass123!"
        )
        agent_profile, created = UserProfile.objects.get_or_create(
             user=self.agent
        )
        agent_profile.role = "support_agent"
        agent_profile.save()

        # Create another employee's ticket
        self.ticket = Ticket.objects.create(
            title="Laptop issue",
            description="Laptop cannot connect to Wi-Fi",
            category="network",
            priority="high",
            status="open",
            created_by=self.employee,
        )

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def test_employee_can_create_ticket(self):
        self.authenticate(self.employee)

        response = self.client.post(
            "/api/tickets/",
            {
                "title": "Keyboard issue",
                "description": "Keyboard is not working",
                "category": "hardware",
                "priority": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Ticket.objects.filter(created_by=self.employee).count(),
            2,
        )

    def test_employee_can_view_own_ticket(self):
        self.authenticate(self.employee)

        response = self.client.get("/api/tickets/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]) if isinstance(
            response.data, dict
        ) and "results" in response.data else len(response.data), 1)

    def test_employee_cannot_update_ticket(self):
        self.authenticate(self.employee)

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/",
            {"title": "Changed title"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_agent_can_update_ticket_status(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()
        self.authenticate(self.agent)

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/status/",
            {"status": "in_progress"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "in_progress")

    def test_unassigned_agent_cannot_update_ticket_status(self):
        self.authenticate(self.agent)

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/status/",
            {"status": "in_progress"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_employee_cannot_assign_ticket(self):
        self.authenticate(self.employee)

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/assign/",
            {"assigned_to": self.agent.id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
