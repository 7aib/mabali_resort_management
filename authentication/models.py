from django.contrib.auth.models import AbstractUser
from django.db import models
from .choices import UserRoles


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRoles.choices, default=UserRoles.CUSTOMER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.username
