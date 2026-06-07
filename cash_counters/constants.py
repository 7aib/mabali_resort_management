from django.db import models

class VisitTypeChoices(models.TextChoices):
    PAID = 'Paid', 'Paid'
    COMPLEMENTARY = 'Complementary', 'Complementary'
    NIGHT_STAY = 'Night Stay', 'Night Stay'
    GROUP = 'Group', 'Group'
    DECOR_TEAM = 'Decor team events', 'Decor team events'

class GateChoices(models.TextChoices):
    MAIN = 'Main Gate', 'Main Gate'
    EVENT = 'Event Gate', 'Event Gate'
    LAKE_SIDE = 'Lake Side gate', 'Lake Side gate'

class StatusChoices (models.TextChoices):
    OLD = 'Old', 'Old'
    NEW = 'New', 'New'

class CitiesChoices(models.TextChoices):
    ISLAMABAD = 'Islamabad', 'Islamabad'
    RAWALPINDI = 'Rawalpindi', 'Rawalpindi'
    LAHORE = 'Lahore', 'Lahore'
    KARACHI = 'Karachi', 'Karachi'
    PESHAWAR = 'Peshawar', 'Peshawar'
    QUETTA = 'Quetta', 'Quetta'
    MULTAN = 'Multan', 'Multan'
    FAISALABAD = 'Faisalabad', 'Faisalabad'
    OTHER = 'Other', 'Other'

class PaymentMethodChoices(models.TextChoices):
    CASH = 'Cash', 'Cash'
    CARD = 'Card', 'Card'