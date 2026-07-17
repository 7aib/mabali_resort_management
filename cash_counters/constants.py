from django.db import models


class VisitTypeChoices(models.TextChoices):
    PAID = "Paid", "Paid"
    COMPLEMENTARY = "Complementary", "Complementary"
    NIGHT_STAY = "Night Stay", "Night Stay"
    GROUP = "Group", "Group"
    DECOR_TEAM = "Decor team events", "Decor team events"


class GateChoices(models.TextChoices):
    MAIN = "Main Gate", "Main Gate"
    EVENT = "Event Gate", "Event Gate"
    LAKE_SIDE = "Lake Side gate", "Lake Side gate"


class StatusChoices(models.TextChoices):
    OLD = "Old", "Old"
    NEW = "New", "New"


class CitiesChoices(models.TextChoices):
    ISLAMABAD = "Islamabad", "Islamabad"
    RAWALPINDI = "Rawalpindi", "Rawalpindi"
    LAHORE = "Lahore", "Lahore"
    KARACHI = "Karachi", "Karachi"
    PESHAWAR = "Peshawar", "Peshawar"
    QUETTA = "Quetta", "Quetta"
    MULTAN = "Multan", "Multan"
    FAISALABAD = "Faisalabad", "Faisalabad"
    OTHER = "Other", "Other"


class PaymentMethodChoices(models.TextChoices):
    CASH = "Cash", "Cash"
    CARD = "Card", "Card"


class CounterTypeChoices(models.TextChoices):
    MAIN_RESTAURANT_LSR = "Main Restaurant LSR", "Main Restaurant LSR"
    ADVENTURE_AREA = "Adventure Area", "Adventure Area"
    RECEPTION = "Reception", "Reception"
    WATER_SPORTS = "Water Sports", "Water Sports"
    WATER_SPORT_TUCK_SHOP = "Water Sport Tuck Shop", "Water Sport Tuck Shop"
    EVENT_BAR = "Event Bar", "Event Bar"
    SHOOTING_RANGE = "Shooting Range", "Shooting Range"
    TUCK_SHOP_MAIN = "Tuck Shop (Main)", "Tuck Shop (Main)"
    NIGHT_STAY = "Night Stay", "Night Stay"
    GROUP_EVENT = "Group/Event", "Group/Event"
    AUCTION = "Auction", "Auction"


class TicketRefundReasonChoices(models.TextChoices):
    WEATHER = "Weather Cancellation", "Weather Cancellation"
    RESTAURANT_TAX = "Restaurant 6% Tax Paid Online", "Restaurant 6% Tax Paid Online"
    OTHER = "Other", "Other"
