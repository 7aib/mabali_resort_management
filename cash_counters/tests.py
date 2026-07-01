from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from authentication.choices import UserRoles
from mabali_resort_management.constants import PAID_VISIT_PRICE
from .models import (
    EntryCounterForm, EntryTransaction, CashHandover,
    CashRegister, TicketRefund,
)
from .constants import (
    VisitTypeChoices, GateChoices, StatusChoices,
    CitiesChoices, PaymentMethodChoices, CounterTypeChoices,
    TicketRefundReasonChoices,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════

class EntryCounterFormModelTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username='cust1', password='pass123', role=UserRoles.CUSTOMER,
            first_name='Ali', phone_number='+923011111111'
        )

    def test_create_entry(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            location=CitiesChoices.ISLAMABAD,
            no_of_persons=3,
            no_of_kids=1,
            visit_type=VisitTypeChoices.PAID,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        self.assertEqual(entry.customer, self.customer)
        self.assertEqual(entry.no_of_persons, 3)
        self.assertEqual(entry.no_of_kids, 1)
        self.assertEqual(entry.visit_type, VisitTypeChoices.PAID)
        self.assertEqual(entry.status, StatusChoices.NEW)
        self.assertEqual(entry.location, CitiesChoices.ISLAMABAD)
        self.assertEqual(entry.gate, GateChoices.MAIN)

    def test_str(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            no_of_persons=2,
            visit_type=VisitTypeChoices.PAID,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        result = str(entry)
        self.assertIn('Ali', result)
        self.assertIn('Paid', result)

    def test_str_fallback_to_username(self):
        self.customer.first_name = ''
        self.customer.save()
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            no_of_persons=1,
            visit_type=VisitTypeChoices.COMPLEMENTARY,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        self.assertIn('cust1', str(entry))

    def test_defaults(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            status=StatusChoices.NEW,
        )
        self.assertEqual(entry.no_of_persons, 1)
        self.assertEqual(entry.no_of_kids, 0)
        self.assertEqual(entry.visit_type, VisitTypeChoices.PAID)
        self.assertEqual(entry.gate, GateChoices.MAIN)
        self.assertEqual(entry.location, CitiesChoices.OTHER)

    def test_soft_delete_fields_exist(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            status=StatusChoices.NEW,
        )
        self.assertFalse(entry.is_deleted)
        self.assertIsNone(entry.deleted_at)

    def test_timestamps_exist(self):
        entry = EntryCounterForm.objects.create(
            customer=self.customer,
            status=StatusChoices.NEW,
        )
        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)


class EntryTransactionModelTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username='cust2', password='pass123', role=UserRoles.CUSTOMER,
            first_name='Sara'
        )
        self.entry = EntryCounterForm.objects.create(
            customer=self.customer,
            no_of_persons=2,
            visit_type=VisitTypeChoices.PAID,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )

    def test_create_transaction(self):
        tx = EntryTransaction.objects.create(
            entry_form=self.entry,
            amount=Decimal('3000.00'),
            payment_method=PaymentMethodChoices.CASH,
        )
        self.assertEqual(tx.entry_form, self.entry)
        self.assertEqual(tx.amount, Decimal('3000.00'))
        self.assertEqual(tx.payment_method, PaymentMethodChoices.CASH)

    def test_str(self):
        tx = EntryTransaction.objects.create(
            entry_form=self.entry,
            amount=Decimal('3000.00'),
            payment_method=PaymentMethodChoices.CARD,
        )
        result = str(tx)
        self.assertIn('Sara', result)
        self.assertIn('3000', result)
        self.assertIn('Card', result)

    def test_one_to_one_constraint(self):
        EntryTransaction.objects.create(
            entry_form=self.entry,
            amount=Decimal('3000.00'),
            payment_method=PaymentMethodChoices.CASH,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            EntryTransaction.objects.create(
                entry_form=self.entry,
                amount=Decimal('1500.00'),
                payment_method=PaymentMethodChoices.CASH,
            )

    def test_default_payment_method(self):
        tx = EntryTransaction.objects.create(
            entry_form=self.entry,
            amount=Decimal('1500.00'),
        )
        self.assertEqual(tx.payment_method, PaymentMethodChoices.CASH)


class CashHandoverModelTest(TestCase):

    def setUp(self):
        self.cashier = User.objects.create_user(
            username='cashier1', password='pass123', role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username='mc1', password='pass123', role=UserRoles.MAIN_CASHIER
        )

    def test_create_handover(self):
        ho = CashHandover.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('50000.00'),
            handover_to=self.main_cashier,
            notes='End of shift',
        )
        self.assertEqual(ho.cashier, self.cashier)
        self.assertEqual(ho.handover_to, self.main_cashier)
        self.assertEqual(ho.cash_amount, Decimal('50000.00'))
        self.assertEqual(ho.counter_type, CounterTypeChoices.RECEPTION)

    def test_str(self):
        ho = CashHandover.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('50000.00'),
            handover_to=self.main_cashier,
        )
        result = str(ho)
        self.assertIn('50000', result)
        self.assertIn('Reception', result)

    def test_default_date(self):
        ho = CashHandover.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('10000.00'),
            handover_to=self.main_cashier,
        )
        self.assertEqual(ho.date, timezone.localdate())

    def test_ordering(self):
        ho1 = CashHandover.objects.create(
            date=timezone.localdate() - timedelta(days=1),
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('10000.00'),
            handover_to=self.main_cashier,
        )
        ho2 = CashHandover.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.ADVENTURE_AREA,
            cashier=self.cashier,
            cash_amount=Decimal('20000.00'),
            handover_to=self.main_cashier,
        )
        handovers = list(CashHandover.objects.all())
        self.assertEqual(handovers[0].pk, ho2.pk)
        self.assertEqual(handovers[1].pk, ho1.pk)

    def test_optional_notes(self):
        ho = CashHandover.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('5000.00'),
            handover_to=self.main_cashier,
        )
        self.assertIsNone(ho.notes)


