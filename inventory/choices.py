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
    ENGINE_OIL = 'engine_oil', 'Engine Oil'


class FuelStatusChoices(models.TextChoices):
    """Fuel status options."""
    PURCHASED = 'purchased', 'Purchased'
    ISSUED = 'issued', 'Issued'


class VehicleChoices(models.TextChoices):
    """Vehicle/equipment options for fuel issued."""
    J1 = 'J1', 'J1 (Jetski)'
    J2 = 'J2', 'J2 (Jetski)'
    J3 = 'J3', 'J3 (Jetski)'
    J4 = 'J4', 'J4 (Jetski)'
    J5 = 'J5', 'J5 (Jetski)'
    J6 = 'J6', 'J6 (Jetski)'
    J7 = 'J7', 'J7 (Jetski)'
    J8 = 'J8', 'J8 (Jetski)'
    J9 = 'J9', 'J9 (Jetski)'
    J10 = 'J10', 'J10 (Jetski)'
    J11 = 'J11', 'J11 (Jetski)'
    B1 = 'B1', 'B1 (Boat)'
    B2 = 'B2', 'B2 (Boat)'
    B3 = 'B3', 'B3 (Boat)'
    B4 = 'B4', 'B4 (Boat)'
    B5 = 'B5', 'B5 (Boat)'
    SP1 = 'SP1', 'SP1 (Speed Boat)'
    SP2 = 'SP2', 'SP2 (Speed Boat)'
    SP3 = 'SP3', 'SP3 (Speed Boat)'
    P1 = 'P1', 'P1 (Parasailing Boat)'
    P2 = 'P2', 'P2 (Parasailing Boat)'
    BIKE = 'bike', 'Bike'
    PAINT = 'paint', 'Paint'
    GRASS_CUTTER = 'grass_cutter', 'Grass Cutter'
    ATV = 'atv', 'ATV'
    AMBULANCE = 'ambulance', 'Ambulance'
    CAR = 'car', 'Car'
    BOAT = 'boat', 'Boat'
    HIACE = 'hiace', 'Hiace'


class GeneratorCapacityChoices(models.TextChoices):
    """Generator capacity options."""
    CAP_35KV = '35kv', '35kv'
    CAP_100KV = '100kv', '100kv'
    CAP_200KV = '200kv', '200kv'


class HospitalChoices(models.TextChoices):
    """Hospital location options."""
    HOSPITAL_KHANPUR = 'khanpur', 'Khanpur (Local)'
    HOSPITAL_HARIPUR = 'haripur', 'Haripur'
    HOSPITAL_TAXILA = 'taxila', 'Taxila'
    HOSPITAL_POF = 'pof', 'POF Hospital'
    HOSPITAL_RAWAL = 'rawalpindi_isb', 'Rawalpindi/Islamabad'
    HOSPITAL_ABBOTTABAD = 'abbottabad', 'Abbottabad'
    HOSPITAL_OTHERS = 'others', 'Others'


class PatientTypeChoices(models.TextChoices):
    """Patient type options."""
    EMPLOYEE = 'employee', 'Employee'
    GUEST = 'guest', 'Guest'
    LOCAL = 'local', 'Local'


class AmmoStatusChoices(models.TextChoices):
    """Ammunition status options."""
    RECEIVED = 'received', 'Received'
    FIRED = 'fired', 'Fired'
    MAIN_STORE = 'main_store', 'Main Store'


class AmmoPaymentChoices(models.TextChoices):
    """Ammunition payment options."""
    PAID_VIA_TICKETS = 'paid_via_tickets', 'Paid via Tickets'
    PAID_VIA_GROUPS = 'paid_via_groups', 'Paid via Groups'
    FREE = 'free', 'Free Bullets'