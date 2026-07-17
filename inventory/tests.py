from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from authentication.choices import UserRoles

from .choices import (
    AmmoPaymentChoices,
    AssetCategoryChoices,
    HospitalChoices,
    PatientTypeChoices,
    StockStatusChoices,
)
from .models import (
    AmbulanceLog,
    AmmoTransactionLog,
    FuelTransactionLog,
    GeneratorLog,
    InventoryItem,
)
from .utils import (
    STATUS_TRANSITIONS,
    get_allowed_transitions,
    get_creation_statuses,
    validate_status_transition,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════
# UTILS TESTS
# ═══════════════════════════════════════════════════════


class StatusTransitionsTest(TestCase):

    def test_required_transitions_to_issued(self):
        self.assertIn(
            StockStatusChoices.ISSUED, STATUS_TRANSITIONS[StockStatusChoices.REQUIRED]
        )

    def test_required_transitions_to_ordered(self):
        self.assertIn(
            StockStatusChoices.ORDERED, STATUS_TRANSITIONS[StockStatusChoices.REQUIRED]
        )

    def test_required_transitions_to_cancelled(self):
        self.assertIn(
            StockStatusChoices.CANCELLED,
            STATUS_TRANSITIONS[StockStatusChoices.REQUIRED],
        )

    def test_ordered_transitions_to_purchased(self):
        self.assertIn(
            StockStatusChoices.PURCHASED, STATUS_TRANSITIONS[StockStatusChoices.ORDERED]
        )

    def test_ordered_transitions_to_cancelled(self):
        self.assertIn(
            StockStatusChoices.CANCELLED, STATUS_TRANSITIONS[StockStatusChoices.ORDERED]
        )

    def test_issued_is_terminal(self):
        self.assertEqual(STATUS_TRANSITIONS[StockStatusChoices.ISSUED], [])

    def test_purchased_is_terminal(self):
        self.assertEqual(STATUS_TRANSITIONS[StockStatusChoices.PURCHASED], [])

    def test_cancelled_is_terminal(self):
        self.assertEqual(STATUS_TRANSITIONS[StockStatusChoices.CANCELLED], [])


class ValidateStatusTransitionTest(TestCase):

    def test_valid_transition_required_to_ordered(self):
        result = validate_status_transition(
            StockStatusChoices.REQUIRED, StockStatusChoices.ORDERED
        )
        self.assertTrue(result)

    def test_valid_transition_required_to_issued(self):
        result = validate_status_transition(
            StockStatusChoices.REQUIRED, StockStatusChoices.ISSUED
        )
        self.assertTrue(result)

    def test_valid_transition_required_to_cancelled(self):
        result = validate_status_transition(
            StockStatusChoices.REQUIRED, StockStatusChoices.CANCELLED
        )
        self.assertTrue(result)

    def test_valid_transition_ordered_to_purchased(self):
        result = validate_status_transition(
            StockStatusChoices.ORDERED, StockStatusChoices.PURCHASED
        )
        self.assertTrue(result)

    def test_valid_transition_ordered_to_cancelled(self):
        result = validate_status_transition(
            StockStatusChoices.ORDERED, StockStatusChoices.CANCELLED
        )
        self.assertTrue(result)

    def test_same_status_returns_true(self):
        result = validate_status_transition(
            StockStatusChoices.REQUIRED, StockStatusChoices.REQUIRED
        )
        self.assertTrue(result)

    def test_invalid_transition_ordered_to_issued(self):
        with self.assertRaises(ValidationError):
            validate_status_transition(
                StockStatusChoices.ORDERED, StockStatusChoices.ISSUED
            )

    def test_invalid_transition_issued_to_purchased(self):
        with self.assertRaises(ValidationError):
            validate_status_transition(
                StockStatusChoices.ISSUED, StockStatusChoices.PURCHASED
            )

    def test_invalid_transition_cancelled_to_any(self):
        with self.assertRaises(ValidationError):
            validate_status_transition(
                StockStatusChoices.CANCELLED, StockStatusChoices.ISSUED
            )

    def test_invalid_transition_purchased_to_any(self):
        with self.assertRaises(ValidationError):
            validate_status_transition(
                StockStatusChoices.PURCHASED, StockStatusChoices.ORDERED
            )


class GetCreationStatusesTest(TestCase):

    def test_returns_required_and_issued(self):
        statuses = get_creation_statuses()
        self.assertIn(StockStatusChoices.REQUIRED, statuses)
        self.assertIn(StockStatusChoices.ISSUED, statuses)
        self.assertEqual(len(statuses), 2)

    def test_does_not_include_ordered(self):
        self.assertNotIn(StockStatusChoices.ORDERED, get_creation_statuses())

    def test_does_not_include_purchased(self):
        self.assertNotIn(StockStatusChoices.PURCHASED, get_creation_statuses())

    def test_does_not_include_cancelled(self):
        self.assertNotIn(StockStatusChoices.CANCELLED, get_creation_statuses())


class GetAllowedTransitionsTest(TestCase):

    def test_required_allows_three(self):
        allowed = get_allowed_transitions(StockStatusChoices.REQUIRED)
        self.assertEqual(len(allowed), 3)

    def test_terminal_returns_empty(self):
        for status in [
            StockStatusChoices.ISSUED,
            StockStatusChoices.PURCHASED,
            StockStatusChoices.CANCELLED,
        ]:
            self.assertEqual(get_allowed_transitions(status), [])


# ═══════════════════════════════════════════════════════
# INVENTORY ITEM MODEL TESTS
# ═══════════════════════════════════════════════════════


class InventoryItemModelTest(TestCase):

    def test_create_item(self):
        item = InventoryItem.objects.create(
            name="Petrol",
            category=AssetCategoryChoices.FUEL,
            stock_quantity=Decimal("500.00"),
            unit="liters",
            supplier="Shell",
            notes="Premium petrol",
        )
        self.assertEqual(item.name, "Petrol")
        self.assertEqual(item.stock_quantity, Decimal("500.00"))
        self.assertEqual(item.unit, "liters")
        self.assertEqual(item.supplier, "Shell")

    def test_str(self):
        item = InventoryItem.objects.create(
            name="9mm Ammo",
            category=AssetCategoryChoices.AMMO,
        )
        self.assertEqual(str(item), "9mm Ammo")

    def test_defaults(self):
        item = InventoryItem.objects.create(
            name="Test Item",
            category=AssetCategoryChoices.OTHER,
        )
        self.assertEqual(item.stock_quantity, Decimal("0"))
        self.assertEqual(item.unit, "")
        self.assertEqual(item.supplier, "")
        self.assertEqual(item.notes, "")

    def test_ordering(self):
        item1 = InventoryItem.objects.create(
            name="B", category=AssetCategoryChoices.OTHER
        )
        item2 = InventoryItem.objects.create(
            name="A", category=AssetCategoryChoices.OTHER
        )
        items = list(InventoryItem.objects.all())
        self.assertEqual(len(items), 2)
        pks = {i.pk for i in items}
        self.assertIn(item1.pk, pks)
        self.assertIn(item2.pk, pks)

    def test_all_categories(self):
        for cat in AssetCategoryChoices:
            item = InventoryItem.objects.create(name=f"Item {cat}", category=cat)
            self.assertEqual(item.category, cat)

    def test_soft_delete_fields(self):
        item = InventoryItem.objects.create(
            name="Test", category=AssetCategoryChoices.OTHER
        )
        self.assertFalse(item.is_deleted)
        self.assertIsNone(item.deleted_at)


# ═══════════════════════════════════════════════════════
# FUEL TRANSACTION LOG MODEL TESTS
# ═══════════════════════════════════════════════════════


class FuelTransactionLogModelTest(TestCase):

    def setUp(self):
        self.fuel = InventoryItem.objects.create(
            name="Petrol",
            category=AssetCategoryChoices.FUEL,
            stock_quantity=Decimal("1000.00"),
            unit="liters",
        )
        self.vehicle = InventoryItem.objects.create(
            name="J1",
            category=AssetCategoryChoices.JETSKI,
        )

    def test_create_required(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("100.00"),
            amount=Decimal("25000.00"),
        )
        self.assertEqual(tx.transaction_status, StockStatusChoices.REQUIRED)
        self.assertEqual(tx.quantity, Decimal("100.00"))

    def test_create_issued(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.ISSUED,
            quantity=Decimal("50.00"),
            issued_to=self.vehicle,
        )
        self.fuel.refresh_from_db()
        self.assertEqual(self.fuel.stock_quantity, Decimal("950.00"))

    def test_purchased_adds_stock(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("200.00"),
            amount=Decimal("50000.00"),
        )
        tx.transaction_status = StockStatusChoices.ORDERED
        tx.save()
        tx.transaction_status = StockStatusChoices.PURCHASED
        tx.save()
        self.fuel.refresh_from_db()
        self.assertEqual(self.fuel.stock_quantity, Decimal("1200.00"))

    def test_issued_deducts_stock(self):
        FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.ISSUED,
            quantity=Decimal("100.00"),
        )
        self.fuel.refresh_from_db()
        self.assertEqual(self.fuel.stock_quantity, Decimal("900.00"))

    def test_insufficient_stock_raises_error(self):
        with self.assertRaises(ValidationError):
            FuelTransactionLog.objects.create(
                inventory_item=self.fuel,
                transaction_status=StockStatusChoices.ISSUED,
                quantity=Decimal("2000.00"),
            )

    def test_invalid_creation_status_raises_error(self):
        with self.assertRaises(ValidationError):
            FuelTransactionLog.objects.create(
                inventory_item=self.fuel,
                transaction_status=StockStatusChoices.ORDERED,
                quantity=Decimal("100.00"),
            )

    def test_str(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("100.00"),
        )
        result = str(tx)
        self.assertIn("required", result)
        self.assertIn("100", result)

    def test_ordering(self):
        tx1 = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
            date=timezone.localdate() - timedelta(days=1),
        )
        tx2 = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("20.00"),
            date=timezone.localdate(),
        )
        txns = list(FuelTransactionLog.objects.all())
        self.assertEqual(txns[0].pk, tx2.pk)
        self.assertEqual(txns[1].pk, tx1.pk)

    def test_default_date(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
        )
        self.assertEqual(tx.date, timezone.localdate())

    def test_notes_blank(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
        )
        self.assertEqual(tx.notes, "")

    def test_created_by_nullable(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
        )
        self.assertIsNone(tx.created_by)


# ═══════════════════════════════════════════════════════
# AMMO TRANSACTION LOG MODEL TESTS
# ═══════════════════════════════════════════════════════


class AmmoTransactionLogModelTest(TestCase):

    def setUp(self):
        self.ammo = InventoryItem.objects.create(
            name="9mm Rounds",
            category=AssetCategoryChoices.AMMO,
            stock_quantity=Decimal("500"),
            unit="rounds",
        )

    def test_create_required(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=50,
        )
        self.assertEqual(tx.bullet_quantity, 50)
        self.assertEqual(tx.payment, "")

    def test_create_issued_deducts_stock(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.ISSUED,
            bullet_quantity=100,
            payment=AmmoPaymentChoices.PAID_VIA_CASH,
        )
        self.ammo.refresh_from_db()
        self.assertEqual(self.ammo.stock_quantity, Decimal("400"))

    def test_purchased_adds_stock(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=200,
        )
        tx.transaction_status = StockStatusChoices.ORDERED
        tx.save()
        tx.transaction_status = StockStatusChoices.PURCHASED
        tx.save()
        self.ammo.refresh_from_db()
        self.assertEqual(self.ammo.stock_quantity, Decimal("700"))

    def test_insufficient_stock_raises_error(self):
        with self.assertRaises(ValidationError):
            AmmoTransactionLog.objects.create(
                inventory_item=self.ammo,
                transaction_status=StockStatusChoices.ISSUED,
                bullet_quantity=1000,
                payment=AmmoPaymentChoices.PAID_VIA_CASH,
            )

    def test_invalid_creation_status_raises_error(self):
        with self.assertRaises(ValidationError):
            AmmoTransactionLog.objects.create(
                inventory_item=self.ammo,
                transaction_status=StockStatusChoices.ORDERED,
                bullet_quantity=50,
            )

    def test_str(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=50,
        )
        result = str(tx)
        self.assertIn("required", result)
        self.assertIn("50", result)

    def test_default_date(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=10,
        )
        self.assertEqual(tx.date, timezone.localdate())

    def test_free_bullet_reason_nullable(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=10,
        )
        self.assertIsNone(tx.free_bullet_reason)


