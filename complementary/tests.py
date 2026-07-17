from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from authentication.choices import UserRoles

from .choices import BillStatusChoices, BillTypeChoices, DepartmentChoices, HeadChoices
from .models import FreeBilling

User = get_user_model()


# ═══════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════


class FreeBillingModelTest(TestCase):

    def test_create_with_defaults(self):
        fb = FreeBilling.objects.create()
        self.assertEqual(fb.date, timezone.localdate())
        self.assertEqual(fb.guest_name, "")
        self.assertEqual(fb.bill_type, BillTypeChoices.QB_BILL)
        self.assertEqual(fb.head, HeadChoices.GUEST)
        self.assertEqual(fb.bill_status, BillStatusChoices.PAID)
        self.assertEqual(fb.invoice_no, "")
        self.assertEqual(fb.department, DepartmentChoices.ALL)
        self.assertEqual(fb.total_bill_amount, Decimal("0"))
        self.assertEqual(fb.discount_amount, Decimal("0"))
        self.assertFalse(fb.bill_upload)
        self.assertEqual(fb.reference, "")

    def test_create_with_all_fields(self):
        fb = FreeBilling.objects.create(
            date=timezone.localdate() - timedelta(days=1),
            guest_name="Ahmed Khan",
            bill_type=BillTypeChoices.PARTIAL_BILL,
            head=HeadChoices.GOVT_OFFICIALS,
            bill_status=BillStatusChoices.PAID_DISCOUNT,
            invoice_no="INV-001",
            department=DepartmentChoices.FB,
            total_bill_amount=Decimal("15000.00"),
            discount_amount=Decimal("2500.00"),
            reference="Manager approved",
        )
        fb.refresh_from_db()
        self.assertEqual(fb.guest_name, "Ahmed Khan")
        self.assertEqual(fb.bill_type, BillTypeChoices.PARTIAL_BILL)
        self.assertEqual(fb.head, HeadChoices.GOVT_OFFICIALS)
        self.assertEqual(fb.bill_status, BillStatusChoices.PAID_DISCOUNT)
        self.assertEqual(fb.invoice_no, "INV-001")
        self.assertEqual(fb.department, DepartmentChoices.FB)
        self.assertEqual(fb.total_bill_amount, Decimal("15000.00"))
        self.assertEqual(fb.discount_amount, Decimal("2500.00"))
        self.assertEqual(fb.reference, "Manager approved")

    def test_str(self):
        fb = FreeBilling.objects.create(
            guest_name="Sara",
            head=HeadChoices.GUEST,
            total_bill_amount=Decimal("5000.00"),
            date=timezone.localdate(),
        )
        result = str(fb)
        self.assertIn("Guest", result)
        self.assertIn("Sara", result)
        self.assertIn("5000", result)

    def test_str_empty_guest_name(self):
        fb = FreeBilling.objects.create(
            head=HeadChoices.STAFF,
            total_bill_amount=Decimal("0"),
            date=timezone.localdate(),
        )
        result = str(fb)
        self.assertIn("—", result)

    def test_str_various_heads(self):
        for head in HeadChoices:
            fb = FreeBilling.objects.create(head=head, date=timezone.localdate())
            result = str(fb)
            self.assertIn(head.label, result)

    def test_ordering(self):
        fb_old = FreeBilling.objects.create(
            date=timezone.localdate() - timedelta(days=2),
            guest_name="Old",
        )
        fb_new = FreeBilling.objects.create(
            date=timezone.localdate(),
            guest_name="New",
        )
        entries = list(FreeBilling.objects.all())
        self.assertEqual(entries[0].pk, fb_new.pk)
        self.assertEqual(entries[1].pk, fb_old.pk)

    def test_ordering_same_date(self):
        fb1 = FreeBilling.objects.create(
            guest_name="First",
            date=timezone.localdate(),
        )
        fb2 = FreeBilling.objects.create(
            guest_name="Second",
            date=timezone.localdate(),
        )
        entries = list(FreeBilling.objects.all())
        self.assertEqual(len(entries), 2)
        pks = {e.pk for e in entries}
        self.assertIn(fb1.pk, pks)
        self.assertIn(fb2.pk, pks)

    def test_verbose_name_plural(self):
        self.assertEqual(FreeBilling._meta.verbose_name_plural, "Free Billings")

    def test_soft_delete_fields(self):
        fb = FreeBilling.objects.create()
        self.assertFalse(fb.is_deleted)
        self.assertIsNone(fb.deleted_at)

    def test_timestamps(self):
        fb = FreeBilling.objects.create()
        self.assertIsNotNone(fb.created_at)
        self.assertIsNotNone(fb.updated_at)

    def test_bill_upload_nullable(self):
        fb = FreeBilling.objects.create()
        self.assertFalse(fb.bill_upload)

    def test_bill_upload_with_file(self):
        upload = SimpleUploadedFile(
            "test_bill.pdf", b"fake content", content_type="application/pdf"
        )
        fb = FreeBilling.objects.create(
            bill_upload=upload,
        )
        fb.refresh_from_db()
        self.assertTrue(fb.bill_upload.name.startswith("bills/"))

    def test_all_bill_types(self):
        for bt in BillTypeChoices:
            fb = FreeBilling.objects.create(bill_type=bt, date=timezone.localdate())
            self.assertEqual(fb.bill_type, bt)

    def test_all_heads(self):
        for h in HeadChoices:
            fb = FreeBilling.objects.create(head=h, date=timezone.localdate())
            self.assertEqual(fb.head, h)

    def test_all_bill_statuses(self):
        for bs in BillStatusChoices:
            fb = FreeBilling.objects.create(bill_status=bs, date=timezone.localdate())
            self.assertEqual(fb.bill_status, bs)

    def test_all_departments(self):
        for d in DepartmentChoices:
            fb = FreeBilling.objects.create(department=d, date=timezone.localdate())
            self.assertEqual(fb.department, d)


