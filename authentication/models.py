from django.contrib.auth.models import AbstractUser
from django.db import models
from .choices import UserRoles
from mabali_resort_management.mixins import TimeStampedModelMixin


class User(TimeStampedModelMixin, AbstractUser):
    role = models.CharField(max_length=20, choices=UserRoles.choices, default=UserRoles.CUSTOMER)

    def __str__(self) -> str:
        return self.username
