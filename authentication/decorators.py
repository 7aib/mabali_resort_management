from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from .choices import UserRoles


def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a particular role,
    raising a PermissionDenied exception if necessary.
    """

    def check_role(user):
        if not user.is_authenticated:
            return False
        if user.role in allowed_roles or user.is_superuser:
            return True
        raise PermissionDenied

    return user_passes_test(check_role)


def ceo_or_hr_required(view_func):
    """
    Decorator for views that checks whether a user is a CEO or HR Manager.
    """
    allowed_roles = [UserRoles.CEO, UserRoles.HR_MANAGER]
    return role_required(allowed_roles)(view_func)