class CashRegisterModelTest(TestCase):

    def setUp(self):
        self.cashier = User.objects.create_user(
            username='cashier2', password='pass123', role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username='mc2', password='pass123', role=UserRoles.MAIN_CASHIER
        )

    def test_create_entry(self):
        cr = CashRegister.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.MAIN_RESTAURANT_LSR,
            amount_received=Decimal('75000.00'),
            received_from=self.cashier,
            on_duty_cashier=self.main_cashier,
            notes='Morning shift',
        )
        self.assertEqual(cr.amount_received, Decimal('75000.00'))
        self.assertEqual(cr.received_from, self.cashier)
        self.assertEqual(cr.on_duty_cashier, self.main_cashier)

    def test_str(self):
        cr = CashRegister.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.MAIN_RESTAURANT_LSR,
            amount_received=Decimal('75000.00'),
            received_from=self.cashier,
            on_duty_cashier=self.main_cashier,
        )
        result = str(cr)
        self.assertIn('75000', result)
        self.assertIn('Main Restaurant LSR', result)

    def test_default_date(self):
        cr = CashRegister.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount_received=Decimal('10000.00'),
            received_from=self.cashier,
            on_duty_cashier=self.main_cashier,
        )
        self.assertEqual(cr.date, timezone.localdate())

    def test_verbose_name_plural(self):
        self.assertEqual(
            CashRegister._meta.verbose_name_plural, 'Cash Register entries'
        )