# ═══════════════════════════════════════════════════════
# GENERATOR LOG MODEL TESTS
# ═══════════════════════════════════════════════════════


class GeneratorLogModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="gen_user", password="pass123", role=UserRoles.CASHIER
        )
        self.generator = InventoryItem.objects.create(
            name="100kv Generator",
            category=AssetCategoryChoices.GENERATOR,
        )

    def test_create_log(self):
        log = GeneratorLog.objects.create(
            created_by=self.user,
            generator=self.generator,
            run_hours=Decimal("8.50"),
            fuel_used_liters=Decimal("25.00"),
            notes="Morning shift",
        )
        self.assertEqual(log.run_hours, Decimal("8.50"))
        self.assertEqual(log.fuel_used_liters, Decimal("25.00"))

    def test_str(self):
        log = GeneratorLog.objects.create(
            created_by=self.user,
            generator=self.generator,
            run_hours=Decimal("4.00"),
        )
        result = str(log)
        self.assertIn("100kv Generator", result)

    def test_defaults(self):
        log = GeneratorLog.objects.create(
            created_by=self.user,
            generator=self.generator,
        )
        self.assertEqual(log.run_hours, Decimal("0"))
        self.assertEqual(log.fuel_used_liters, Decimal("0"))
        self.assertEqual(log.notes, "")


