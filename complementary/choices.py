from django.db import models


class BillTypeChoices(models.TextChoices):
    QB_BILL = 'QB Bill', 'QB Bill'
    PARTIAL_BILL = 'Partial Bill', 'Partial Bill'
    WITHOUT_QT = 'Without QT', 'Without QT'
    ZOHO_FULL = 'Zoho Bill Full', 'Zoho Bill Full'


class HeadChoices(models.TextChoices):
    GOVT_OFFICIALS = 'Govt. Officials', 'Govt. Officials'
    MARKETING_PR = 'Marketing PR Bills', 'Marketing PR Bills'
    EXECUTIVE_PERSONALS = 'Executive Personals', 'Executive Personals'
    GUEST_COMPLAINT = 'Guest Complaint', 'Guest Complaint'
    EXECUTIVE_FAMILY = 'Executive Family / Home / Reference', 'Executive Family / Home / Reference'
    NIGHT_STAY = 'Night Stay', 'Night Stay'
    STAFF = 'Staff', 'Staff'
    VENDOR = 'Vendor', 'Vendor'
    GUEST = 'Guest', 'Guest'
    AUDITOR_NAEEM = 'Auditor - Naeem', 'Auditor - Naeem'
    MUSIC_TEAM_TEA = 'Music Team (Tea)', 'Music Team (Tea)'


class BillStatusChoices(models.TextChoices):
    PAID = 'Paid', 'Paid'
    PAID_DISCOUNT = 'Paid with Discount', 'Paid with Discount'
    PENDING = 'Pending', 'Pending'
    FREE = 'Free', 'Free'
    PACKAGE = 'Package Bill', 'Package Bill'


class DepartmentChoices(models.TextChoices):
    ALL = 'All Department', 'All Department'
    FB = 'F&B', 'F&B'
    WATERSPORTS = 'Watersports', 'Watersports'
    ADVENTURE = 'Adventure Activities', 'Adventure Activities'
    SHOOTING = 'Shooting Range', 'Shooting Range'
    EVENT = 'Event', 'Event'
    NIGHT_STAY = 'Night Stay', 'Night Stay'
    TUCK_SHOP = 'Tuck Shop', 'Tuck Shop'
