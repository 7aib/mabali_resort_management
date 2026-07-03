from django.db import models


class RoomCategoryChoices(models.TextChoices):
    HUT = 'hut', 'Hut'
    SUITE = 'suite', 'Suite'
    ROOM = 'room', 'Room'
    HONEYMOON = 'honeymoon', 'Honeymoon'


class PaymentMethodChoices(models.TextChoices):
    CASH = 'cash', 'Cash'
    CREDIT = 'credit', 'Credit Card'
    IBFT = 'ibft', 'IBFT'


class PaymentTypeChoices(models.TextChoices):
    ADVANCE = 'advance', 'Advance Payment'
    FINAL = 'final', 'Final Payment'


class ReservationStatusChoices(models.TextChoices):
    CONFIRMED = 'confirmed', 'Confirmed'
    CHECKED_IN = 'checked_in', 'Checked In'
    CHECKED_OUT = 'checked_out', 'Checked Out'
    CANCELLED = 'cancelled', 'Cancelled'


class BankChoices(models.TextChoices):
    MABALI_FBIL = 'mabali_fbil', 'Mabali FBIL'