# ═══════════════════════════════════════════════════════
# VIEW TESTS
# ═══════════════════════════════════════════════════════


class FreeBillingViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="fb_user", password="pass123", role=UserRoles.CASHIER
        )
        self.url = reverse("complementary:free_billing")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/complementary/free-billing/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "complementary/free_billing.html")

    def test_get_shows_context(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.get(self.url)
        self.assertIn("bill_type_choices", response.context)
        self.assertIn("head_choices", response.context)
        self.assertIn("bill_status_choices", response.context)
        self.assertIn("department_choices", response.context)
        self.assertIn("today_entries", response.context)
        self.assertEqual(response.context["today"], timezone.localdate())

    def test_post_creates_entry(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "guest_name": "Test Guest",
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.PAID,
                "department": DepartmentChoices.FB,
                "total_bill_amount": "10000.00",
                "discount_amount": "500.00",
                "invoice_no": "INV-100",
                "reference": "Test reference",
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(FreeBilling.objects.count(), 1)
        fb = FreeBilling.objects.first()
        self.assertEqual(fb.guest_name, "Test Guest")
        self.assertEqual(fb.total_bill_amount, Decimal("10000.00"))
        self.assertEqual(fb.discount_amount, Decimal("500.00"))
        self.assertEqual(fb.invoice_no, "INV-100")

    def test_post_creates_entry_with_file(self):
        self.client.login(username="fb_user", password="pass123")
        upload = SimpleUploadedFile(
            "bill.pdf", b"file content", content_type="application/pdf"
        )
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.STAFF,
                "bill_status": BillStatusChoices.FREE,
                "department": DepartmentChoices.ALL,
                "bill_upload": upload,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(FreeBilling.objects.count(), 1)
        fb = FreeBilling.objects.first()
        self.assertTrue(fb.bill_upload.name.startswith("bills/"))

    def test_post_missing_date_shows_error(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.PAID,
                "department": DepartmentChoices.ALL,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(FreeBilling.objects.count(), 0)

    def test_post_missing_bill_type_shows_error(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.PAID,
                "department": DepartmentChoices.ALL,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(FreeBilling.objects.count(), 0)

    def test_post_missing_head_shows_error(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.QB_BILL,
                "bill_status": BillStatusChoices.PAID,
                "department": DepartmentChoices.ALL,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(FreeBilling.objects.count(), 0)

    def test_post_missing_bill_status_shows_error(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "department": DepartmentChoices.ALL,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(FreeBilling.objects.count(), 0)

    def test_post_missing_department_shows_error(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.PAID,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(FreeBilling.objects.count(), 0)

    def test_post_optional_fields_blank(self):
        self.client.login(username="fb_user", password="pass123")
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.WITHOUT_QT,
                "head": HeadChoices.VENDOR,
                "bill_status": BillStatusChoices.PENDING,
                "department": DepartmentChoices.ADVENTURE,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        fb = FreeBilling.objects.first()
        self.assertEqual(fb.guest_name, "")
        self.assertEqual(fb.invoice_no, "")
        self.assertEqual(fb.reference, "")

    def test_shows_today_entries(self):
        self.client.login(username="fb_user", password="pass123")
        fb = FreeBilling.objects.create(
            date=timezone.localdate(),
            guest_name="Today Guest",
            head=HeadChoices.GUEST,
        )
        response = self.client.get(self.url)
        self.assertIn(fb, response.context["today_entries"])

    def test_excludes_other_days_entries(self):
        self.client.login(username="fb_user", password="pass123")
        fb_old = FreeBilling.objects.create(
            date=timezone.localdate() - timedelta(days=3),
            guest_name="Old Guest",
            head=HeadChoices.STAFF,
        )
        response = self.client.get(self.url)
        self.assertNotIn(fb_old, response.context["today_entries"])

    def test_post_all_bill_types(self):
        self.client.login(username="fb_user", password="pass123")
        for bt in BillTypeChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "bill_type": bt,
                    "head": HeadChoices.GUEST,
                    "bill_status": BillStatusChoices.PAID,
                    "department": DepartmentChoices.ALL,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(FreeBilling.objects.count(), len(BillTypeChoices))

    def test_post_all_heads(self):
        self.client.login(username="fb_user", password="pass123")
        for h in HeadChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "bill_type": BillTypeChoices.QB_BILL,
                    "head": h,
                    "bill_status": BillStatusChoices.PAID,
                    "department": DepartmentChoices.ALL,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(FreeBilling.objects.count(), len(HeadChoices))

    def test_post_all_bill_statuses(self):
        self.client.login(username="fb_user", password="pass123")
        for bs in BillStatusChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "bill_type": BillTypeChoices.QB_BILL,
                    "head": HeadChoices.GUEST,
                    "bill_status": bs,
                    "department": DepartmentChoices.ALL,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(FreeBilling.objects.count(), len(BillStatusChoices))

    def test_post_all_departments(self):
        self.client.login(username="fb_user", password="pass123")
        for d in DepartmentChoices:
            response = self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "bill_type": BillTypeChoices.QB_BILL,
                    "head": HeadChoices.GUEST,
                    "bill_status": BillStatusChoices.PAID,
                    "department": d,
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(FreeBilling.objects.count(), len(DepartmentChoices))


# ═══════════════════════════════════════════════════════
# PERMISSION TESTS
# ═══════════════════════════════════════════════════════


class FreeBillingPermissionTest(TestCase):
    """Any logged-in user can access free_billing_view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("complementary:free_billing")
        self.cashier = User.objects.create_user(
            username="perm_cashier", password="pass123", role=UserRoles.CASHIER
        )
        self.main_cashier = User.objects.create_user(
            username="perm_mc", password="pass123", role=UserRoles.MAIN_CASHIER
        )
        self.ceo = User.objects.create_user(
            username="perm_ceo", password="pass123", role=UserRoles.CEO
        )
        self.accountant = User.objects.create_user(
            username="perm_acc", password="pass123", role=UserRoles.ACCOUNTANT
        )
        self.customer = User.objects.create_user(
            username="perm_cust", password="pass123", role=UserRoles.CUSTOMER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_cashier_can_access(self):
        self.client.login(username="perm_cashier", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_main_cashier_can_access(self):
        self.client.login(username="perm_mc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_ceo_can_access(self):
        self.client.login(username="perm_ceo", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_accountant_can_access(self):
        self.client.login(username="perm_acc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_customer_can_access(self):
        self.client.login(username="perm_cust", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)


# ═══════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════


class FreeBillingIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="fb_int", password="pass123", role=UserRoles.ACCOUNTANT
        )
        self.client.login(username="fb_int", password="pass123")
        self.url = reverse("complementary:free_billing")

    def test_create_multiple_entries_today(self):
        for i in range(5):
            self.client.post(
                self.url,
                {
                    "date": timezone.localdate().isoformat(),
                    "guest_name": f"Guest {i}",
                    "bill_type": BillTypeChoices.QB_BILL,
                    "head": HeadChoices.GUEST,
                    "bill_status": BillStatusChoices.PAID,
                    "department": DepartmentChoices.ALL,
                    "total_bill_amount": str(1000 * (i + 1)),
                },
            )
        self.assertEqual(FreeBilling.objects.count(), 5)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["today_entries"]), 5)

    def test_entries_across_days_split_correctly(self):
        self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "guest_name": "Today",
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.GUEST,
                "bill_status": BillStatusChoices.PAID,
                "department": DepartmentChoices.ALL,
            },
        )
        self.client.post(
            self.url,
            {
                "date": (timezone.localdate() - timedelta(days=1)).isoformat(),
                "guest_name": "Yesterday",
                "bill_type": BillTypeChoices.QB_BILL,
                "head": HeadChoices.STAFF,
                "bill_status": BillStatusChoices.FREE,
                "department": DepartmentChoices.ALL,
            },
        )
        response = self.client.get(self.url)
        entries = response.context["today_entries"]
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().guest_name, "Today")

    def test_discount_and_amount_persisted(self):
        self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "bill_type": BillTypeChoices.PARTIAL_BILL,
                "head": HeadChoices.EXECUTIVE_PERSONALS,
                "bill_status": BillStatusChoices.PAID_DISCOUNT,
                "department": DepartmentChoices.FB,
                "total_bill_amount": "25000.00",
                "discount_amount": "5000.00",
                "reference": "Approved by GM",
            },
        )
        fb = FreeBilling.objects.first()
        self.assertEqual(fb.total_bill_amount, Decimal("25000.00"))
        self.assertEqual(fb.discount_amount, Decimal("5000.00"))
        self.assertEqual(fb.reference, "Approved by GM")
