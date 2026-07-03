from functools import wraps
from django.core.exceptions import PermissionDenied


def roles_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if request.user.role not in allowed_roles:
                raise PermissionDenied("Permission denied.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator