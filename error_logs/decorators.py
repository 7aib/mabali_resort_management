"""Reusable decorator that logs any unhandled exception in a view."""
import logging
import functools

logger = logging.getLogger('django')


def log_errors(view_func):
    """
    Decorator: wraps a view so any unhandled exception is logged
    to the database via the ErrorLog handler, then re-raised so
    Django's default 505 handling still fires.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception:
            logger.exception('Unhandled exception in %s', view_func.__qualname__)
            raise
    return wrapper
