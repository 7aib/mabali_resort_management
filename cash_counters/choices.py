from django.db import models

class CounterType(models.TextChoices):
    COUNTER_1 = "counter_1", "Counter 1"
    COUNTER_2 = "counter_2", "Counter 2"
    COUNTER_3 = "counter_3", "Counter 3"
    OTHER = "other", "Other"