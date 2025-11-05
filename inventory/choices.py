from django.db import models as model

class AssetCategoryChoices(model.TextChoices):
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


class AmmoCaliberChoices(model.TextChoices):
    NINE_MM = '9mm', '9mm'
    FORTY_FIVE = '.45', '.45'
    TWENTY_TWO = '.22', '.22'
    THIRTY_EIGHT = '.38', '.38'

class StockStatusChoices(model.TextChoices):
    # Required means items that need to be ordered to replenish stock
    REQUIRED = 'required', 'Required' 
    # Ordered means items that have been in our stock 
    PURCHASED = 'purchased', 'Purchased'
    # Issued means items that have been issued to assets or consumed
    ISSUED = 'issued', 'Issued'

    IN_STOCK = 'in_stock', 'In Stock'
    LOW_STOCK = 'low_stock', 'Low Stock'
    OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'

class FuelTypeChoices(model.TextChoices):
    PETROL = 'petrol', 'Petrol'
    DIESEL = 'diesel', 'Diesel'
    KEROSENE = 'kerosene', 'Kerosene'

class GeneratorCapacityChoices(model.TextChoices):
    CAP_35KV = '35kv', '35kv'
    CAP_100KV = '100kv', '100kv'
    CAP_200KV = '200kv', '200kv'

class HospitalChoices(model.TextChoices):
    HOSPITAL_KHANPUR = 'khanpur', 'Khanpur'
    HOSPITAL_HARIPUR = 'haripur', 'Haripur'
    HOSPITAL_TAXILA = 'taxila', 'Taxila'
    HOSPITAL_POF = 'pof', 'POF Hospital'
    HOSPITAL_RAWAL = 'rawalpindi_isb', 'Rawalpindi/Islamabad'
    HOSPITAL_ABBOTTABAD = 'abbottabad', 'Abbottabad'
    HOSPITAL_OTHERS = 'others', 'Others'