from django.db import models


class AssetCategoryChoices(models.TextChoices):
    """Asset category options for inventory items."""

    JETSKI = "jetski", "Jetski"
    BOAT = "boat", "Boat"
    SPEEDBOAT = "speedboat", "Speed Boat"
    PARASAIL = "parasail", "Parasailing Boat"
    VEHICLE = "vehicle", "Vehicle"
    EQUIPMENT = "equipment", "Equipment"
    FUEL = "fuel", "Fuel"
    AMMO = "ammo", "Ammo"
    GENERATOR = "generator", "Generator"
    AMBULANCE = "ambulance", "Ambulance"
    OTHER = "other", "Other"


class StockStatusChoices(models.TextChoices):
    """Inventory stock status options."""

    ORDERED = "ordered", "Ordered"
    REQUIRED = "required", "Required"
    PURCHASED = "purchased", "Purchased"
    CANCELLED = "cancelled", "Cancelled"
    ISSUED = "issued", "Issued"


class HospitalChoices(models.TextChoices):
    """Hospital location options."""

    HOSPITAL_KHANPUR = "khanpur", "Khanpur (Local)"
    HOSPITAL_HARIPUR = "haripur", "Haripur"
    HOSPITAL_TAXILA = "taxila", "Taxila"
    HOSPITAL_POF = "pof", "POF Hospital"
    HOSPITAL_RAWAL = "rawalpindi_isb", "Rawalpindi/Islamabad"
    HOSPITAL_ABBOTTABAD = "abbottabad", "Abbottabad"
    HOSPITAL_OTHERS = "others", "Others"


class PatientTypeChoices(models.TextChoices):
    """Patient type options."""

    EMPLOYEE = "employee", "Employee"
    GUEST = "guest", "Guest"
    LOCAL = "local", "Local"


class AmmoPaymentChoices(models.TextChoices):
    """Ammunition payment options."""

    PAID_VIA_CASH = "paid_via_cash", "Paid via Cash"
    PAID_VIA_TICKETS = "paid_via_tickets", "Paid via Tickets"
    PAID_VIA_GROUPS = "paid_via_groups", "Paid via Groups"
    FREE = "free", "Free Bullets"