# ═══════════════════════════════════════════════════════
# AMBULANCE LOG MODEL TESTS
# ═══════════════════════════════════════════════════════


class AmbulanceLogModelTest(TestCase):

    def setUp(self):
        self.driver = User.objects.create_user(
            username="amb_driver", password="pass123", role=UserRoles.CASHIER
        )
        self.ambulance = InventoryItem.objects.create(
            name="Ambulance 1",
            category=AssetCategoryChoices.AMBULANCE,
        )

    def test_create_log(self):
        log = AmbulanceLog.objects.create(
            date=timezone.localdate(),
            patient_name="Ali",
            patient_type=PatientTypeChoices.LOCAL,
            ambulance=self.ambulance,
            start_reading_km=1000,
            end_reading_km=1050,
            medical_expense=Decimal("5000.00"),
            hospital=HospitalChoices.HOSPITAL_KHANPUR,
            driver=self.driver,
        )
        self.assertEqual(log.patient_name, "Ali")
        self.assertEqual(log.kms_travelled, 50)

    def test_kms_travelled_property(self):
        log = AmbulanceLog.objects.create(
            patient_name="Test",
            patient_type=PatientTypeChoices.GUEST,
            ambulance=self.ambulance,
            start_reading_km=2000,
            end_reading_km=2100,
            hospital=HospitalChoices.HOSPITAL_RAWAL,
            driver=self.driver,
        )
        self.assertEqual(log.kms_travelled, 100)

    def test_kms_travelled_zero_if_end_less_than_start(self):
        with self.assertRaises(ValidationError):
            AmbulanceLog.objects.create(
                patient_name="Test",
                patient_type=PatientTypeChoices.LOCAL,
                ambulance=self.ambulance,
                start_reading_km=2000,
                end_reading_km=1500,
                hospital=HospitalChoices.HOSPITAL_RAWAL,
                driver=self.driver,
            )

    def test_save_validates_end_reading(self):
        with self.assertRaises(ValidationError):
            AmbulanceLog.objects.create(
                patient_name="Test",
                patient_type=PatientTypeChoices.LOCAL,
                ambulance=self.ambulance,
                start_reading_km=2000,
                end_reading_km=1500,
                hospital=HospitalChoices.HOSPITAL_RAWAL,
                driver=self.driver,
            )

    def test_save_validates_equal_readings_ok(self):
        log = AmbulanceLog.objects.create(
            patient_name="Test",
            ambulance=self.ambulance,
            start_reading_km=2000,
            end_reading_km=2000,
            hospital=HospitalChoices.HOSPITAL_RAWAL,
            driver=self.driver,
        )
        self.assertEqual(log.kms_travelled, 0)

    def test_str(self):
        log = AmbulanceLog.objects.create(
            patient_name="Ahmed",
            ambulance=self.ambulance,
            start_reading_km=1000,
            end_reading_km=1050,
            hospital=HospitalChoices.HOSPITAL_HARIPUR,
            driver=self.driver,
        )
        result = str(log)
        self.assertIn("Ahmed", result)
        self.assertIn("haripur", result)

    def test_default_date(self):
        log = AmbulanceLog.objects.create(
            patient_name="Test",
            ambulance=self.ambulance,
            start_reading_km=1000,
            end_reading_km=1050,
            hospital=HospitalChoices.HOSPITAL_RAWAL,
            driver=self.driver,
        )
        self.assertEqual(log.date, timezone.localdate())

    def test_all_hospitals(self):
        for h in HospitalChoices:
            log = AmbulanceLog.objects.create(
                patient_name="Test",
                ambulance=self.ambulance,
                start_reading_km=1000,
                end_reading_km=1050,
                hospital=h,
                driver=self.driver,
            )
            self.assertEqual(log.hospital, h)

    def test_all_patient_types(self):
        for pt in PatientTypeChoices:
            log = AmbulanceLog.objects.create(
                patient_name="Test",
                patient_type=pt,
                ambulance=self.ambulance,
                start_reading_km=1000,
                end_reading_km=1050,
                hospital=HospitalChoices.HOSPITAL_RAWAL,
                driver=self.driver,
            )
            self.assertEqual(log.patient_type, pt)