class TicketRefundModelTest(TestCase):

    def test_create_refund(self):
        refund = TicketRefund.objects.create(
            date=timezone.localdate(),
            no_of_tickets=5,
            rate_per_ticket=Decimal('1500.00'),
            total_amount_refunded=Decimal('7500.00'),
            reason=TicketRefundReasonChoices.WEATHER,
            remarks='Heavy rain',
        )
        self.assertEqual(refund.no_of_tickets, 5)
        self.assertEqual(refund.total_amount_refunded, Decimal('7500.00'))

    def test_str(self):
        refund = TicketRefund.objects.create(
            date=timezone.localdate(),
            no_of_tickets=3,
            rate_per_ticket=Decimal('1500.00'),
            total_amount_refunded=Decimal('4500.00'),
            reason=TicketRefundReasonChoices.OTHER,
        )
        result = str(refund)
        self.assertIn('3', result)
        self.assertIn('4500', result)

    def test_defaults(self):
        refund = TicketRefund.objects.create()
        self.assertEqual(refund.no_of_tickets, 1)
        self.assertEqual(refund.rate_per_ticket, Decimal('0'))
        self.assertEqual(refund.total_amount_refunded, Decimal('0'))
        self.assertEqual(refund.reason, TicketRefundReasonChoices.WEATHER)
        self.assertEqual(refund.remarks, '')

    def test_ordering(self):
        r1 = TicketRefund.objects.create(
            date=timezone.localdate() - timedelta(days=1),
            no_of_tickets=1,
            total_amount_refunded=Decimal('1500.00'),
        )
        r2 = TicketRefund.objects.create(
            date=timezone.localdate(),
            no_of_tickets=2,
            total_amount_refunded=Decimal('3000.00'),
        )
        refunds = list(TicketRefund.objects.all())
        self.assertEqual(refunds[0].pk, r2.pk)
        self.assertEqual(refunds[1].pk, r1.pk)

    def test_verbose_name_plural(self):
        self.assertEqual(
            TicketRefund._meta.verbose_name_plural, 'Ticket Refunds'
        )


# ═══════════════════════════════════════════════════════
# VIEW HELPER TESTS
# ═══════════════════════════════════════════════════════

class DailySalesViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1', password='pass123', role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:daily_sales'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/daily-sales/', fetch_redirect_response=False)

    def test_get_returns_200(self):
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('cash_counters:daily_sales'))
        self.assertEqual(response.status_code, 200)

    def test_shows_today_entries(self):
        self.client.login(username='user1', password='pass123')
        customer = User.objects.create_user(
            username='cust3', password='pass123', role=UserRoles.CUSTOMER
        )
        entry = EntryCounterForm.objects.create(
            customer=customer,
            no_of_persons=2,
            visit_type=VisitTypeChoices.PAID,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        response = self.client.get(reverse('cash_counters:daily_sales'))
        self.assertIn(entry, response.context['daily_entries'])

    def test_excludes_other_days_entries(self):
        self.client.login(username='user1', password='pass123')
        customer = User.objects.create_user(
            username='cust4', password='pass123', role=UserRoles.CUSTOMER
        )
        from django.utils import timezone
        entry = EntryCounterForm.objects.create(
            customer=customer,
            no_of_persons=2,
            visit_type=VisitTypeChoices.PAID,
            gate=GateChoices.MAIN,
            status=StatusChoices.NEW,
        )
        # Simulate old entry by updating created_at
        old_date = timezone.now() - timedelta(days=5)
        EntryCounterForm.objects.filter(pk=entry.pk).update(created_at=old_date)
        response = self.client.get(reverse('cash_counters:daily_sales'))
        self.assertNotIn(entry, response.context['daily_entries'])


class EntryFormViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user2', password='pass123', role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:entry_form'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/new-guest-entry/', fetch_redirect_response=False)

    def test_get_returns_200(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.get(reverse('cash_counters:entry_form'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cash_counters/entry_form.html')

    def test_get_shows_context(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.get(reverse('cash_counters:entry_form'))
        self.assertIn('cities', response.context)
        self.assertIn('visit_types', response.context)
        self.assertIn('gates', response.context)
        self.assertIn('payment_methods', response.context)
        self.assertIn('paid_price', response.context)
        self.assertEqual(response.context['paid_price'], PAID_VISIT_PRICE)

    def test_post_paid_visit_creates_entry_and_transaction(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923012345678',
            'name': 'Ahmed',
            'location': CitiesChoices.ISLAMABAD,
            'no_of_persons': 3,
            'no_of_kids': 0,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
            'payment_method': PaymentMethodChoices.CASH,
        })
        self.assertRedirects(response, reverse('cash_counters:entry_form'), fetch_redirect_response=False)

        customer = User.objects.get(phone_number='+923012345678')
        self.assertEqual(customer.first_name, 'Ahmed')
        self.assertEqual(customer.role, UserRoles.CUSTOMER)

        entry = EntryCounterForm.objects.get(customer=customer)
        self.assertEqual(entry.status, StatusChoices.NEW)
        self.assertEqual(entry.no_of_persons, 3)

        tx = EntryTransaction.objects.get(entry_form=entry)
        self.assertEqual(tx.amount, Decimal(str(PAID_VISIT_PRICE * 3)))
        self.assertEqual(tx.payment_method, PaymentMethodChoices.CASH)

    def test_post_complementary_no_transaction(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923098765432',
            'name': 'Zara',
            'location': CitiesChoices.LAHORE,
            'no_of_persons': 2,
            'no_of_kids': 1,
            'visit_type': VisitTypeChoices.COMPLEMENTARY,
            'gate': GateChoices.LAKE_SIDE,
        })
        self.assertRedirects(response, reverse('cash_counters:entry_form'), fetch_redirect_response=False)

        customer = User.objects.get(phone_number='+923098765432')
        entry = EntryCounterForm.objects.get(customer=customer)
        self.assertEqual(entry.visit_type, VisitTypeChoices.COMPLEMENTARY)
        self.assertFalse(EntryTransaction.objects.filter(entry_form=entry).exists())

    def test_post_existing_customer_sets_old_status(self):
        self.client.login(username='user2', password='pass123')
        customer = User.objects.create_user(
            username='existing_cust', password='pass123',
            role=UserRoles.CUSTOMER, phone_number='+923055555555',
            first_name='Omar'
        )
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923055555555',
            'name': 'Omar',
            'location': CitiesChoices.OTHER,
            'no_of_persons': 1,
            'no_of_kids': 0,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
        })
        entry = EntryCounterForm.objects.filter(customer=customer).latest('created_at')
        self.assertEqual(entry.status, StatusChoices.OLD)

    def test_post_missing_phone_shows_error(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'name': 'Test',
            'no_of_persons': 1,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))

    def test_post_missing_name_shows_error(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923011111111',
            'no_of_persons': 1,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))

    def test_post_updates_name_if_missing(self):
        self.client.login(username='user2', password='pass123')
        customer = User.objects.create_user(
            username='noname_cust', password='pass123',
            role=UserRoles.CUSTOMER, phone_number='+923077777777',
        )
        self.assertEqual(customer.first_name, '')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923077777777',
            'name': 'NewName',
            'location': CitiesChoices.OTHER,
            'no_of_persons': 1,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
        })
        customer.refresh_from_db()
        self.assertEqual(customer.first_name, 'NewName')

    def test_post_night_stay_no_transaction(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923066666666',
            'name': 'NightGuest',
            'location': CitiesChoices.OTHER,
            'no_of_persons': 2,
            'visit_type': VisitTypeChoices.NIGHT_STAY,
            'gate': GateChoices.MAIN,
        })
        customer = User.objects.get(phone_number='+923066666666')
        entry = EntryCounterForm.objects.get(customer=customer)
        self.assertEqual(entry.visit_type, VisitTypeChoices.NIGHT_STAY)
        self.assertFalse(EntryTransaction.objects.filter(entry_form=entry).exists())

    def test_post_group_no_transaction(self):
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923044444444',
            'name': 'GroupGuest',
            'location': CitiesChoices.OTHER,
            'no_of_persons': 10,
            'no_of_kids': 2,
            'visit_type': VisitTypeChoices.GROUP,
            'gate': GateChoices.EVENT,
        })
        customer = User.objects.get(phone_number='+923044444444')
        entry = EntryCounterForm.objects.get(customer=customer)
        self.assertEqual(entry.visit_type, VisitTypeChoices.GROUP)
        self.assertEqual(entry.no_of_kids, 2)
        self.assertFalse(EntryTransaction.objects.filter(entry_form=entry).exists())


class CheckCustomerStatusTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user3', password='pass123', role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:check_customer'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/check-customer/', fetch_redirect_response=False)

    def test_empty_phone_returns_invalid(self):
        self.client.login(username='user3', password='pass123')
        response = self.client.get(reverse('cash_counters:check_customer'))
        self.assertEqual(response.json()['status'], 'invalid')

    def test_new_phone_returns_new(self):
        self.client.login(username='user3', password='pass123')
        response = self.client.get(
            reverse('cash_counters:check_customer'),
            {'phone_number': '+923000000000'}
        )
        data = response.json()
        self.assertEqual(data['status'], 'New')

    def test_existing_phone_returns_old(self):
        self.client.login(username='user3', password='pass123')
        User.objects.create_user(
            username='oldcust', password='pass123',
            phone_number='+923012340000', first_name='OldCust',
            role=UserRoles.CUSTOMER
        )
        response = self.client.get(
            reverse('cash_counters:check_customer'),
            {'phone_number': '+923012340000'}
        )
        data = response.json()
        self.assertEqual(data['status'], 'Old')
        self.assertEqual(data['name'], 'OldCust')

    def test_existing_user_without_name(self):
        self.client.login(username='user3', password='pass123')
        User.objects.create_user(
            username='noname', password='pass123',
            phone_number='+923022222222', role=UserRoles.CUSTOMER
        )
        response = self.client.get(
            reverse('cash_counters:check_customer'),
            {'phone_number': '+923022222222'}
        )
        data = response.json()
        self.assertEqual(data['status'], 'Old')
        self.assertEqual(data['name'], 'noname')


# ═══════════════════════════════════════════════════════
# CASH HANDOVER VIEW TESTS
# ═══════════════════════════════════════════════════════

class CashHandoverViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cashier = User.objects.create_user(
            username='cashier_ho', password='pass123', role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username='mc_ho', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.ceo = User.objects.create_user(
            username='ceo_ho', password='pass123', role=UserRoles.CEO
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/cash-handover/', fetch_redirect_response=False)

    def test_cashier_can_access(self):
        self.client.login(username='cashier_ho', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertEqual(response.status_code, 200)

    def test_ceo_cannot_access(self):
        self.client.login(username='ceo_ho', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertEqual(response.status_code, 403)

    def test_main_cashier_cannot_access(self):
        self.client.login(username='mc_ho', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertEqual(response.status_code, 403)

    def test_get_shows_context(self):
        self.client.login(username='cashier_ho', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertIn('counter_types', response.context)
        self.assertIn('cashiers', response.context)
        self.assertIn('main_cashiers', response.context)
        self.assertIn('today_handovers', response.context)
        self.assertEqual(response.context['today'], timezone.localdate())

    def test_post_creates_handover(self):
        self.client.login(username='cashier_ho', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_handover'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.RECEPTION,
            'cashier': self.cashier.pk,
            'cash_amount': '50000.00',
            'handover_to': self.main_cashier.pk,
            'notes': 'Evening shift',
        })
        self.assertRedirects(response, reverse('cash_counters:cash_handover'), fetch_redirect_response=False)
        self.assertEqual(CashHandover.objects.count(), 1)
        ho = CashHandover.objects.first()
        self.assertEqual(ho.cash_amount, Decimal('50000.00'))
        self.assertEqual(ho.notes, 'Evening shift')

    def test_post_missing_fields_shows_error(self):
        self.client.login(username='cashier_ho', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_handover'), {
            'date': timezone.localdate().isoformat(),
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))
        self.assertEqual(CashHandover.objects.count(), 0)

    def test_post_invalid_user_shows_error(self):
        self.client.login(username='cashier_ho', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_handover'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.RECEPTION,
            'cashier': 99999,
            'cash_amount': '50000.00',
            'handover_to': self.main_cashier.pk,
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(m).lower() for m in messages_list))
        self.assertEqual(CashHandover.objects.count(), 0)

    def test_shows_today_handovers(self):
        self.client.login(username='cashier_ho', password='pass123')
        ho = CashHandover.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('10000.00'),
            handover_to=self.main_cashier,
        )
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertIn(ho, response.context['today_handovers'])

    def test_excludes_other_days_handovers(self):
        self.client.login(username='cashier_ho', password='pass123')
        ho = CashHandover.objects.create(
            date=timezone.localdate() - timedelta(days=3),
            counter_type=CounterTypeChoices.RECEPTION,
            cashier=self.cashier,
            cash_amount=Decimal('10000.00'),
            handover_to=self.main_cashier,
        )
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertNotIn(ho, response.context['today_handovers'])


# ═══════════════════════════════════════════════════════
# CASH REGISTER VIEW TESTS
# ═══════════════════════════════════════════════════════

class CashRegisterViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cashier = User.objects.create_user(
            username='cashier_cr', password='pass123', role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username='mc_cr', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.ceo = User.objects.create_user(
            username='ceo_cr', password='pass123', role=UserRoles.CEO
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/cash-register/', fetch_redirect_response=False)

    def test_main_cashier_can_access(self):
        self.client.login(username='mc_cr', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertEqual(response.status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username='cashier_cr', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertEqual(response.status_code, 403)

    def test_ceo_cannot_access(self):
        self.client.login(username='ceo_cr', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertEqual(response.status_code, 403)

    def test_get_shows_context(self):
        self.client.login(username='mc_cr', password='pass123')
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertIn('counter_types', response.context)
        self.assertIn('cashiers', response.context)
        self.assertIn('today_entries', response.context)
        self.assertEqual(response.context['today'], timezone.localdate())

    def test_post_creates_entry(self):
        self.client.login(username='mc_cr', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_register'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.MAIN_RESTAURANT_LSR,
            'amount_received': '75000.00',
            'received_from': self.cashier.pk,
            'on_duty_cashier': self.main_cashier.pk,
            'notes': 'Morning shift',
        })
        self.assertRedirects(response, reverse('cash_counters:cash_register'), fetch_redirect_response=False)
        self.assertEqual(CashRegister.objects.count(), 1)
        cr = CashRegister.objects.first()
        self.assertEqual(cr.amount_received, Decimal('75000.00'))

    def test_post_missing_fields_shows_error(self):
        self.client.login(username='mc_cr', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_register'), {
            'date': timezone.localdate().isoformat(),
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))
        self.assertEqual(CashRegister.objects.count(), 0)

    def test_post_invalid_user_shows_error(self):
        self.client.login(username='mc_cr', password='pass123')
        response = self.client.post(reverse('cash_counters:cash_register'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.RECEPTION,
            'amount_received': '50000.00',
            'received_from': 99999,
            'on_duty_cashier': self.main_cashier.pk,
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(m).lower() for m in messages_list))
        self.assertEqual(CashRegister.objects.count(), 0)

    def test_shows_today_entries(self):
        self.client.login(username='mc_cr', password='pass123')
        cr = CashRegister.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            amount_received=Decimal('10000.00'),
            received_from=self.cashier,
            on_duty_cashier=self.main_cashier,
        )
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertIn(cr, response.context['today_entries'])

    def test_excludes_other_days_entries(self):
        self.client.login(username='mc_cr', password='pass123')
        cr = CashRegister.objects.create(
            date=timezone.localdate() - timedelta(days=3),
            counter_type=CounterTypeChoices.RECEPTION,
            amount_received=Decimal('10000.00'),
            received_from=self.cashier,
            on_duty_cashier=self.main_cashier,
        )
        response = self.client.get(reverse('cash_counters:cash_register'))
        self.assertNotIn(cr, response.context['today_entries'])


# ═══════════════════════════════════════════════════════
# TICKET REFUND VIEW TESTS
# ═══════════════════════════════════════════════════════

class TicketRefundViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user_tr', password='pass123', role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertRedirects(response, reverse('login') + '?next=/cash-counters/ticket-refund/', fetch_redirect_response=False)

    def test_get_returns_200(self):
        self.client.login(username='user_tr', password='pass123')
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertEqual(response.status_code, 200)

    def test_get_shows_context(self):
        self.client.login(username='user_tr', password='pass123')
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertIn('reasons', response.context)
        self.assertIn('today_refunds', response.context)
        self.assertEqual(response.context['today'], timezone.localdate())

    def test_post_creates_refund(self):
        self.client.login(username='user_tr', password='pass123')
        response = self.client.post(reverse('cash_counters:ticket_refund'), {
            'date': timezone.localdate().isoformat(),
            'no_of_tickets': 5,
            'rate_per_ticket': '1500.00',
            'total_amount_refunded': '7500.00',
            'reason': TicketRefundReasonChoices.WEATHER,
            'remarks': 'Heavy rain',
        })
        self.assertRedirects(response, reverse('cash_counters:ticket_refund'), fetch_redirect_response=False)
        self.assertEqual(TicketRefund.objects.count(), 1)
        refund = TicketRefund.objects.first()
        self.assertEqual(refund.no_of_tickets, 5)
        self.assertEqual(refund.total_amount_refunded, Decimal('7500.00'))

    def test_post_missing_fields_shows_error(self):
        self.client.login(username='user_tr', password='pass123')
        response = self.client.post(reverse('cash_counters:ticket_refund'), {
            'date': timezone.localdate().isoformat(),
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))
        self.assertEqual(TicketRefund.objects.count(), 0)

    def test_shows_today_refunds(self):
        self.client.login(username='user_tr', password='pass123')
        refund = TicketRefund.objects.create(
            date=timezone.localdate(),
            no_of_tickets=3,
            total_amount_refunded=Decimal('4500.00'),
            reason=TicketRefundReasonChoices.RESTAURANT_TAX,
        )
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertIn(refund, response.context['today_refunds'])

    def test_excludes_other_days_refunds(self):
        self.client.login(username='user_tr', password='pass123')
        refund = TicketRefund.objects.create(
            date=timezone.localdate() - timedelta(days=2),
            no_of_tickets=2,
            total_amount_refunded=Decimal('3000.00'),
        )
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertNotIn(refund, response.context['today_refunds'])

    def test_post_all_reason_types(self):
        self.client.login(username='user_tr', password='pass123')
        for reason in TicketRefundReasonChoices:
            response = self.client.post(reverse('cash_counters:ticket_refund'), {
                'date': timezone.localdate().isoformat(),
                'no_of_tickets': 1,
                'rate_per_ticket': '1500.00',
                'total_amount_refunded': '1500.00',
                'reason': reason,
            })
            self.assertEqual(response.status_code, 302)
        self.assertEqual(TicketRefund.objects.count(), len(TicketRefundReasonChoices))


# ═══════════════════════════════════════════════════════
# INTEGRATION / EDGE CASE TESTS
# ═══════════════════════════════════════════════════════

class EntryTransactionIntegrationTest(TestCase):
    """Test the full entry workflow with transaction calculation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user_int', password='pass123', role=UserRoles.CASHIER
        )
        self.client.login(username='user_int', password='pass123')

    def test_paid_entry_amount_matches_formula(self):
        persons = 4
        response = self.client.post(reverse('cash_counters:entry_form'), {
            'phone_number': '+923010000001',
            'name': 'TestUser',
            'location': CitiesChoices.OTHER,
            'no_of_persons': persons,
            'visit_type': VisitTypeChoices.PAID,
            'gate': GateChoices.MAIN,
        })
        customer = User.objects.get(phone_number='+923010000001')
        entry = EntryCounterForm.objects.get(customer=customer)
        tx = EntryTransaction.objects.get(entry_form=entry)
        expected = Decimal(str(PAID_VISIT_PRICE * persons))
        self.assertEqual(tx.amount, expected)

    def test_multiple_entries_same_customer(self):
        customer = User.objects.create_user(
            username='multi', password='pass123',
            role=UserRoles.CUSTOMER, phone_number='+923010000002'
        )
        for i in range(3):
            self.client.post(reverse('cash_counters:entry_form'), {
                'phone_number': '+923010000002',
                'name': 'Multi',
                'location': CitiesChoices.OTHER,
                'no_of_persons': i + 1,
                'visit_type': VisitTypeChoices.PAID,
                'gate': GateChoices.MAIN,
            })
        entries = EntryCounterForm.objects.filter(customer=customer)
        self.assertEqual(entries.count(), 3)
        self.assertTrue(EntryTransaction.objects.filter(entry_form__customer=customer).count(), 3)

    def test_cash_handover_then_view_shows_it(self):
        mc = User.objects.create_user(
            username='mc_int', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.client.post(reverse('cash_counters:cash_handover'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.RECEPTION,
            'cashier': self.user.pk,
            'cash_amount': '25000.00',
            'handover_to': mc.pk,
            'notes': 'Test',
        })
        self.assertEqual(CashHandover.objects.count(), 1)
        response = self.client.get(reverse('cash_counters:cash_handover'))
        self.assertEqual(CashHandover.objects.filter(date=timezone.localdate()).count(), 1)

    def test_ticket_refund_then_view_shows_it(self):
        self.client.post(reverse('cash_counters:ticket_refund'), {
            'date': timezone.localdate().isoformat(),
            'no_of_tickets': 10,
            'rate_per_ticket': '1500.00',
            'total_amount_refunded': '15000.00',
            'reason': TicketRefundReasonChoices.WEATHER,
            'remarks': 'Storm',
        })
        self.assertEqual(TicketRefund.objects.count(), 1)
        response = self.client.get(reverse('cash_counters:ticket_refund'))
        self.assertEqual(len(response.context['today_refunds']), 1)

    def test_cash_register_full_workflow(self):
        mc = User.objects.create_user(
            username='mc_wf', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.client.login(username='mc_wf', password='pass123')
        self.client.post(reverse('cash_counters:cash_register'), {
            'date': timezone.localdate().isoformat(),
            'counter_type': CounterTypeChoices.SHOOTING_RANGE,
            'amount_received': '30000.00',
            'received_from': self.user.pk,
            'on_duty_cashier': mc.pk,
            'notes': 'Evening',
        })
        self.assertEqual(CashRegister.objects.count(), 1)
        cr = CashRegister.objects.first()
        self.assertEqual(cr.counter_type, CounterTypeChoices.SHOOTING_RANGE)
        self.assertEqual(cr.amount_received, Decimal('30000.00'))


class PermissionMatrixTest(TestCase):
    """Verify the exact permission matrix for all cash_counters views."""

    def setUp(self):
        self.client = Client()
        self.cashier = User.objects.create_user(
            username='perm_cashier', password='pass123', role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username='perm_mc', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.ceo = User.objects.create_user(
            username='perm_ceo', password='pass123', role=UserRoles.CEO
        )
        self.accountant = User.objects.create_user(
            username='perm_acc', password='pass123', role=UserRoles.ACCOUNTANT
        )
        self.customer = User.objects.create_user(
            username='perm_cust', password='pass123', role=UserRoles.CUSTOMER
        )

    def test_cash_handover_permissions(self):
        views = [
            reverse('cash_counters:cash_handover'),
        ]
        for url in views:
            self.client.login(username='perm_cashier', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()

            self.client.login(username='perm_mc', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

            self.client.login(username='perm_ceo', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

            self.client.login(username='perm_acc', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

            self.client.login(username='perm_cust', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

    def test_cash_register_permissions(self):
        views = [
            reverse('cash_counters:cash_register'),
        ]
        for url in views:
            self.client.login(username='perm_mc', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()

            self.client.login(username='perm_cashier', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

            self.client.login(username='perm_ceo', password='pass123')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

    def test_entry_form_any_role_can_access(self):
        for user, pwd in [
            (self.cashier, 'pass123'),
            (self.main_cashier, 'pass123'),
            (self.ceo, 'pass123'),
            (self.accountant, 'pass123'),
        ]:
            self.client.login(username=user.username, password=pwd)
            response = self.client.get(reverse('cash_counters:entry_form'))
            self.assertEqual(response.status_code, 200)
            self.client.logout()

    def test_ticket_refund_any_role_can_access(self):
        for user, pwd in [
            (self.cashier, 'pass123'),
            (self.main_cashier, 'pass123'),
            (self.ceo, 'pass123'),
        ]:
            self.client.login(username=user.username, password=pwd)
            response = self.client.get(reverse('cash_counters:ticket_refund'))
            self.assertEqual(response.status_code, 200)
            self.client.logout()

    def test_daily_sales_any_role_can_access(self):
        for user, pwd in [
            (self.cashier, 'pass123'),
            (self.main_cashier, 'pass123'),
        ]:
            self.client.login(username=user.username, password=pwd)
            response = self.client.get(reverse('cash_counters:daily_sales'))
            self.assertEqual(response.status_code, 200)
            self.client.logout()
