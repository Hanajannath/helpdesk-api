from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class UserProfile(models.Model):

    class Role(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        SUPPORT_AGENT = "support_agent", "Support Agent"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
