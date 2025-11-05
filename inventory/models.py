from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from authentication.models import User
from .choices import AmmoCaliberChoices, AssetCategoryChoices, GeneratorCapacityChoices, HospitalChoices, StockStatusChoices, FuelTypeChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin


class InventoryItem(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

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
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.issued_to_asset.category}) - {self.quantity} {self.unit}"


class FuelTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_fuel_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='fuel_txns')
    fuel_type = models.CharField(max_length=10, choices=FuelTypeChoices.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, default='liters')
    transaction_status = models.CharField(max_length=20, choices=StockStatusChoices.choices, default=StockStatusChoices.REQUIRED)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.fuel_type} {self.quantity} {self.unit} -> {self.issued_to or 'stock'}"


class AmmoTransactionLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_ammo_logs')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='ammo_txns')
    caliber = models.CharField(max_length=10, choices=AmmoCaliberChoices.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.caliber} x{self.quantity} -> {self.issued_to or 'stock'}"


class GeneratorLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_generator_log')
    generator = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='generator_logs')
    capacity = models.CharField(max_length=10, choices=GeneratorCapacityChoices.choices)
    run_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    fuel_used_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.generator.code} {self.capacity} @ {self.log_time.date()}"


class AmbulanceLog(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

    ambulance = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='ambulance_logs')
    start_reading_km = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    end_reading_km = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    medical_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    hospital = models.CharField(max_length=30, choices=HospitalChoices.choices)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ambulance_drives')
    notes = models.TextField(blank=True)

    @property
    def kms_travelled(self):
        return max(0, self.end_reading_km - self.start_reading_km)

    def save(self, *args, **kwargs):
        # ensure sensible readings
        if self.end_reading_km is not None and self.start_reading_km is not None and self.end_reading_km < self.start_reading_km:
            raise ValueError("end_reading_km must be >= start_reading_km")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ambulance.code} {self.created_at} kms: {self.kms_travelled}"
