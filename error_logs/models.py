"""Error log model — stores every exception captured by Django."""
from django.db import models
from django.utils import timezone


class ErrorLog(models.Model):
    """Single error/exception record."""

    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    logger_name = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    exception_type = models.CharField(max_length=300, blank=True, default='')
    exception_traceback = models.TextField(blank=True, default='')

    # Request context
    url = models.CharField(max_length=500, blank=True, default='')
    method = models.CharField(max_length=10, blank=True, default='')
    query_string = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default='')
    user_id = models.IntegerField(null=True, blank=True)
    user_display = models.CharField(max_length=150, blank=True, default='')

    # Metadata
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'

    def __str__(self):
        return '[%s] %s — %s' % (self.level, self.created_at.strftime('%Y-%m-%d %H:%M:%S'), self.message[:80])
