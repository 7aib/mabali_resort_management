from django.db import models
from django.utils import timezone

from mabali_resort_management.mixins import SoftDeleteModelMixin, TimeStampedModelMixin

from .choices import BillStatusChoices, BillTypeChoices, DepartmentChoices, HeadChoices


class FreeBilling(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    date = models.DateField(default=timezone.localdate)
    guest_name = models.CharField(max_length=150, blank=True, default="")
    bill_type = models.CharField(
        max_length=50, choices=BillTypeChoices.choices, default=BillTypeChoices.QB_BILL
    )
    head = models.CharField(
        max_length=100, choices=HeadChoices.choices, default=HeadChoices.GUEST
    )
    bill_status = models.CharField(
        max_length=50, choices=BillStatusChoices.choices, default=BillStatusChoices.PAID
    )
    invoice_no = models.CharField(max_length=50, blank=True, default="")
    department = models.CharField(
        max_length=50, choices=DepartmentChoices.choices, default=DepartmentChoices.ALL
    )
    total_bill_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bill_upload = models.FileField(upload_to="bills/", blank=True, null=True)
    reference = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name_plural = "Free Billings"

    def __str__(self):
        return "%s — %s — Rs. %s on %s" % (
            self.get_head_display(),
            self.guest_name or "—",
            self.total_bill_amount,
            self.date,
        )
