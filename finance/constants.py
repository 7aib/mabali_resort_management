from django.db import models


class POSPaymentMethodChoices(models.TextChoices):
    CASH = 'Cash', 'Cash'
    IBFT = 'IBFT', 'IBFT'
    CREDIT_CARD = 'Credit Card', 'Credit Card'


class CounterTypeChoices(models.TextChoices):
    MAIN_RESTAURANT_LSR = 'Main Restaurant LSR', 'Main Restaurant LSR'
    ADVENTURE_AREA = 'Adventure Area', 'Adventure Area'
    RECEPTION = 'Reception', 'Reception'
    WATER_SPORTS = 'Water Sports', 'Water Sports'
    WATER_SPORT_TUCK_SHOP = 'Water Sport Tuck Shop', 'Water Sport Tuck Shop'
    EVENT_BAR = 'Event Bar', 'Event Bar'
    SHOOTING_RANGE = 'Shooting Range', 'Shooting Range'
    TUCK_SHOP_MAIN = 'Tuck Shop (Main)', 'Tuck Shop (Main)'
    NIGHT_STAY = 'Night Stay', 'Night Stay'
    GROUP_EVENT = 'Group/Event', 'Group/Event'
    AUCTION = 'Auction', 'Auction'
