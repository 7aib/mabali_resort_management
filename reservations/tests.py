from decimal import Decimal
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from authentication.choices import UserRoles
from .models import Room, Reservation
from .choices import (
    RoomCategoryChoices, ReservationStatusChoices,
    PaymentMethodChoices, PaymentTypeChoices, BankChoices,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════
# HELPER FUNCTION TESTS
# ═══════════════════════════════════════════════════════

class GetCustomerByPhoneTest(TestCase):

    def test_returns_user_with_phone(self):
        from .views import _get_customer_by_phone
        user = User.objects.create_user(
            username='phone1', password='pass123', phone_number='+923011111111',
        )
        result = _get_customer_by_phone('+923011111111')
        self.assertEqual(result, user)

    def test_returns_none_for_unknown(self):
        from .views import _get_customer_by_phone
        self.assertIsNone(_get_customer_by_phone('+923099999999'))

    def test_returns_none_for_empty(self):
        from .views import _get_customer_by_phone
        self.assertIsNone(_get_customer_by_phone(''))

    def test_returns_none_for_none(self):
        from .views import _get_customer_by_phone
        self.assertIsNone(_get_customer_by_phone(None))

    def test_excludes_deleted_users(self):
        from .views import _get_customer_by_phone
        user = User.objects.create_user(
            username='del_phone', password='pass123', phone_number='+923022222222',
        )
        user.is_deleted = True
        user.save()
        self.assertIsNone(_get_customer_by_phone('+923022222222'))


class GetOrCreateCustomerTest(TestCase):

    def test_creates_new_customer(self):
        from .views import _get_or_create_customer
        user = _get_or_create_customer('+923033333333', 'NewGuest')
        self.assertEqual(user.phone_number, '+923033333333')
        self.assertEqual(user.first_name, 'NewGuest')
        self.assertEqual(user.role, UserRoles.CUSTOMER)

    def test_returns_existing_customer(self):
        from .views import _get_or_create_customer
        existing = User.objects.create_user(
            username='exist_phone', password='pass123',
            phone_number='+923044444444', first_name='OldGuest',
        )
        result = _get_or_create_customer('+923044444444', 'NewName')
        self.assertEqual(result.pk, existing.pk)
        self.assertEqual(result.first_name, 'OldGuest')

    def test_handles_username_collision(self):
        from .views import _get_or_create_customer
        User.objects.create_user(
            username='+923055555555', password='pass123',
        )
        user = _get_or_create_customer('+923055555555', 'CollideGuest')
        self.assertEqual(user.username, '+923055555555_1')


# ═══════════════════════════════════════════════════════
# ROOM MODEL TESTS
# ═══════════════════════════════════════════════════════

class RoomModelTest(TestCase):

    def test_create_room(self):
        room = Room.objects.create(
            name='Hut 1', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.assertEqual(room.name, 'Hut 1')
        self.assertEqual(room.rate_per_night, Decimal('10000.00'))
        self.assertTrue(room.is_active)

    def test_str(self):
        room = Room.objects.create(name='Suite A', category=RoomCategoryChoices.SUITE)
        self.assertEqual(str(room), 'Suite A')

    def test_ordering(self):
        Room.objects.create(name='Hut B', category=RoomCategoryChoices.HUT)
        Room.objects.create(name='Hut A', category=RoomCategoryChoices.HUT)
        rooms = list(Room.objects.all())
        self.assertEqual(rooms[0].name, 'Hut A')
        self.assertEqual(rooms[1].name, 'Hut B')

    def test_defaults(self):
        room = Room.objects.create(name='Test', category=RoomCategoryChoices.ROOM)
        self.assertEqual(room.rate_per_night, Decimal('0'))
        self.assertTrue(room.is_active)

    def test_soft_delete_fields(self):
        room = Room.objects.create(name='Test', category=RoomCategoryChoices.ROOM)
        self.assertFalse(room.is_deleted)
        self.assertIsNone(room.deleted_at)


# ═══════════════════════════════════════════════════════
# RESERVATION MODEL TESTS
# ═══════════════════════════════════════════════════════

class ReservationModelTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username='res_cust', password='pass123', role=UserRoles.CUSTOMER,
            first_name='Guest'
        )
        self.room = Room.objects.create(
            name='Hut 1', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.today = timezone.localdate()

    def test_create_reservation(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Guest', phone_number='+923011111111',
            no_of_adults=2, no_of_kids=1,
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            nights=2, rate_per_night=Decimal('10000.00'),
            advance_amount=Decimal('20000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        self.assertEqual(res.guest_name, 'Guest')
        self.assertEqual(res.nights, 2)

    def test_str(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='TestGuest',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=1),
            rate_per_night=Decimal('10000.00'),
        )
        result = str(res)
        self.assertIn('TestGuest', result)
        self.assertIn('Hut 1', result)

    def test_total_cost(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Cost',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=3),
            nights=3, rate_per_night=Decimal('10000.00'),
            discount=Decimal('5000.00'),
        )
        self.assertEqual(res.total_cost, Decimal('25000.00'))

    def test_balance_due(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Balance',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=3),
            nights=3, rate_per_night=Decimal('10000.00'),
            discount=Decimal('5000.00'),
            advance_amount=Decimal('10000.00'),
            amount_received=Decimal('5000.00'),
        )
        self.assertEqual(res.balance_due, Decimal('10000.00'))

    def test_overlap_validation_raises_error(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='First',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=3),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        res2 = Reservation(
            customer=self.customer, room=self.room,
            guest_name='Second',
            check_in_date=self.today + timedelta(days=1),
            check_out_date=self.today + timedelta(days=4),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        with self.assertRaises(ValidationError):
            res2.full_clean()

    def test_same_room_different_dates_ok(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='First',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        res2 = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Second',
            check_in_date=self.today + timedelta(days=3),
            check_out_date=self.today + timedelta(days=5),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        res2.full_clean()

    def test_edit_same_reservation_no_overlap(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='EditMe',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        res.guest_name = 'Edited'
        res.full_clean()

    def test_defaults(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Defaults',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=1),
            rate_per_night=Decimal('10000.00'),
        )
        self.assertEqual(res.no_of_adults, 1)
        self.assertEqual(res.no_of_kids, 0)
        self.assertEqual(res.nights, 1)
        self.assertEqual(res.discount, Decimal('0'))
        self.assertEqual(res.advance_amount, Decimal('0'))
        self.assertEqual(res.amount_received, Decimal('0'))
        self.assertEqual(res.payment_type, PaymentTypeChoices.ADVANCE)
        self.assertEqual(res.status, ReservationStatusChoices.CONFIRMED)

    def test_cancelled_reservation_allows_overlap(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Cancelled',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CANCELLED,
        )
        res2 = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='New',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        res2.full_clean()


# ═══════════════════════════════════════════════════════
# PERMISSION TESTS
# ═══════════════════════════════════════════════════════

class ReservationPermissionTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username='perm_ceo', password='pass123', role=UserRoles.CEO
        )
        self.acc = User.objects.create_user(
            username='perm_acc', password='pass123', role=UserRoles.ACCOUNTANT
        )
        self.mc = User.objects.create_user(
            username='perm_mc', password='pass123', role=UserRoles.MAIN_CASHIER
        )
        self.cashier = User.objects.create_user(
            username='perm_cashier', password='pass123', role=UserRoles.CASHIER
        )
        self.hr = User.objects.create_user(
            username='perm_hr', password='pass123', role=UserRoles.HR_MANAGER
        )
        self.customer = User.objects.create_user(
            username='perm_cust', password='pass123', role=UserRoles.CUSTOMER
        )

    def test_ceo_can_access_list(self):
        self.client.login(username='perm_ceo', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 200)

    def test_accountant_can_access_list(self):
        self.client.login(username='perm_acc', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 200)

    def test_main_cashier_can_access_list(self):
        self.client.login(username='perm_mc', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 200)

    def test_cashier_can_access_list(self):
        self.client.login(username='perm_cashier', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 200)

    def test_hr_manager_can_access_list(self):
        self.client.login(username='perm_hr', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 200)

    def test_customer_cannot_access_list(self):
        self.client.login(username='perm_cust', password='pass123')
        self.assertEqual(self.client.get(reverse('reservations:reservation_list')).status_code, 403)


# ═══════════════════════════════════════════════════════
# RESERVATION LIST VIEW TESTS
# ═══════════════════════════════════════════════════════

class ReservationListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='list_user', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='list_cust', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(name='Hut L', category=RoomCategoryChoices.HUT)
        self.client.login(username='list_user', password='pass123')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('reservations:reservation_list'))
        self.assertRedirects(response, reverse('login') + '?next=/reservations/', fetch_redirect_response=False)

    def test_shows_reservations(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='ListGuest',
            check_in_date=timezone.localdate(),
            check_out_date=timezone.localdate() + timedelta(days=1),
            rate_per_night=Decimal('10000.00'),
        )
        response = self.client.get(reverse('reservations:reservation_list'))
        self.assertIn(res, response.context['reservations'])
        self.assertEqual(response.context['total_count'], 1)

    def test_excludes_deleted_reservations(self):
        res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Deleted',
            check_in_date=timezone.localdate(),
            check_out_date=timezone.localdate() + timedelta(days=1),
            rate_per_night=Decimal('10000.00'),
            is_deleted=True,
        )
        response = self.client.get(reverse('reservations:reservation_list'))
        self.assertNotIn(res, response.context['reservations'])


# ═══════════════════════════════════════════════════════
# RESERVATION CREATE VIEW TESTS
# ═══════════════════════════════════════════════════════

class ReservationCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('reservations:reservation_create')
        self.user = User.objects.create_user(
            username='create_user', password='pass123', role=UserRoles.CEO
        )
        self.room = Room.objects.create(
            name='Hut C', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.today = timezone.localdate()
        self.client.login(username='create_user', password='pass123')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + '?next=/reservations/create/', fetch_redirect_response=False)

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservations/reservation_create.html')

    def test_get_shows_rooms(self):
        response = self.client.get(self.url)
        self.assertIn('rooms', response.context)
        self.assertIn(self.room, response.context['rooms'])

    def test_post_creates_reservation(self):
        response = self.client.post(self.url, {
            'guest_name': 'NewGuest',
            'phone_number': '+923010000001',
            'no_of_adults': 2,
            'no_of_kids': 0,
            'room': self.room.pk,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=2)).isoformat(),
            'nights': 2,
            'rate_per_night': '10000.00',
            'advance_amount': '20000.00',
        })
        self.assertRedirects(response, reverse('reservations:reservation_list'), fetch_redirect_response=False)
        self.assertEqual(Reservation.objects.count(), 1)
        res = Reservation.objects.first()
        self.assertEqual(res.guest_name, 'NewGuest')

    def test_post_creates_customer(self):
        self.client.post(self.url, {
            'guest_name': 'BrandNew',
            'phone_number': '+923010000099',
            'room': self.room.pk,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=1)).isoformat(),
        })
        customer = User.objects.get(phone_number='+923010000099')
        self.assertEqual(customer.first_name, 'BrandNew')
        self.assertEqual(customer.role, UserRoles.CUSTOMER)

    def test_post_reuses_existing_customer(self):
        User.objects.create_user(
            username='reuse_cust', password='pass123',
            phone_number='+923010000050', first_name='ReuseMe',
        )
        self.client.post(self.url, {
            'guest_name': 'ShouldNotUpdate',
            'phone_number': '+923010000050',
            'room': self.room.pk,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=1)).isoformat(),
        })
        customer = User.objects.get(phone_number='+923010000050')
        self.assertEqual(customer.first_name, 'ReuseMe')

    def test_post_missing_fields_shows_error(self):
        response = self.client.post(self.url, {
            'guest_name': '',
            'phone_number': '',
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))
        self.assertEqual(Reservation.objects.count(), 0)

    def test_post_invalid_room_shows_error(self):
        response = self.client.post(self.url, {
            'guest_name': 'Test',
            'phone_number': '+923010000002',
            'room': 99999,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=1)).isoformat(),
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('invalid' in str(m).lower() for m in messages_list))

    def test_post_overlap_shows_error(self):
        Reservation.objects.create(
            customer=self.customer if hasattr(self, 'customer') else User.objects.create_user(
                username='overlap_cust', password='pass123', role=UserRoles.CUSTOMER
            ),
            room=self.room,
            guest_name='Existing',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=3),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        response = self.client.post(self.url, {
            'guest_name': 'Overlap',
            'phone_number': '+923010000003',
            'room': self.room.pk,
            'check_in_date': (self.today + timedelta(days=1)).isoformat(),
            'check_out_date': (self.today + timedelta(days=4)).isoformat(),
        })
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already booked' in str(m).lower() for m in messages_list))
        self.assertEqual(Reservation.objects.count(), 1)


