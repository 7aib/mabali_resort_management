from decimal import Decimal
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from authentication.choices import UserRoles
from cash_counters.models import (
    EntryCounterForm, EntryTransaction, CashHandover, CashRegister, TicketRefund,
)
from cash_counters.constants import (
    VisitTypeChoices, GateChoices, StatusChoices, CitiesChoices,
    PaymentMethodChoices as CCPaymentMethod, CounterTypeChoices as CCCounterType,
    TicketRefundReasonChoices,
)
from finance.models import POS
from finance.constants import POSPaymentMethodChoices, CounterTypeChoices as FinCounterType
from complementary.models import FreeBilling
from complementary.choices import BillTypeChoices, HeadChoices, BillStatusChoices, DepartmentChoices
from reservations.models import Room, Reservation
from reservations.choices import ReservationStatusChoices, RoomCategoryChoices
from inventory.models import FuelTransactionLog, AmmoTransactionLog, InventoryItem
from inventory.choices import StockStatusChoices, AssetCategoryChoices
from mabali_resort_management.constants import PAID_VISIT_PRICE

User = get_user_model()


# ═══════════════════════════════════════════════════════
# PERMISSION TESTS
# ═══════════════════════════════════════════════════════

class DashboardPermissionTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard')
        self.ceo = User.objects.create_user(
            username='dash_ceo', password='pass123', role=UserRoles.CEO
        )
        self.acc = User.objects.create_user(
            username='dash_acc', password='pass123', role=UserRoles.ACCOUNTANT
        )
        self.hr = User.objects.create_user(
            username='dash_hr', password='pass123', role=UserRoles.HR_MANAGER
        )
        self.mc = User.objects.create_user(
            username='dash_mc', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.cashier = User.objects.create_user(
            username='dash_cashier', password='pass123', role=UserRoles.CASHIER
        )
        self.customer = User.objects.create_user(
            username='dash_cust', password='pass123', role=UserRoles.CUSTOMER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse('login') + '?next=/dashboard',
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username='dash_ceo', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_accountant_can_access(self):
        self.client.login(username='dash_acc', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_hr_manager_can_access(self):
        self.client.login(username='dash_hr', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_main_cashier_cannot_access(self):
        self.client.login(username='dash_mc', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_cashier_cannot_access(self):
        self.client.login(username='dash_cashier', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_customer_cannot_access(self):
        self.client.login(username='dash_cust', password='pass123')
        self.assertEqual(self.client.get(self.url).status_code, 403)


# ═══════════════════════════════════════════════════════
# CONTEXT KEYS TEST
# ═══════════════════════════════════════════════════════

class DashboardContextKeysTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_ctx', password='pass123', role=UserRoles.CEO
        )
        self.client.login(username='dash_ctx', password='pass123')
        self.response = self.client.get(reverse('dashboard'))
        self.ctx = self.response.context

    def test_template_used(self):
        self.assertTemplateUsed(self.response, 'dashboard/index.html')

    def test_today_in_context(self):
        self.assertEqual(self.ctx['today'], timezone.localdate())

    def test_pos_keys(self):
        for key in ['pos_by_counter', 'pos_with_cashier', 'total_pos_today']:
            self.assertIn(key, self.ctx)

    def test_guest_keys(self):
        for key in ['total_adults', 'total_kids', 'total_guests', 'new_guests', 'old_guests',
                     'guest_entries_detail', 'visit_breakdown']:
            self.assertIn(key, self.ctx)

    def test_revenue_keys(self):
        for key in ['entry_revenue', 'cash_counter_revenue', 'total_cash_register',
                     'cash_register_count', 'total_cash_handover', 'cash_handover_count',
                     'free_billing_total', 'refund_total']:
            self.assertIn(key, self.ctx)

    def test_room_keys(self):
        for key in ['total_rooms', 'occupied_count', 'reserved_count', 'available_count',
                     'occupied_rooms', 'reserved_rooms', 'active_reservations',
                     'today_checkins', 'today_checkouts', 'night_stay_revenue']:
            self.assertIn(key, self.ctx)

    def test_other_keys(self):
        for key in ['trust_amounts', 'total_trust_amount', 'free_bills', 'free_bill_count',
                     'events_today', 'event_count', 'expense_items', 'total_expenses',
                     'pending_orders', 'refunds_today', 'refund_count',
                     'recent_transactions', 'total_guests_all', 'total_pos_all',
                     'total_reservations', 'can_view_amounts', 'avg_spending_per_person']:
            self.assertIn(key, self.ctx)


# ═══════════════════════════════════════════════════════
# POS COMPUTATION TESTS
# ═══════════════════════════════════════════════════════

class DashboardPOSTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_pos', password='pass123', role=UserRoles.CEO
        )
        self.client.login(username='dash_pos', password='pass123')

    def test_pos_total_today(self):
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('10000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        POS.objects.create(
            counter_type=FinCounterType.SHOOTING_RANGE,
            amount=Decimal('5000.00'),
            payment_method=POSPaymentMethodChoices.IBFT,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_pos_today'], Decimal('15000.00'))

    def test_pos_excludes_water_sports(self):
        POS.objects.create(
            counter_type=FinCounterType.WATER_SPORTS,
            amount=Decimal('20000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('5000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_pos_today'], Decimal('5000.00'))

    def test_pos_by_counter_grouped(self):
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('3000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('2000.00'),
            payment_method=POSPaymentMethodChoices.CREDIT_CARD,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(len(ctx['pos_by_counter']), 1)
        self.assertEqual(ctx['pos_by_counter'][0]['total'], Decimal('5000.00'))

    def test_pos_excludes_other_days(self):
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('10000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
            date=timezone.localdate() - timedelta(days=1),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_pos_today'], 0)


# ═══════════════════════════════════════════════════════
# GUEST STATS TESTS
# ═══════════════════════════════════════════════════════

class DashboardGuestStatsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_guest', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_g', password='pass123', role=UserRoles.CUSTOMER,
            first_name='Ali'
        )
        self.client.login(username='dash_guest', password='pass123')

    def test_guest_counts(self):
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=3, no_of_kids=1,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2, no_of_kids=0,
            visit_type=VisitTypeChoices.COMPLEMENTARY, gate=GateChoices.MAIN,
            status=StatusChoices.OLD,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_adults'], 5)
        self.assertEqual(ctx['total_kids'], 1)
        self.assertEqual(ctx['total_guests'], 6)
        self.assertEqual(ctx['new_guests'], 1)
        self.assertEqual(ctx['old_guests'], 1)

    def test_visit_breakdown(self):
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=3,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=1,
            visit_type=VisitTypeChoices.GROUP, gate=GateChoices.EVENT,
            status=StatusChoices.NEW,
        )
        ctx = self.client.get(reverse('dashboard')).context
        breakdown = {v['visit_type']: v['count'] for v in ctx['visit_breakdown']}
        self.assertEqual(breakdown[VisitTypeChoices.PAID], 2)
        self.assertEqual(breakdown[VisitTypeChoices.GROUP], 1)

    def test_empty_guests(self):
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_guests'], 0)
        self.assertEqual(ctx['new_guests'], 0)
        self.assertEqual(ctx['old_guests'], 0)


# ═══════════════════════════════════════════════════════
# REVENUE TESTS
# ═══════════════════════════════════════════════════════

class DashboardRevenueTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_rev', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_r', password='pass123', role=UserRoles.CUSTOMER
        )
        self.client.login(username='dash_rev', password='pass123')

    def test_entry_revenue(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryTransaction.objects.create(
            entry_form=entry, amount=Decimal('3000.00'),
            payment_method=CCPaymentMethod.CASH,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['entry_revenue'], Decimal('3000.00'))
        self.assertEqual(ctx['cash_counter_revenue'], Decimal('3000.00'))

    def test_cash_register_total(self):
        mc = User.objects.create_user(
            username='mc_rev', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        CashRegister.objects.create(
            counter_type=CCCounterType.RECEPTION,
            amount_received=Decimal('50000.00'),
            received_from=self.customer,
            on_duty_cashier=mc,
        )
        CashRegister.objects.create(
            counter_type=CCCounterType.SHOOTING_RANGE,
            amount_received=Decimal('25000.00'),
            received_from=self.customer,
            on_duty_cashier=mc,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_cash_register'], Decimal('75000.00'))
        self.assertEqual(ctx['cash_register_count'], 2)

    def test_cash_handover_total(self):
        mc = User.objects.create_user(
            username='mc_ho', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        CashHandover.objects.create(
            counter_type=CCCounterType.RECEPTION,
            cashier=self.customer,
            cash_amount=Decimal('30000.00'),
            handover_to=mc,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_cash_handover'], Decimal('30000.00'))
        self.assertEqual(ctx['cash_handover_count'], 1)

    def test_avg_spending_per_person(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryTransaction.objects.create(
            entry_form=entry, amount=Decimal('3000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['avg_spending_per_person'], Decimal('1500.00'))

    def test_avg_spending_zero_guests(self):
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['avg_spending_per_person'], Decimal('0'))


# ═══════════════════════════════════════════════════════
# FREE BILLING / REFUNDS / EXPENSES TESTS
# ═══════════════════════════════════════════════════════

class DashboardFreeBillingTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_fb', password='pass123', role=UserRoles.CEO
        )
        self.client.login(username='dash_fb', password='pass123')

    def test_free_billing_totals(self):
        FreeBilling.objects.create(
            guest_name='Guest 1', bill_type=BillTypeChoices.QB_BILL,
            head=HeadChoices.GUEST, bill_status=BillStatusChoices.PAID,
            department=DepartmentChoices.ALL,
            total_bill_amount=Decimal('10000.00'),
            discount_amount=Decimal('1500.00'),
        )
        FreeBilling.objects.create(
            guest_name='Guest 2', bill_type=BillTypeChoices.WITHOUT_QT,
            head=HeadChoices.STAFF, bill_status=BillStatusChoices.FREE,
            department=DepartmentChoices.FB,
            total_bill_amount=Decimal('5000.00'),
            discount_amount=Decimal('500.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['free_billing_total'], Decimal('15000.00'))
        self.assertEqual(ctx['free_bills_total'], Decimal('15000.00'))
        self.assertEqual(ctx['free_bills_discount'], Decimal('2000.00'))
        self.assertEqual(ctx['free_bill_count'], 2)

    def test_ticket_refund_total(self):
        TicketRefund.objects.create(
            no_of_tickets=5, rate_per_ticket=Decimal('1500.00'),
            total_amount_refunded=Decimal('7500.00'),
            reason=TicketRefundReasonChoices.WEATHER,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['refund_total'], Decimal('7500.00'))
        self.assertEqual(ctx['refund_count'], 1)

    def test_total_expenses(self):
        TicketRefund.objects.create(
            total_amount_refunded=Decimal('3000.00'),
            reason=TicketRefundReasonChoices.OTHER,
        )
        FreeBilling.objects.create(
            total_bill_amount=Decimal('7000.00'),
            head=HeadChoices.GUEST,
            department=DepartmentChoices.ALL,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_expenses'], Decimal('10000.00'))


# ═══════════════════════════════════════════════════════
# ROOM STATS TESTS
# ═══════════════════════════════════════════════════════

class DashboardRoomStatsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_room', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_rm', password='pass123', role=UserRoles.CUSTOMER,
            first_name='RoomGuest'
        )
        self.room = Room.objects.create(
            name='Hut 1', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.room2 = Room.objects.create(
            name='Suite 1', category=RoomCategoryChoices.SUITE,
            rate_per_night=Decimal('20000.00'),
        )
        self.client.login(username='dash_room', password='pass123')

    def test_total_rooms(self):
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_rooms'], 2)

    def test_occupied_room(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='RoomGuest', no_of_adults=2,
            check_in_date=today, check_out_date=today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CHECKED_IN,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['occupied_count'], 1)
        self.assertEqual(ctx['available_count'], 1)

    def test_reserved_room(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='RoomGuest', no_of_adults=2,
            check_in_date=today + timedelta(days=3),
            check_out_date=today + timedelta(days=5),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['reserved_count'], 1)
        self.assertEqual(ctx['available_count'], 1)

    def test_check_in_today(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='RoomGuest', no_of_adults=2,
            check_in_date=today,
            check_out_date=today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['today_checkins'].count(), 1)

    def test_check_out_today(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='RoomGuest', no_of_adults=2,
            check_in_date=today - timedelta(days=2),
            check_out_date=today,
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CHECKED_IN,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['today_checkouts'].count(), 1)


# ═══════════════════════════════════════════════════════
# TRUST AMOUNT TEST
# ═══════════════════════════════════════════════════════

class DashboardTrustAmountTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_trust', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_tr', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(
            name='Hut Trust', category=RoomCategoryChoices.HUT,
        )
        self.client.login(username='dash_trust', password='pass123')

    def test_trust_amount_today(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='TrustGuest', no_of_adults=2,
            check_in_date=today + timedelta(days=1),
            check_out_date=today + timedelta(days=3),
            advance_amount=Decimal('25000.00'),
            advance_date=today,
            rate_per_night=Decimal('10000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_trust_amount'], Decimal('25000.00'))

    def test_trust_excludes_other_days(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='OldTrust', no_of_adults=2,
            check_in_date=yesterday + timedelta(days=1),
            check_out_date=yesterday + timedelta(days=3),
            advance_amount=Decimal('10000.00'),
            advance_date=yesterday,
            rate_per_night=Decimal('10000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_trust_amount'], 0)

    def test_trust_excludes_zero_advance(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='NoAdvance', no_of_adults=2,
            check_in_date=today + timedelta(days=1),
            check_out_date=today + timedelta(days=3),
            advance_amount=Decimal('0'),
            rate_per_night=Decimal('10000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_trust_amount'], 0)


# ═══════════════════════════════════════════════════════
# INVENTORY ALERTS TEST
# ═══════════════════════════════════════════════════════

class DashboardInventoryAlertsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_inv', password='pass123', role=UserRoles.CEO
        )
        self.fuel = InventoryItem.objects.create(
            name='Petrol', category=AssetCategoryChoices.FUEL,
            stock_quantity=Decimal('1000'),
        )
        self.client.login(username='dash_inv', password='pass123')

    def test_pending_orders_count(self):
        FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal('100'),
        )
        FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal('200'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['pending_orders'], 2)

    def test_pending_orders_excludes_non_required(self):
        FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.ISSUED,
            quantity=Decimal('100'),
        )
        FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal('50'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['pending_orders'], 1)


# ═══════════════════════════════════════════════════════
# ALL-TIME STATS TEST
# ═══════════════════════════════════════════════════════

class DashboardAllTimeStatsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_all', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_all', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(
            name='Room All', category=RoomCategoryChoices.ROOM,
        )
        self.client.login(username='dash_all', password='pass123')

    def test_total_guests_all(self):
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=3,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2,
            visit_type=VisitTypeChoices.COMPLEMENTARY, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_guests_all'], 2)

    def test_total_pos_all(self):
        POS.objects.create(
            counter_type=FinCounterType.RECEPTION,
            amount=Decimal('5000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        POS.objects.create(
            counter_type=FinCounterType.SHOOTING_RANGE,
            amount=Decimal('3000.00'),
            payment_method=POSPaymentMethodChoices.CASH,
            date=timezone.localdate() - timedelta(days=5),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_pos_all'], Decimal('8000.00'))

    def test_total_reservations(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Res 1', no_of_adults=2,
            check_in_date=today, check_out_date=today + timedelta(days=1),
            rate_per_night=Decimal('10000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['total_reservations'], 1)


# ═══════════════════════════════════════════════════════
# PERMISSION VISIBILITY TEST
# ═══════════════════════════════════════════════════════

class DashboardCanViewAmountsTest(TestCase):

    def setUp(self):
        self.client = Client()

    def _get_can_view(self, role):
        user = User.objects.create_user(
            username=f'cva_{role}', password='pass123', role=role
        )
        self.client.login(username=f'cva_{role}', password='pass123')
        ctx = self.client.get(reverse('dashboard')).context
        self.client.logout()
        return ctx['can_view_amounts']

    def test_ceo_can_view(self):
        self.assertTrue(self._get_can_view(UserRoles.CEO))

    def test_accountant_can_view(self):
        self.assertTrue(self._get_can_view(UserRoles.ACCOUNTANT))

    def test_hr_manager_can_view(self):
        self.assertTrue(self._get_can_view(UserRoles.HR_MANAGER))


# ═══════════════════════════════════════════════════════
# EVENTS TEST
# ═══════════════════════════════════════════════════════

class DashboardEventsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_evt', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_evt', password='pass123', role=UserRoles.CUSTOMER,
            first_name='EventGuest'
        )
        self.client.login(username='dash_evt', password='pass123')

    def test_group_event_appears(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=10,
            visit_type=VisitTypeChoices.GROUP, gate=GateChoices.EVENT,
            status=StatusChoices.NEW, location=CitiesChoices.ISLAMABAD,
        )
        EntryTransaction.objects.create(
            entry_form=entry, amount=Decimal('15000.00'),
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['event_count'], 1)
        self.assertEqual(ctx['events_today'][0]['amount'], Decimal('15000.00'))

    def test_decor_team_event_appears(self):
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=5,
            visit_type=VisitTypeChoices.DECOR_TEAM, gate=GateChoices.EVENT,
            status=StatusChoices.NEW,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['event_count'], 1)

    def test_paid_entry_not_counted_as_event(self):
        EntryCounterForm.objects.create(
            customer=self.customer, no_of_persons=2,
            visit_type=VisitTypeChoices.PAID, gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['event_count'], 0)


# ═══════════════════════════════════════════════════════
# NIGHT STAY REVENUE TEST
# ═══════════════════════════════════════════════════════

class DashboardNightStayTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dash_ns', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='cust_ns', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(
            name='Hut NS', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('15000.00'),
        )
        self.client.login(username='dash_ns', password='pass123')

    def test_night_stay_revenue(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='NightGuest', no_of_adults=2,
            check_in_date=today - timedelta(days=1),
            check_out_date=today + timedelta(days=1),
            rate_per_night=Decimal('15000.00'),
            status=ReservationStatusChoices.CHECKED_IN,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['night_stay_revenue'], Decimal('15000.00'))

    def test_night_stay_excludes_checked_out(self):
        today = timezone.localdate()
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='CheckedOut', no_of_adults=2,
            check_in_date=today - timedelta(days=2),
            check_out_date=today - timedelta(days=1),
            rate_per_night=Decimal('15000.00'),
            status=ReservationStatusChoices.CHECKED_OUT,
        )
        ctx = self.client.get(reverse('dashboard')).context
        self.assertEqual(ctx['night_stay_revenue'], 0)
