"""User role choices for the authentication app."""
from django.db import models


class UserRoles(models.TextChoices):
    """User role enumeration for role-based access control."""
    CASHIER = "CASHIER", "Cashier"
    ACCOUNTANT = "ACCOUNTANT", "Accountant"
    MAIN_CASHIER = "MAIN_CASHIER", "Main Cashier"
    CEO = "CEO", "CEO"
    HOST = "HOST", "Host"
    SALE = "SALE", "Sale"
    CUSTOMER = "CUSTOMER", "Customer"
    DRIVER = "DRIVER", "Driver"
    WAITER = "WAITER", "Waiter"
    HR_MANAGER = "HR_MANAGER", "HR Manager"