# ═══════════════════════════════════════════════════════
# VIEW TESTS — INVENTORY DASHBOARD
# ═══════════════════════════════════════════════════════


class InventoryDashboardViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="dash_user", password="pass123", role=UserRoles.CEO
        )

    def test_requires_login(self):
        response = self.client.get(reverse("inventory:inventory_dashboard"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/",
            fetch_redirect_response=False,
        )

    def test_redirects_to_stock_management(self):
        self.client.login(username="dash_user", password="pass123")
        response = self.client.get(reverse("inventory:inventory_dashboard"))
        self.assertRedirects(
            response,
            reverse("inventory:stock_management"),
            fetch_redirect_response=False,
        )


# ═══════════════════════════════════════════════════════
# VIEW TESTS — ITEM CRUD
# ═══════════════════════════════════════════════════════


class InventoryItemCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:item_create")
        self.ceo = User.objects.create_user(
            username="item_ceo", password="pass123", role=UserRoles.CEO
        )
        self.acc = User.objects.create_user(
            username="item_acc", password="pass123", role=UserRoles.ACCOUNTANT
        )
        self.hr = User.objects.create_user(
            username="item_hr", password="pass123", role=UserRoles.HR_MANAGER
        )
        self.cashier = User.objects.create_user(
            username="item_cashier", password="pass123", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/items/create/",
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="item_ceo", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_accountant_can_access(self):
        self.client.login(username="item_acc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_hr_manager_can_access(self):
        self.client.login(username="item_hr", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="item_cashier", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_creates_item(self):
        self.client.login(username="item_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "name": "New Fuel",
                "category": AssetCategoryChoices.FUEL,
                "stock_quantity": "100.00",
                "unit": "liters",
                "supplier": "Shell",
                "notes": "Test",
            },
        )
        self.assertRedirects(
            response, reverse("inventory:item_list"), fetch_redirect_response=False
        )
        self.assertEqual(InventoryItem.objects.count(), 1)
        item = InventoryItem.objects.first()
        self.assertEqual(item.name, "New Fuel")

    def test_post_missing_name_shows_error(self):
        self.client.login(username="item_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "category": AssetCategoryChoices.FUEL,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(InventoryItem.objects.count(), 0)

    def test_post_missing_category_shows_error(self):
        self.client.login(username="item_ceo", password="pass123")
        response = self.client.post(
            self.url,
            {
                "name": "Test Item",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))
        self.assertEqual(InventoryItem.objects.count(), 0)

    def test_get_shows_categories(self):
        self.client.login(username="item_ceo", password="pass123")
        response = self.client.get(self.url)
        self.assertIn("categories", response.context)


class InventoryItemListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:item_list")
        self.user = User.objects.create_user(
            username="list_user", password="pass123", role=UserRoles.CEO
        )
        self.client.login(username="list_user", password="pass123")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/items/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_shows_items(self):
        item = InventoryItem.objects.create(
            name="Fuel", category=AssetCategoryChoices.FUEL
        )
        response = self.client.get(self.url)
        self.assertIn(item, response.context["items"])

    def test_excludes_deleted_items(self):
        item = InventoryItem.objects.create(
            name="Deleted", category=AssetCategoryChoices.OTHER, is_deleted=True
        )
        response = self.client.get(self.url)
        self.assertNotIn(item, response.context["items"])

    def test_search_by_name(self):
        item = InventoryItem.objects.create(
            name="Petrol 95", category=AssetCategoryChoices.FUEL
        )
        InventoryItem.objects.create(name="Diesel", category=AssetCategoryChoices.FUEL)
        response = self.client.get(self.url, {"search": "Petrol"})
        self.assertIn(item, response.context["items"])
        self.assertEqual(response.context["search_query"], "Petrol")

    def test_search_by_supplier(self):
        item = InventoryItem.objects.create(
            name="Fuel", category=AssetCategoryChoices.FUEL, supplier="Shell Pakistan"
        )
        response = self.client.get(self.url, {"search": "Shell"})
        self.assertIn(item, response.context["items"])

    def test_category_filter(self):
        item = InventoryItem.objects.create(
            name="Petrol", category=AssetCategoryChoices.FUEL
        )
        InventoryItem.objects.create(
            name="Ammo Box", category=AssetCategoryChoices.AMMO
        )
        response = self.client.get(self.url, {"category": AssetCategoryChoices.FUEL})
        self.assertIn(item, response.context["items"])
        self.assertEqual(response.context["category_filter"], AssetCategoryChoices.FUEL)


class InventoryItemEditViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="edit_user", password="pass123", role=UserRoles.CEO
        )
        self.item = InventoryItem.objects.create(
            name="Old Name",
            category=AssetCategoryChoices.FUEL,
        )
        self.client.login(username="edit_user", password="pass123")

    def test_edit_updates_item(self):
        url = reverse("inventory:item_edit", args=[self.item.pk])
        response = self.client.post(
            url,
            {
                "name": "New Name",
                "category": AssetCategoryChoices.FUEL,
                "stock_quantity": "200.00",
            },
        )
        self.assertRedirects(
            response, reverse("inventory:item_list"), fetch_redirect_response=False
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "New Name")
        self.assertEqual(self.item.stock_quantity, Decimal("200.00"))

    def test_edit_missing_fields_shows_error(self):
        url = reverse("inventory:item_edit", args=[self.item.pk])
        response = self.client.post(url, {"name": ""})
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_edit_nonexistent_redirects(self):
        url = reverse("inventory:item_edit", args=[99999])
        response = self.client.get(url)
        self.assertRedirects(
            response, reverse("inventory:item_list"), fetch_redirect_response=False
        )

    def test_cashier_cannot_access(self):
        self.client.logout()
        self.client.login(username="edit_user", password="pass123")
        self.user.role = UserRoles.CASHIER
        self.user.save()
        response = self.client.get(reverse("inventory:item_edit", args=[self.item.pk]))
        self.assertEqual(response.status_code, 403)


class InventoryItemDeleteViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="del_user", password="pass123", role=UserRoles.CEO
        )
        self.item = InventoryItem.objects.create(
            name="To Delete",
            category=AssetCategoryChoices.OTHER,
        )
        self.client.login(username="del_user", password="pass123")

    def test_post_soft_deletes_item(self):
        url = reverse("inventory:item_delete", args=[self.item.pk])
        response = self.client.post(url)
        self.assertRedirects(
            response, reverse("inventory:item_list"), fetch_redirect_response=False
        )
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_deleted)
        self.assertIsNotNone(self.item.deleted_at)

    def test_get_does_not_delete(self):
        url = reverse("inventory:item_delete", args=[self.item.pk])
        response = self.client.get(url)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_deleted)

    def test_delete_nonexistent_shows_error(self):
        url = reverse("inventory:item_delete", args=[99999])
        response = self.client.post(url)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("not found" in str(m).lower() for m in messages_list))


