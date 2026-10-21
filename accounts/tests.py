from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationAPITests(APITestCase):

    def test_employee_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newemployee",
                "email": "employee@example.com",
                "password": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            User.objects.filter(username="newemployee").exists()
        )

        user = User.objects.get(username="newemployee")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertEqual(user.profile.role, "employee")

    def test_registration_rejects_short_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "shortpass",
                "email": "short@example.com",
                "password": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(
            username="existinguser",
            password="SecurePass123!",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "existinguser",
                "email": "another@example.com",
                "password": "SecurePass123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