# ═══════════════════════════════════════════════════════
# RESERVATION EDIT VIEW TESTS
# ═══════════════════════════════════════════════════════

class ReservationEditViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='edit_user', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='edit_cust', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(
            name='Hut E', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.today = timezone.localdate()
        self.res = Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='EditGuest', phone_number='+923020000001',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            nights=2, rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        self.client.login(username='edit_user', password='pass123')

    def test_get_returns_200(self):
        url = reverse('reservations:reservation_edit', args=[self.res.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_updates_reservation(self):
        url = reverse('reservations:reservation_edit', args=[self.res.pk])
        response = self.client.post(url, {
            'guest_name': 'UpdatedGuest',
            'phone_number': '+923020000001',
            'no_of_adults': 3,
            'no_of_kids': 1,
            'room': self.room.pk,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=3)).isoformat(),
            'nights': 3,
            'rate_per_night': '10000.00',
            'status': ReservationStatusChoices.CHECKED_IN,
            'advance_amount': '15000.00',
        })
        self.assertRedirects(response, reverse('reservations:reservation_list'), fetch_redirect_response=False)
        self.res.refresh_from_db()
        self.assertEqual(self.res.guest_name, 'UpdatedGuest')
        self.assertEqual(self.res.status, ReservationStatusChoices.CHECKED_IN)

    def test_edit_nonexistent_redirects(self):
        url = reverse('reservations:reservation_edit', args=[99999])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('reservations:reservation_list'), fetch_redirect_response=False)

    def test_post_missing_fields_shows_error(self):
        url = reverse('reservations:reservation_edit', args=[self.res.pk])
        response = self.client.post(url, {'guest_name': ''})
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any('required' in str(m).lower() for m in messages_list))

    def test_edit_same_room_no_overlap_error(self):
        url = reverse('reservations:reservation_edit', args=[self.res.pk])
        response = self.client.post(url, {
            'guest_name': 'EditGuest',
            'phone_number': '+923020000001',
            'room': self.room.pk,
            'check_in_date': self.today.isoformat(),
            'check_out_date': (self.today + timedelta(days=2)).isoformat(),
            'nights': 2,
            'rate_per_night': '10000.00',
        })
        self.res.refresh_from_db()
        self.assertEqual(self.res.guest_name, 'EditGuest')