# ═══════════════════════════════════════════════════════
# VIEW TESTS — FUEL ENTRY
# ═══════════════════════════════════════════════════════


class FuelEntryViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:fuel_entry")
        self.user = User.objects.create_user(
            username="fuel_user", password="pass123", role=UserRoles.CASHIER
        )
        self.fuel = InventoryItem.objects.create(
            name="Petrol",
            category=AssetCategoryChoices.FUEL,
            stock_quantity=Decimal("500.00"),
        )
        self.vehicle = InventoryItem.objects.create(
            name="J1",
            category=AssetCategoryChoices.JETSKI,
        )
        self.client.login(username="fuel_user", password="pass123")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/fuel-entry/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_required_entry(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.REQUIRED,
                "quantity": "50.00",
                "inventory_item": self.fuel.pk,
                "amount": "12500.00",
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(FuelTransactionLog.objects.count(), 1)

    def test_post_creates_issued_entry(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ISSUED,
                "quantity": "100.00",
                "inventory_item": self.fuel.pk,
                "issued_to": self.vehicle.pk,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.fuel.refresh_from_db()
        self.assertEqual(self.fuel.stock_quantity, Decimal("400.00"))

    def test_post_missing_required_fields(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_post_invalid_status(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ORDERED,
                "quantity": "50.00",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages_list))

    def test_post_insufficient_stock(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ISSUED,
                "quantity": "9999.00",
                "inventory_item": self.fuel.pk,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "insufficient" in str(m).lower() or "error" in str(m).lower()
                for m in messages_list
            )
        )

    def test_shows_today_entries(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
            created_by=self.user,
        )
        response = self.client.get(self.url)
        self.assertIn(tx, response.context["today_entries"])

    def test_excludes_old_entries(self):
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("10.00"),
            date=timezone.localdate() - timedelta(days=5),
        )
        response = self.client.get(self.url)
        self.assertNotIn(tx, response.context["today_entries"])


