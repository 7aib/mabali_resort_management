"""Inventory management models."""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from authentication.models import User
from .choices import AmmoCaliberChoices, AssetCategoryChoices, GeneratorCapacityChoices, HospitalChoices, StockStatusChoices, FuelTypeChoices, PatientTypeChoices, FuelStatusChoices, VehicleChoices, AmmoStatusChoices, AmmoPaymentChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin


class InventoryItem(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Base inventory item model for tracking assets and supplies."""

    name = models.CharField(max_length=120)  # e.g. "Petrol", "9mm Ammo", "100kv Generator"
    category = models.CharField(max_length=20, choices=AssetCategoryChoices.choices)
    status = models.CharField(max_length=20, choices=StockStatusChoices.choices, default=StockStatusChoices.REQUIRED)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=30, default='unit')  # e.g. liters, pieces, kms
    ordered_at = models.DateTimeField(null=True, blank=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    supplier = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        """Model options."""
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Return string representation of inventory item."""
        return f"{self.name} - {self.quantity} {self.unit}"


class FuelTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log fuel transactions (usage, consumption, transfers)."""

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_fuel_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='fuel_txns')
    fuel_type = models.CharField(max_length=10, choices=FuelTypeChoices.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, default='liters')
    transaction_status = models.CharField(max_length=20, choices=StockStatusChoices.choices, default=StockStatusChoices.REQUIRED)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        """Return string representation of fuel transaction."""
        created_by_name = self.created_by.get_full_name() if self.created_by else 'Unknown'
        return f"{self.fuel_type} {self.quantity} {self.unit} by {created_by_name}"


class AmmoTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log ammunition transactions (issuance, consumption)."""

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_ammo_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='ammo_txns')
    caliber = models.CharField(max_length=10, choices=AmmoCaliberChoices.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        """Return string representation of ammo transaction."""
        created_by_name = self.created_by.get_full_name() if self.created_by else 'Unknown'
        return f"{self.caliber} x{self.quantity} by {created_by_name}"


class GeneratorLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Log generator usage and fuel consumption."""

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_generator_log')
    generator = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='generator_logs')
    capacity = models.CharField(max_length=10, choices=GeneratorCapacityChoices.choices)
    run_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    fuel_used_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        """Return string representation of generator log."""
        return f"{self.generator.name} {self.capacity} @ {self.created_at.date()}"


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


class FuelEntry(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Fuel purchase and issuance log."""

    date = models.DateField(default=timezone.now)
    fuel_type = models.CharField(max_length=20, choices=FuelTypeChoices.choices)
    status = models.CharField(max_length=20, choices=FuelStatusChoices.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    issued_to = models.CharField(max_length=50, choices=VehicleChoices.choices, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Fuel Entries'

    def __str__(self) -> str:
        return f"{self.fuel_type} - {self.status} - {self.quantity}L on {self.date}"


class AmmoEntry(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Shooting range ammunition entry log."""

    date = models.DateField(default=timezone.now)
    bullet_type = models.CharField(max_length=10, choices=AmmoCaliberChoices.choices)
    bullet_status = models.CharField(max_length=20, choices=AmmoStatusChoices.choices)
    bullet_quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    payment = models.CharField(max_length=20, choices=AmmoPaymentChoices.choices)
    free_bullet_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Ammo Entries'

    def __str__(self) -> str:
        return f"{self.bullet_type} - {self.bullet_status} - {self.bullet_quantity} rounds on {self.date}"
