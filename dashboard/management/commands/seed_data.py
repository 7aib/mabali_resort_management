"""Management command to seed test data for dashboard verification."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from authentication.choices import UserRoles
from cash_counters.constants import (
    CitiesChoices,
    GateChoices,
    PaymentMethodChoices,
    StatusChoices,
    VisitTypeChoices,
)
from cash_counters.models import EntryCounterForm, EntryTransaction, TicketRefund
from complementary.choices import (
    BillStatusChoices,
    BillTypeChoices,
    DepartmentChoices,
    HeadChoices,
)
from complementary.models import FreeBilling
from finance.constants import CounterTypeChoices, POSPaymentMethodChoices
from finance.models import POS
from inventory.choices import (
    AmmoPaymentChoices,
    AssetCategoryChoices,
    StockStatusChoices,
)
from inventory.models import AmmoTransactionLog, FuelTransactionLog, InventoryItem
from reservations.choices import PaymentTypeChoices, ReservationStatusChoices
from reservations.models import Reservation, Room

User = get_user_model()


class Command(BaseCommand):
    help = "Seed test data for dashboard verification"

    def handle(self, *args, **options):
        self.stdout.write("Seeding test data...")

        # Create users if they don't exist
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@mabali.com",
                "role": UserRoles.CEO,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()

        cashier, _ = User.objects.get_or_create(
            username="cashier1",
            defaults={
                "email": "cashier@mabali.com",
                "role": UserRoles.CASHIER,
                "first_name": "Ahmed",
                "last_name": "Khan",
            },
        )

        accountant, _ = User.objects.get_or_create(
            username="accountant1",
            defaults={
                "email": "accountant@mabali.com",
                "role": UserRoles.ACCOUNTANT,
                "first_name": "Sara",
                "last_name": "Ali",
            },
        )

        # Create rooms
        rooms_data = [
            ("Hut 1", "hut", 5000),
            ("Hut 2", "hut", 5000),
            ("Hut 3", "hut", 5000),
            ("Suite 1", "suite", 12000),
            ("Suite 2", "suite", 12000),
            ("Room 1", "room", 8000),
            ("Room 2", "room", 8000),
            ("Room 3", "room", 8000),
            ("Room 4", "room", 8000),
            ("Honeymoon 1", "honeymoon", 15000),
            ("Honeymoon 2", "honeymoon", 15000),
        ]
        for name, category, rate in rooms_data:
            Room.objects.get_or_create(
                name=name, defaults={"category": category, "rate_per_night": rate}
            )

        # Create reservations
        today = date.today()
        Reservation.objects.get_or_create(
            customer=admin_user,
            room=Room.objects.get(name="Suite 1"),
            defaults={
                "check_in_date": today,
                "check_out_date": today + timedelta(days=2),
                "guest_name": "Ali Raza",
                "phone_number": "+923001234567",
                "no_of_adults": 2,
                "status": ReservationStatusChoices.CONFIRMED,
                "payment_type": PaymentTypeChoices.ADVANCE,
                "advance_amount": 10000,
                "amount_received": 24000,
                "created_by": admin_user,
            },
        )

        # Create inventory items
        items_data = [
            ("Petrol", "fuel", 500, "liters", "Shell"),
            ("Diesel", "fuel", 300, "liters", "Total"),
            ("9mm Ammo", "ammo", 1000, "rounds", "Police Dept"),
            ("12 Gauge Shells", "ammo", 200, "rounds", "Police Dept"),
            ("Generator Oil", "generator", 50, "liters", "Shell"),
            ("First Aid Kit", "equipment", 20, "units", "Medical Supply"),
        ]
        for name, category, stock, unit, supplier in items_data:
            InventoryItem.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "stock_quantity": stock,
                    "unit": unit,
                    "supplier": supplier,
                },
            )

        # Create fuel transactions
        FuelTransactionLog.objects.get_or_create(
            inventory_item=InventoryItem.objects.get(name="Petrol"),
            quantity=50,
            defaults={
                "transaction_status": StockStatusChoices.ISSUED,
                "amount": 5000,
                "issued_to": InventoryItem.objects.get(name="Petrol"),
                "created_by": admin_user,
            },
        )

        # Create ammo transactions
        AmmoTransactionLog.objects.get_or_create(
            inventory_item=InventoryItem.objects.get(name="9mm Ammo"),
            quantity=100,
            defaults={
                "transaction_status": StockStatusChoices.ISSUED,
                "payment": AmmoPaymentChoices.FREE,
                "amount": 0,
                "created_by": admin_user,
            },
        )

        # Create guest entries
        for i in range(5):
            entry = EntryCounterForm.objects.create(
                customer=cashier,
                location=CitiesChoices.ISLAMABAD,
                no_of_persons=2 + (i % 3),
                no_of_persons_kids=i % 2,
                visit_type=VisitTypeChoices.PAID,
                gate=GateChoices.MAIN,
                status=StatusChoices.NEW if i < 3 else StatusChoices.OLD,
            )
            EntryTransaction.objects.create(
                entry_form=entry,
                amount=1000 * (2 + (i % 3)),
                payment_method=PaymentMethodChoices.CASH,
            )

        # Create POS entries
        for i in range(3):
            POS.objects.get_or_create(
                date=today,
                counter_type=(
                    CounterTypeChoices.MAIN_GATE
                    if i == 0
                    else CounterTypeChoices.RESTAURANT
                ),
                amount=15000 + (i * 5000),
                defaults={
                    "payment_method": POSPaymentMethodChoices.CASH,
                    "remarks": "Test entry %d" % (i + 1),
                },
            )

        # Create free billing entries
        FreeBilling.objects.get_or_create(
            guest_name="VIP Guest",
            defaults={
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.FREE,
                "department": DepartmentChoices.ALL,
                "total_bill_amount": 5000,
                "discount_amount": 5000,
            },
        )

        # Create ticket refunds
        TicketRefund.objects.get_or_create(
            defaults={
                "no_of_tickets": 5,
                "rate_per_ticket": 1000,
                "total_amount_refunded": 5000,
                "reason": "Weather Cancellation",
                "remarks": "Rainy day - full refund",
            }
        )

        self.stdout.write(self.style.SUCCESS("Test data seeded successfully!"))
        self.stdout.write("Login with: admin / admin123")
