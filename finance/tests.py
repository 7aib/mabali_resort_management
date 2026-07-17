from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from authentication.choices import UserRoles

from .constants import CounterTypeChoices, POSPaymentMethodChoices
from .models import POS

User = get_user_model()


# ═══════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════


class POSModelTest(TestCase):

    def test_create_with_defaults(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("5000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertEqual(pos.date, timezone.localdate())
        self.assertIsNone(pos.remarks)

    def test_create_with_all_fields(self):
        pos = POS.objects.create(
            date=timezone.localdate() - timedelta(days=1),
            counter_type=CounterTypeChoices.WATER_SPORTS,
            amount=Decimal("12500.75"),
            payment_method=POSPaymentMethodChoices.IBFT,
            remarks="POS entry for water sports",
        )
        pos.refresh_from_db()
        self.assertEqual(pos.counter_type, CounterTypeChoices.WATER_SPORTS)
        self.assertEqual(pos.amount, Decimal("12500.75"))
        self.assertEqual(pos.payment_method, POSPaymentMethodChoices.IBFT)
        self.assertEqual(pos.remarks, "POS entry for water sports")

    def test_str(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.SHOOTING_RANGE,
            amount=Decimal("3000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
            date=timezone.localdate(),
        )
        result = str(pos)
        self.assertIn("Shooting Range", result)
        self.assertIn("3000", result)
        self.assertIn(str(timezone.localdate()), result)

    def test_str_with_different_counters(self):
        for ct in CounterTypeChoices:
            pos = POS.objects.create(
                counter_type=ct,
                amount=Decimal("1000.00"),
                payment_method=POSPaymentMethodChoices.CASH,
            )
            result = str(pos)
            self.assertIn("POS:", result)
            self.assertIn("1000", result)

    def test_ordering(self):
        pos_old = POS.objects.create(
            date=timezone.localdate() - timedelta(days=2),
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        pos_new = POS.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("2000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        entries = list(POS.objects.all())
        self.assertEqual(entries[0].pk, pos_new.pk)
        self.assertEqual(entries[1].pk, pos_old.pk)

    def test_ordering_same_date(self):
        pos1 = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
            date=timezone.localdate(),
        )
        pos2 = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("2000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
            date=timezone.localdate(),
        )
        entries = list(POS.objects.all())
        self.assertEqual(len(entries), 2)
        pks = {e.pk for e in entries}
        self.assertIn(pos1.pk, pks)
        self.assertIn(pos2.pk, pks)

    def test_verbose_name_plural(self):
        self.assertEqual(POS._meta.verbose_name_plural, "POS entries")

    def test_soft_delete_fields(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertFalse(pos.is_deleted)
        self.assertIsNone(pos.deleted_at)

    def test_timestamps(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertIsNotNone(pos.created_at)
        self.assertIsNotNone(pos.updated_at)

    def test_remarks_nullable(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertIsNone(pos.remarks)

    def test_all_payment_methods(self):
        for pm in POSPaymentMethodChoices:
            pos = POS.objects.create(
                counter_type=CounterTypeChoices.RECEPTION,
                amount=Decimal("1000.00"),
                payment_method=pm,
            )
            self.assertEqual(pos.payment_method, pm)

    def test_all_counter_types(self):
        for ct in CounterTypeChoices:
            pos = POS.objects.create(
                counter_type=ct,
                amount=Decimal("1000.00"),
                payment_method=POSPaymentMethodChoices.CASH,
            )
            self.assertEqual(pos.counter_type, ct)

    def test_zero_amount(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("0.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertEqual(pos.amount, Decimal("0.00"))

    def test_large_amount(self):
        pos = POS.objects.create(
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("999999999.99"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        self.assertEqual(pos.amount, Decimal("999999999.99"))


# ═══════════════════════════════════════════════════════
# VIEW TESTS
# ═══════════════════════════════════════════════════════


class POSEntryViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("finance:pos_entry")
        self.ceo = User.objects.create_user(
            username="pos_ceo", password="pass123", role=UserRoles.CEO
        )
        self.accountant = User.objects.create_user(
            username="pos_acc", password="pass123", role=UserRoles.ACCOUNTANT
        )
        self.hr = User.objects.create_user(
            username="pos_hr", password="pass123", role=UserRoles.HR_MANAGER
        )
        self.mc = User.objects.create_user(
            username="pos_mc", password="pass123", role=UserRoles.MAIN_CASHIER
        )
        self.cashier = User.objects.create_user(
            username="pos_cashier", password="pass123", role=UserRoles.CASHIER
        )
        self.customer = User.objects.create_user(
            username="pos_cust", password="pass123", role=UserRoles.CUSTOMER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/finance/pos-entry/",
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="pos_ceo", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_accountant_can_access(self):
        self.client.login(username="pos_acc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_hr_manager_can_access(self):
        self.client.login(username="pos_hr", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_main_cashier_can_access(self):
        self.client.login(username="pos_mc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="pos_cashier", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_customer_cannot_access(self):
        self.client.login(username="pos_cust", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_get_shows_context(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.get(self.url)
        self.assertIn("counter_types", response.context)
        self.assertIn("payment_methods", response.context)
        self.assertIn("today_entries", response.context)
        self.assertEqual(response.context["today"], timezone.localdate())
        self.assertTemplateUsed(response, "finance/pos_entry.html")

    def test_post_creates_pos_entry(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "25000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
                "remarks": "Morning sales",
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(POS.objects.count(), 1)
        pos = POS.objects.first()
        self.assertEqual(pos.amount, Decimal("25000.00"))
        self.assertEqual(pos.counter_type, CounterTypeChoices.RECEPTION)
        self.assertEqual(pos.payment_method, POSPaymentMethodChoices.CASH)
        self.assertEqual(pos.remarks, "Morning sales")

    def test_post_without_remarks(self):
        self.client.login(username="pos_acc", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.ADVENTURE_AREA,
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.IBFT,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        pos = POS.objects.first()
        self.assertEqual(pos.remarks, "")

    def test_post_missing_date_shows_error(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(POS.objects.count(), 0)

    def test_post_missing_counter_type_shows_error(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(POS.objects.count(), 0)

    def test_post_missing_amount_shows_error(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(POS.objects.count(), 0)

    def test_post_missing_payment_method_shows_error(self):
        self.client.login(username="pos_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "5000.00",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(POS.objects.count(), 0)

    def test_shows_today_entries(self):
        self.client.login(username="pos_ceo", password="pass123")
        pos = POS.objects.create(
            date=timezone.localdate(),
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        response = self.client.get(self.url)
        self.assertIn(pos, response.context["today_entries"])

    def test_excludes_other_days_entries(self):
        self.client.login(username="pos_ceo", password="pass123")
        pos_old = POS.objects.create(
            date=timezone.localdate() - timedelta(days=3),
            counter_type=CounterTypeChoices.RECEPTION,
            amount=Decimal("1000.00"),
            payment_method=POSPaymentMethodChoices.CASH,
        )
        response = self.client.get(self.url)
        self.assertNotIn(pos_old, response.context["today_entries"])

    def test_post_all_counter_types(self):
        self.client.login(username="pos_ceo", password="pass123")
        for ct in CounterTypeChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "counter_type": ct,
                    "amount": "1000.00",
                    "payment_method": POSPaymentMethodChoices.CASH,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(POS.objects.count(), len(CounterTypeChoices))

    def test_post_all_payment_methods(self):
        self.client.login(username="pos_acc", password="pass123")
        for pm in POSPaymentMethodChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "counter_type": CounterTypeChoices.RECEPTION,
                    "amount": "1000.00",
                    "payment_method": pm,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(POS.objects.count(), len(POSPaymentMethodChoices))

    def test_accountant_can_post(self):
        self.client.login(username="pos_acc", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        self.assertEqual(POS.objects.count(), 1)

    def test_hr_manager_can_post(self):
        self.client.login(username="pos_hr", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        self.assertEqual(POS.objects.count(), 1)

    def test_main_cashier_can_post(self):
        self.client.login(username="pos_mc", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "5000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        self.assertEqual(POS.objects.count(), 1)


# ═══════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════


class POSIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="pos_int", password="pass123", role=UserRoles.CEO
        )
        self.client.login(username="pos_int", password="pass123")
        self.url = reverse("finance:pos_entry")

    def test_multiple_entries_today(self):
        for i in range(5):
            self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "counter_type": CounterTypeChoices.RECEPTION,
                    "amount": str(1000 * (i + 1)),
                    "payment_method": POSPaymentMethodChoices.CASH,
                },
            )
        self.assertEqual(POS.objects.count(), 5)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["today_entries"]), 5)

    def test_entries_across_days_split_correctly(self):
        self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "counter_type": CounterTypeChoices.RECEPTION,
                "amount": "1000.00",
                "payment_method": POSPaymentMethodChoices.CASH,
            },
        )
        self.client.post(
            self.url,
            {
                "date": (timezone.localdate() - timedelta(days=1)).isoformat(),
                "counter_type": CounterTypeChoices.WATER_SPORTS,
                "amount": "2000.00",
                "payment_method": POSPaymentMethodChoices.IBFT,
            },
        )
        response = self.client.get(self.url)
        entries = response.context["today_entries"]
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().counter_type, CounterTypeChoices.RECEPTION)

    def test_mixed_payment_methods(self):
        for pm in POSPaymentMethodChoices:
            self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "counter_type": CounterTypeChoices.RECEPTION,
                    "amount": "1000.00",
                    "payment_method": pm,
                },
            )
        self.assertEqual(POS.objects.count(), len(POSPaymentMethodChoices))
        for pm in POSPaymentMethodChoices:
            self.assertTrue(POS.objects.filter(payment_method=pm).exists())
