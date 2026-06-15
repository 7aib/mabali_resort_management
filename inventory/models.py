"""Inventory management models."""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from authentication.models import User
from .choices import AssetCategoryChoices, HospitalChoices, PatientTypeChoices, StockStatusChoices, AmmoPaymentChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin


class InventoryItem(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Base inventory item model - reference table for assets and supplies."""

    name = models.CharField(max_length=120)  # e.g. "Petrol", "9mm Ammo", "100kv Generator"
    category = models.CharField(max_length=20, choices=AssetCategoryChoices.choices)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, blank=True)  # e.g. "liters", "rounds", "units"
    supplier = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class FuelTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log fuel transactions (purchases, issuances)."""

    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_fuel_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='fuel_txns')
    transaction_status = models.CharField(max_length=20, choices=StockStatusChoices.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    issued_to = models.ForeignKey(
        InventoryItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_received_logs'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Fuel Transactions'

    def save(self, *args, **kwargs):
        from decimal import Decimal
        old_status = None
        if self.pk:
            try:
                old_status = FuelTransactionLog.objects.get(pk=self.pk).transaction_status
            except FuelTransactionLog.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.inventory_item and old_status != self.transaction_status:
            qty = Decimal(str(self.quantity))
            item = self.inventory_item
            if self.transaction_status == StockStatusChoices.PURCHASED:
                item.stock_quantity += qty
                item.save(update_fields=['stock_quantity'])
            elif self.transaction_status == StockStatusChoices.ISSUED:
                item.stock_quantity = max(Decimal('0'), item.stock_quantity - qty)
                item.save(update_fields=['stock_quantity'])

    def __str__(self) -> str:
        return f"{self.transaction_status} - {self.quantity}L on {self.date}"


class AmmoTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log ammunition transactions (received, fired)."""

    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_ammo_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='ammo_txns')
    transaction_status = models.CharField(max_length=20, choices=StockStatusChoices.choices)
    bullet_quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    payment = models.CharField(max_length=20, choices=AmmoPaymentChoices.choices, blank=True)
    free_bullet_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Ammo Transactions'

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            try:
                old_status = AmmoTransactionLog.objects.get(pk=self.pk).transaction_status
            except AmmoTransactionLog.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.inventory_item and old_status != self.transaction_status:
            item = self.inventory_item
            qty = self.bullet_quantity
            if self.transaction_status == StockStatusChoices.PURCHASED:
                item.stock_quantity += qty
                item.save(update_fields=['stock_quantity'])
            elif self.transaction_status == StockStatusChoices.ISSUED:
                item.stock_quantity = max(0, item.stock_quantity - qty)
                item.save(update_fields=['stock_quantity'])

    def __str__(self) -> str:
        return f"{self.transaction_status} - {self.bullet_quantity} rounds on {self.date}"


class GeneratorLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log generator usage and fuel consumption."""

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_generator_log')
    generator = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='generator_logs')
    run_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    fuel_used_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.generator.name} @ {self.created_at.date()}"


class AmbulanceLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log ambulance trips including distance and medical expenses."""

    date = models.DateField(default=timezone.now)
    patient_name = models.CharField(max_length=150, default='')
    patient_type = models.CharField(max_length=20, choices=PatientTypeChoices.choices, default=PatientTypeChoices.LOCAL)
    ambulance = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='ambulance_logs')
    start_reading_km = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    end_reading_km = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    medical_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    hospital = models.CharField(max_length=30, choices=HospitalChoices.choices)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ambulance_drives')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Ambulance Logs'

    @property
    def kms_travelled(self):
        return max(0, self.end_reading_km - self.start_reading_km)

    def save(self, *args, **kwargs):
        """Validate ambulance log readings before saving."""
        from django.core.exceptions import ValidationError
        # ensure sensible readings
        if self.end_reading_km is not None and self.start_reading_km is not None and self.end_reading_km < self.start_reading_km:
            raise ValidationError("end_reading_km must be >= start_reading_km")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of ambulance log."""
        return f"{self.patient_name} - {self.hospital} on {self.date}"