# ═══════════════════════════════════════════════════════
# CUSTOMER LOOKUP API TESTS
# ═══════════════════════════════════════════════════════

class CustomerLookupAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='lookup_user', password='pass123', role=UserRoles.CEO
        )
        self.client.login(username='lookup_user', password='pass123')
        self.url = reverse('reservations:customer_lookup')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_empty_phone(self):
        response = self.client.get(self.url)
        self.assertFalse(response.json()['found'])

    def test_unknown_phone(self):
        response = self.client.get(self.url, {'phone': '+923099999999'})
        self.assertFalse(response.json()['found'])

    def test_found_customer(self):
        User.objects.create_user(
            username='found_cust', password='pass123',
            phone_number='+923012340000', first_name='FoundMe',
        )
        response = self.client.get(self.url, {'phone': '+923012340000'})
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['name'], 'FoundMe')
        self.assertEqual(data['phone'], '+923012340000')

    def test_found_falls_back_to_username(self):
        User.objects.create_user(
            username='fallback_user', password='pass123',
            phone_number='+923012340001',
        )
        response = self.client.get(self.url, {'phone': '+923012340001'})
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['name'], 'fallback_user')


# ═══════════════════════════════════════════════════════
# ROOM STATUS VIEW TESTS
# ═══════════════════════════════════════════════════════

class RoomStatusViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='status_user', password='pass123', role=UserRoles.CEO
        )
        self.customer = User.objects.create_user(
            username='status_cust', password='pass123', role=UserRoles.CUSTOMER
        )
        self.room = Room.objects.create(
            name='Hut S', category=RoomCategoryChoices.HUT,
            rate_per_night=Decimal('10000.00'),
        )
        self.room2 = Room.objects.create(
            name='Suite S', category=RoomCategoryChoices.SUITE,
            rate_per_night=Decimal('20000.00'),
        )
        self.today = timezone.localdate()
        self.client.login(username='status_user', password='pass123')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('reservations:room_status'))
        self.assertRedirects(response, reverse('login') + '?next=/reservations/room-status/', fetch_redirect_response=False)

    def test_get_returns_200(self):
        response = self.client.get(reverse('reservations:room_status'))
        self.assertEqual(response.status_code, 200)

    def test_all_available_when_no_reservations(self):
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['available_count'], 2)
        self.assertEqual(ctx['occupied_count'], 0)
        self.assertEqual(ctx['reserved_count'], 0)

    def test_occupied_room(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Occupant',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CHECKED_IN,
        )
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['occupied_count'], 1)
        self.assertEqual(ctx['available_count'], 1)
        occupied = [r for r in ctx['room_data'] if r['status'] == 'occupied']
        self.assertEqual(len(occupied), 1)
        self.assertEqual(occupied[0]['guest'], 'Occupant')

    def test_reserved_room(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Reserver',
            check_in_date=self.today + timedelta(days=3),
            check_out_date=self.today + timedelta(days=5),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
        )
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['reserved_count'], 1)
        self.assertEqual(ctx['available_count'], 1)
        reserved = [r for r in ctx['room_data'] if r['status'] == 'reserved']
        self.assertEqual(len(reserved), 1)
        self.assertEqual(reserved[0]['guest'], 'Reserver')

    def test_checkout_day_counts_as_available(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='CheckingOut',
            check_in_date=self.today - timedelta(days=2),
            check_out_date=self.today,
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CHECKED_IN,
        )
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['available_count'], 2)
        self.assertEqual(ctx['occupied_count'], 0)

    def test_excludes_deleted_reservations(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room,
            guest_name='Deleted',
            check_in_date=self.today,
            check_out_date=self.today + timedelta(days=2),
            rate_per_night=Decimal('10000.00'),
            status=ReservationStatusChoices.CONFIRMED,
            is_deleted=True,
        )
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['available_count'], 2)
        self.assertEqual(ctx['occupied_count'], 0)

    def test_total_rooms_count(self):
        ctx = self.client.get(reverse('reservations:room_status')).context
        self.assertEqual(ctx['total_rooms'], 2)
