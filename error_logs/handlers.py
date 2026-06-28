"""Custom logging handler that writes errors to the database."""
import logging
import traceback
import threading

_local = threading.local()


def set_current_request(request):
    """Store the current request on the thread for the handler to access."""
    _local.request = request


def get_current_request():
    return getattr(_local, 'request', None)


def clear_current_request():
    _local.request = None


class DatabaseLogHandler(logging.Handler):
    """Logging handler that saves records to the ErrorLog model."""

    def emit(self, record):
        try:
            from error_logs.models import ErrorLog

            request = get_current_request()

            exc_type = ''
            exc_tb = ''
            if record.exc_info and record.exc_info[0]:
                exc_type = record.exc_info[0].__name__
                exc_tb = ''.join(traceback.format_exception(*record.exc_info))

            user_id = None
            user_display = ''
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.pk
                user_display = request.user.get_full_name() or request.user.username

            ErrorLog.objects.create(
                level=record.levelname,
                logger_name=record.name or '',
                message=self.format(record),
                exception_type=exc_type,
                exception_traceback=exc_tb,
                url=getattr(request, 'path', '') if request else '',
                method=getattr(request, 'method', '') if request else '',
                query_string=getattr(request, 'GET', {}).urlencode() if request else '',
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=str(request.META.get('HTTP_USER_AGENT', ''))[:500] if request else '',
                user_id=user_id,
                user_display=user_display,
            )
        except Exception:
            pass

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