# ═══════════════════════════════════════════════════════
# VIEW TESTS — AMMO ENTRY
# ═══════════════════════════════════════════════════════


class AmmoEntryViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:ammo_entry")
        self.user = User.objects.create_user(
            username="ammo_user", password="pass123", role=UserRoles.CASHIER
        )
        self.ammo = InventoryItem.objects.create(
            name="9mm Ammo",
            category=AssetCategoryChoices.AMMO,
            stock_quantity=Decimal("500"),
        )
        self.client.login(username="ammo_user", password="pass123")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/ammo-entry/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_required_entry(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.REQUIRED,
                "bullet_quantity": "50",
                "inventory_item": self.ammo.pk,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(AmmoTransactionLog.objects.count(), 1)

    def test_post_creates_issued_entry(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ISSUED,
                "bullet_quantity": "100",
                "inventory_item": self.ammo.pk,
                "payment": AmmoPaymentChoices.PAID_VIA_CASH,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.ammo.refresh_from_db()
        self.assertEqual(self.ammo.stock_quantity, Decimal("400"))

    def test_post_issued_requires_payment(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ISSUED,
                "bullet_quantity": "50",
                "inventory_item": self.ammo.pk,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("payment" in str(m).lower() for m in messages_list))

    def test_post_missing_fields(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_post_invalid_status(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "transaction_status": StockStatusChoices.ORDERED,
                "bullet_quantity": "50",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages_list))

    def test_shows_today_entries(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=10,
            created_by=self.user,
        )
        response = self.client.get(self.url)
        self.assertIn(tx, response.context["today_entries"])

    def test_excludes_old_entries(self):
        tx = AmmoTransactionLog.objects.create(
            inventory_item=self.ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=10,
            date=timezone.localdate() - timedelta(days=3),
        )
        response = self.client.get(self.url)
        self.assertNotIn(tx, response.context["today_entries"])


# ═══════════════════════════════════════════════════════
# VIEW TESTS — GENERATOR LOG
# ═══════════════════════════════════════════════════════


class GeneratorLogViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:generator_log")
        self.user = User.objects.create_user(
            username="gen_user", password="pass123", role=UserRoles.CASHIER
        )
        self.generator = InventoryItem.objects.create(
            name="100kv Gen",
            category=AssetCategoryChoices.GENERATOR,
        )
        self.client.login(username="gen_user", password="pass123")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/generator-log/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_log(self):
        response = self.client.post(
            self.url,
            {
                "generator": self.generator.pk,
                "run_hours": "8.5",
                "fuel_used_liters": "25.0",
                "notes": "Morning",
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(GeneratorLog.objects.count(), 1)
        log = GeneratorLog.objects.first()
        self.assertEqual(log.created_by, self.user)

    def test_post_missing_generator(self):
        response = self.client.post(
            self.url,
            {
                "run_hours": "8.5",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_post_missing_run_hours(self):
        response = self.client.post(
            self.url,
            {
                "generator": self.generator.pk,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_post_invalid_generator(self):
        response = self.client.post(
            self.url,
            {
                "generator": 99999,
                "run_hours": "8.5",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages_list))


# ═══════════════════════════════════════════════════════
# VIEW TESTS — AMBULANCE LOG
# ═══════════════════════════════════════════════════════


class AmbulanceLogViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:ambulance_log")
        self.user = User.objects.create_user(
            username="amb_user", password="pass123", role=UserRoles.CASHIER
        )
        self.ambulance = InventoryItem.objects.create(
            name="Ambulance 1",
            category=AssetCategoryChoices.AMBULANCE,
        )
        self.client.login(username="amb_user", password="pass123")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/ambulance-log/",
            fetch_redirect_response=False,
        )

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_shows_context(self):
        response = self.client.get(self.url)
        self.assertIn("ambulances", response.context)
        self.assertIn("drivers", response.context)
        self.assertIn("hospitals", response.context)
        self.assertIn("patient_types", response.context)
        self.assertIn("today_logs", response.context)

    def test_post_creates_log(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "patient_name": "Ali Khan",
                "patient_type": PatientTypeChoices.LOCAL,
                "ambulance": self.ambulance.pk,
                "start_reading_km": "1000",
                "end_reading_km": "1050",
                "medical_expense": "5000.00",
                "hospital": HospitalChoices.HOSPITAL_KHANPUR,
                "driver": self.user.pk,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(AmbulanceLog.objects.count(), 1)

    def test_post_missing_fields(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages_list))

    def test_post_invalid_ambulance(self):
        response = self.client.post(
            self.url,
            {
                "date": timezone.localdate().isoformat(),
                "patient_name": "Test",
                "patient_type": PatientTypeChoices.LOCAL,
                "ambulance": 99999,
                "start_reading_km": "1000",
                "end_reading_km": "1050",
                "hospital": HospitalChoices.HOSPITAL_RAWAL,
                "driver": self.user.pk,
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages_list))


# ═══════════════════════════════════════════════════════
# VIEW TESTS — PURCHASE ORDERS & STOCK MANAGEMENT
# ═══════════════════════════════════════════════════════


class PurchaseOrdersViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:purchase_orders")
        self.fuel = InventoryItem.objects.create(
            name="Petrol",
            category=AssetCategoryChoices.FUEL,
            stock_quantity=Decimal("1000.00"),
        )
        self.ceo = User.objects.create_user(
            username="po_ceo", password="pass123", role=UserRoles.CEO
        )
        self.mc = User.objects.create_user(
            username="po_mc", password="pass123", role=UserRoles.MAIN_CASHIER
        )
        self.cashier = User.objects.create_user(
            username="po_cashier", password="pass123", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/purchase-orders/",
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="po_ceo", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_main_cashier_can_access(self):
        self.client.login(username="po_mc", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="po_cashier", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_shows_required_and_ordered_counts(self):
        self.client.login(username="po_ceo", password="pass123")
        fuel_req = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("100.00"),
            created_by=self.ceo,
        )
        fuel_ord = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("50.00"),
            created_by=self.ceo,
        )
        fuel_ord.transaction_status = StockStatusChoices.ORDERED
        fuel_ord.save()
        response = self.client.get(self.url)
        self.assertEqual(response.context["required_count"], 1)
        self.assertEqual(response.context["ordered_count"], 1)

    def test_post_updates_fuel_status(self):
        self.client.login(username="po_ceo", password="pass123")
        tx = FuelTransactionLog.objects.create(
            inventory_item=self.fuel,
            transaction_status=StockStatusChoices.REQUIRED,
            quantity=Decimal("100.00"),
        )
        response = self.client.post(
            self.url,
            {
                "model": "fuel",
                "record_id": tx.pk,
                "new_status": StockStatusChoices.ORDERED,
            },
        )
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        tx.refresh_from_db()
        self.assertEqual(tx.transaction_status, StockStatusChoices.ORDERED)

    def test_post_updates_ammo_status(self):
        self.client.login(username="po_ceo", password="pass123")
        ammo = InventoryItem.objects.create(
            name="Ammo",
            category=AssetCategoryChoices.AMMO,
            stock_quantity=Decimal("100"),
        )
        tx = AmmoTransactionLog.objects.create(
            inventory_item=ammo,
            transaction_status=StockStatusChoices.REQUIRED,
            bullet_quantity=50,
        )
        response = self.client.post(
            self.url,
            {
                "model": "ammo",
                "record_id": tx.pk,
                "new_status": StockStatusChoices.ORDERED,
            },
        )
        tx.refresh_from_db()
        self.assertEqual(tx.transaction_status, StockStatusChoices.ORDERED)


class StockManagementViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("inventory:stock_management")
        self.user = User.objects.create_user(
            username="sm_user", password="pass123", role=UserRoles.CEO
        )
        self.cashier = User.objects.create_user(
            username="sm_cashier", password="pass123", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("login") + "?next=/inventory/stock-management/",
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="sm_user", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="sm_cashier", password="pass123")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_shows_all_item_categories(self):
        self.client.login(username="sm_user", password="pass123")
        InventoryItem.objects.create(name="Fuel", category=AssetCategoryChoices.FUEL)
        InventoryItem.objects.create(name="Ammo", category=AssetCategoryChoices.AMMO)
        InventoryItem.objects.create(
            name="Gen", category=AssetCategoryChoices.GENERATOR
        )
        InventoryItem.objects.create(
            name="Amb", category=AssetCategoryChoices.AMBULANCE
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["fuel_items"]), 1)
        self.assertEqual(len(response.context["ammo_items"]), 1)
        self.assertEqual(len(response.context["generator_items"]), 1)
        self.assertEqual(len(response.context["ambulance_items"]), 1)
