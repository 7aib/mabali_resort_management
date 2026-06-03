from django.db import models


class AssetCategoryChoices(models.TextChoices):
    """Asset category options for inventory items."""
    JETSKI = 'jetski', 'Jetski'
    BOAT = 'boat', 'Boat'
    SPEEDBOAT = 'speedboat', 'Speed Boat'
    PARASAIL = 'parasail', 'Parasailing Boat'
    VEHICLE = 'vehicle', 'Vehicle'
    EQUIPMENT = 'equipment', 'Equipment'
    FUEL = 'fuel', 'Fuel'
    AMMO = 'ammo', 'Ammo'
    GENERATOR = 'generator', 'Generator'
    AMBULANCE = 'ambulance', 'Ambulance'
    OTHER = 'other', 'Other'


class AmmoCaliberChoices(models.TextChoices):
    """Ammunition caliber options."""
    NINE_MM = '9mm', '9mm'
    FORTY_FIVE = '.45', '.45'
    TWENTY_TWO = '.22', '.22'
    THIRTY_EIGHT = '.38', '.38'


class StockStatusChoices(models.TextChoices):
    """Inventory stock status options."""
    REQUIRED = 'required', 'Required'
    PURCHASED = 'purchased', 'Purchased'
    ISSUED = 'issued', 'Issued'
    IN_STOCK = 'in_stock', 'In Stock'
    LOW_STOCK = 'low_stock', 'Low Stock'
    OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'


class FuelTypeChoices(models.TextChoices):
    """Fuel type options."""
    PETROL = 'petrol', 'Petrol'
    DIESEL = 'diesel', 'Diesel'
    KEROSENE = 'kerosene', 'Kerosene'


class GeneratorCapacityChoices(models.TextChoices):
    """Generator capacity options."""
    CAP_35KV = '35kv', '35kv'
    CAP_100KV = '100kv', '100kv'
    CAP_200KV = '200kv', '200kv'


class HospitalChoices(models.TextChoices):
    """Hospital location options."""
    HOSPITAL_KHANPUR = 'khanpur', 'Khanpur'
    HOSPITAL_HARIPUR = 'haripur', 'Haripur'
    HOSPITAL_TAXILA = 'taxila', 'Taxila'
    HOSPITAL_POF = 'pof', 'POF Hospital'
    HOSPITAL_RAWAL = 'rawalpindi_isb', 'Rawalpindi/Islamabad'
    HOSPITAL_ABBOTTABAD = 'abbottabad', 'Abbottabad'
    HOSPITAL_OTHERS = 'others', 'Others'