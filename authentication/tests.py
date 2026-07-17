"""Comprehensive tests for the authentication app."""

import re

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from authentication.choices import UserRoles
from authentication.forms import LoginForm
from authentication.views import _check_phone_number_exists, _validate_phone_number

User = get_user_model()


# ═══════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════


class UserModelTest(TestCase):
    """Test User model creation, fields, and behavior."""

    def test_create_user_with_defaults(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.role, UserRoles.CUSTOMER)
        self.assertIsNone(user.phone_number)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_deleted)
        self.assertIsNone(user.deleted_at)

    def test_str_representation(self):
        user = User.objects.create_user(
            username="ahmed", password="testpass123", role=UserRoles.CEO
        )
        self.assertEqual(str(user), "ahmed (CEO)")

    def test_str_representation_default_role(self):
        user = User.objects.create_user(username="guest", password="testpass123")
        self.assertEqual(str(user), "guest (Customer)")

    def test_phone_number_unique(self):
        User.objects.create_user(
            username="user1", password="testpass123", phone_number="+923011234567"
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2", password="testpass123", phone_number="+923011234567"
            )

    def test_phone_number_nullable(self):
        user = User.objects.create_user(username="nophone", password="testpass123")
        self.assertIsNone(user.phone_number)

    def test_phone_number_max_length(self):
        user = User.objects.create_user(
            username="phonetest", password="testpass123", phone_number="+923011234567"
        )
        self.assertLessEqual(len(user.phone_number), 15)

    def test_timestamp_fields_auto_set(self):
        user = User.objects.create_user(username="timestamp", password="testpass123")
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_soft_delete_fields(self):
        user = User.objects.create_user(username="softdel", password="testpass123")
        self.assertFalse(user.is_deleted)
        self.assertIsNone(user.deleted_at)

    def test_role_choices(self):
        for role_value, role_label in UserRoles.choices:
            user = User.objects.create_user(
                username="role_%s" % role_value.lower(),
                password="testpass123",
                role=role_value,
            )
            self.assertEqual(user.role, role_value)
            self.assertEqual(user.get_role_display(), role_label)

    def test_all_role_values_exist(self):
        expected_roles = [
            "CASHIER",
            "ACCOUNTANT",
            "MAIN_CASHIER",
            "CEO",
            "HOST",
            "SALE",
            "CUSTOMER",
            "DRIVER",
            "WAITER",
            "HR_MANAGER",
        ]
        actual_roles = [r[0] for r in UserRoles.choices]
        for role in expected_roles:
            self.assertIn(role, actual_roles)


# ═══════════════════════════════════════════════════════
# PHONE VALIDATION HELPER TESTS
# ═══════════════════════════════════════════════════════


class PhoneValidationTest(TestCase):
    """Test _validate_phone_number helper function."""

    def test_valid_phone_number(self):
        valid, msg = _validate_phone_number("+923011234567")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_empty_phone_is_valid(self):
        valid, msg = _validate_phone_number("")
        self.assertTrue(valid)

    def test_none_phone_is_valid(self):
        valid, msg = _validate_phone_number(None)
        self.assertTrue(valid)

    def test_whitespace_only_is_valid(self):
        valid, msg = _validate_phone_number("   ")
        self.assertTrue(valid)

    def test_missing_plus_prefix(self):
        valid, msg = _validate_phone_number("923011234567")
        self.assertFalse(valid)
        self.assertIn("+92", msg)

    def test_wrong_country_code(self):
        valid, msg = _validate_phone_number("+913011234567")
        self.assertFalse(valid)

    def test_too_short(self):
        valid, msg = _validate_phone_number("+92301123")
        self.assertFalse(valid)

    def test_too_long(self):
        valid, msg = _validate_phone_number("+9230112345678")
        self.assertFalse(valid)

    def test_contains_letters(self):
        valid, msg = _validate_phone_number("+92301123456a")
        self.assertFalse(valid)

    def test_with_spaces(self):
        valid, msg = _validate_phone_number("+92 301 123 4567")
        self.assertFalse(valid)

    def test_with_dashes(self):
        valid, msg = _validate_phone_number("+92-301-123-4567")
        self.assertFalse(valid)

    def test_exactly_13_chars(self):
        valid, msg = _validate_phone_number("+923011234567")
        self.assertTrue(valid)
        self.assertEqual(len("+923011234567"), 13)


class PhoneExistsTest(TestCase):
    """Test _check_phone_number_exists helper function."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="existing", password="testpass123", phone_number="+923011234567"
        )

    def test_phone_exists(self):
        self.assertTrue(_check_phone_number_exists("+923011234567"))

    def test_phone_does_not_exist(self):
        self.assertFalse(_check_phone_number_exists("+923099999999"))

    def test_empty_phone_returns_false(self):
        self.assertFalse(_check_phone_number_exists(""))

    def test_none_phone_returns_false(self):
        self.assertFalse(_check_phone_number_exists(None))

    def test_exclude_user(self):
        self.assertFalse(
            _check_phone_number_exists("+923011234567", exclude_user_id=self.user.id)
        )

    def test_exclude_different_user_still_exists(self):
        other = User.objects.create_user(
            username="other", password="testpass123", phone_number="+923099999999"
        )
        self.assertTrue(
            _check_phone_number_exists("+923099999999", exclude_user_id=self.user.id)
        )


# ═══════════════════════════════════════════════════════
# FORM TESTS
# ═══════════════════════════════════════════════════════


class LoginFormTest(TestCase):
    """Test LoginForm validation."""

    def test_valid_form(self):
        form = LoginForm(data={"username": "admin", "password": "pass123"})
        self.assertTrue(form.is_valid())

    def test_missing_username(self):
        form = LoginForm(data={"password": "pass123"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_missing_password(self):
        form = LoginForm(data={"username": "admin"})
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_empty_data(self):
        form = LoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn("password", form.errors)


# ═══════════════════════════════════════════════════════
# LOGIN VIEW TESTS
# ═══════════════════════════════════════════════════════


class LoginViewTest(TestCase):
    """Test login_view for GET and POST scenarios."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testlogin", password="TestPass123!", role=UserRoles.CASHIER
        )

    def test_get_returns_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_post_valid_credentials_redirects(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "testlogin",
                "password": "TestPass123!",
            },
        )
        self.assertRedirects(
            response, reverse("dashboard"), fetch_redirect_response=False
        )

    def test_post_valid_credentials_logs_in(self):
        self.client.post(
            reverse("login"),
            {
                "username": "testlogin",
                "password": "TestPass123!",
            },
        )
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_post_invalid_password(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "testlogin",
                "password": "WrongPassword",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Invalid username or password" in str(m) for m in messages_list)
        )

    def test_post_nonexistent_user(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "nouser",
                "password": "nopass",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Invalid username or password" in str(m) for m in messages_list)
        )

    def test_post_empty_form(self):
        response = self.client.post(reverse("login"), {})
        self.assertEqual(response.status_code, 200)

    def test_already_logged_in_user_can_still_see_login(self):
        self.client.login(username="testlogin", password="TestPass123!")
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)


# ═══════════════════════════════════════════════════════
# LOGOUT VIEW TESTS
# ═══════════════════════════════════════════════════════


class LogoutViewTest(TestCase):
    """Test logout_view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testlogout", password="TestPass123!", role=UserRoles.CASHIER
        )

    def test_logout_redirects_to_login(self):
        self.client.login(username="testlogout", password="TestPass123!")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_logout_logs_out_user(self):
        self.client.login(username="testlogout", password="TestPass123!")
        self.client.get(reverse("logout"))
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=/profile/",
            fetch_redirect_response=False,
        )

    def test_logout_when_not_logged_in(self):
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)


# ═══════════════════════════════════════════════════════
# PROFILE VIEW TESTS
# ═══════════════════════════════════════════════════════


class ProfileViewTest(TestCase):
    """Test profile_view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testprofile", password="TestPass123!", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=/profile/",
            fetch_redirect_response=False,
        )

    def test_logged_in_user_sees_profile(self):
        self.client.login(username="testprofile", password="TestPass123!")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")


# ═══════════════════════════════════════════════════════
# CHANGE PASSWORD VIEW TESTS
# ═══════════════════════════════════════════════════════


class ChangePasswordViewTest(TestCase):
    """Test change_password_view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testpw", password="OldPass123!", role=UserRoles.CASHIER
        )
        self.client.login(username="testpw", password="OldPass123!")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("change_password"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=/change-password/",
            fetch_redirect_response=False,
        )

    def test_get_renders_form(self):
        response = self.client.get(reverse("change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "change_password.html")

    def test_wrong_current_password(self):
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "WrongPass",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("incorrect" in str(m).lower() for m in messages_list))

    def test_empty_new_password(self):
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "",
                "confirm_password": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("cannot be empty" in str(m).lower() for m in messages_list))

    def test_passwords_do_not_match(self):
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "NewPass123!",
                "confirm_password": "DifferentPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("do not match" in str(m).lower() for m in messages_list))

    def test_password_too_short(self):
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "short",
                "confirm_password": "short",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("8 characters" in str(m) for m in messages_list))

    def test_successful_password_change(self):
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "NewPass456!",
                "confirm_password": "NewPass456!",
            },
        )
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("successfully" in str(m).lower() for m in messages_list))

    def test_old_password_no_longer_works_after_change(self):
        self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "NewPass456!",
                "confirm_password": "NewPass456!",
            },
        )
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {
                "username": "testpw",
                "password": "OldPass123!",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid" in str(m) for m in messages_list))


# ═══════════════════════════════════════════════════════
# EMPLOYEE DASHBOARD TESTS
# ═══════════════════════════════════════════════════════


class EmployeeDashboardTest(TestCase):
    """Test employee_dashboard view."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="TestPass123!", role=UserRoles.CASHIER
        )
        self.customer = User.objects.create_user(
            username="customer", password="TestPass123!", role=UserRoles.CUSTOMER
        )

    def test_requires_login(self):
        response = self.client.get(reverse("employee_dashboard"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=/employee_dashboard/",
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="cashier", password="TestPass123!")
        response = self.client.get(reverse("employee_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access(self):
        self.client.login(username="customer", password="TestPass123!")
        response = self.client.get(reverse("employee_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_excludes_ceo_from_list(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_dashboard"))
        employees = response.context["employees"]
        self.assertNotIn(self.ceo, employees)
        self.assertIn(self.cashier, employees)


# ═══════════════════════════════════════════════════════
# EMPLOYEE CREATE TESTS
# ═══════════════════════════════════════════════════════


class EmployeeCreateTest(TestCase):
    """Test employee_create view."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="TestPass123!", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse("employee_create"))
        self.assertRedirects(
            response, "/?next=/employee_create/", fetch_redirect_response=False
        )

    def test_ceo_can_access(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_create"))
        self.assertEqual(response.status_code, 200)

    def test_cashier_cannot_access(self):
        self.client.login(username="cashier", password="TestPass123!")
        response = self.client.get(reverse("employee_create"))
        self.assertEqual(response.status_code, 403)

    def test_get_shows_roles(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_create"))
        self.assertIn("roles", response.context)

    def test_create_employee_success(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(
            reverse("employee_create"),
            {
                "first_name": "New",
                "last_name": "Employee",
                "username": "newemp",
                "email": "new@test.com",
                "role": UserRoles.CASHIER,
                "password": "StrongPass123!",
                "phone_number": "+923011234567",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newemp").exists())

    def test_create_employee_invalid_phone(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(
            reverse("employee_create"),
            {
                "first_name": "Bad",
                "last_name": "Phone",
                "username": "badphone",
                "email": "bad@test.com",
                "role": UserRoles.CASHIER,
                "password": "StrongPass123!",
                "phone_number": "12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Phone Number Error" in str(m) for m in messages_list))

    def test_create_employee_duplicate_username(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(
            reverse("employee_create"),
            {
                "first_name": "Dup",
                "last_name": "User",
                "username": "cashier",  # already exists
                "email": "dup@test.com",
                "role": UserRoles.CASHIER,
                "password": "StrongPass123!",
                "phone_number": "+923099999999",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "already exists" in str(m).lower() or "Error" in str(m)
                for m in messages_list
            )
        )


# ═══════════════════════════════════════════════════════
# EMPLOYEE DETAIL TESTS
# ═══════════════════════════════════════════════════════


class EmployeeDetailTest(TestCase):
    """Test employee_detail view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="detailuser", password="TestPass123!", role=UserRoles.CASHIER
        )
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )

    def test_requires_login(self):
        response = self.client.get(reverse("employee_detail", args=[self.user.pk]))
        self.assertRedirects(
            response,
            "/?next=/employee/%d/" % self.user.pk,
            fetch_redirect_response=False,
        )

    def test_logged_in_user_can_view(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_detail", args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["employee"], self.user)

    def test_404_for_nonexistent(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


# ═══════════════════════════════════════════════════════
# EMPLOYEE EDIT TESTS
# ═══════════════════════════════════════════════════════


class EmployeeEditTest(TestCase):
    """Test employee_edit view."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )
        self.employee = User.objects.create_user(
            username="editemp",
            password="TestPass123!",
            role=UserRoles.CASHIER,
            phone_number="+923011234567",
        )

    def test_requires_login(self):
        response = self.client.get(reverse("employee_edit", args=[self.employee.pk]))
        self.assertRedirects(
            response,
            "/?next=/employee/%d/edit/" % self.employee.pk,
            fetch_redirect_response=False,
        )

    def test_ceo_can_access(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_edit", args=[self.employee.pk]))
        self.assertEqual(response.status_code, 200)

    def test_edit_updates_employee(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(
            reverse("employee_edit", args=[self.employee.pk]),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@test.com",
                "role": UserRoles.ACCOUNTANT,
                "phone_number": "+923019876543",
            },
        )
        self.assertRedirects(
            response,
            reverse("employee_detail", args=[self.employee.pk]),
            fetch_redirect_response=False,
        )
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, "Updated")
        self.assertEqual(self.employee.role, UserRoles.ACCOUNTANT)

    def test_edit_invalid_phone(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(
            reverse("employee_edit", args=[self.employee.pk]),
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@test.com",
                "role": UserRoles.CASHIER,
                "phone_number": "badphone",
            },
        )
        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Phone Number Error" in str(m) for m in messages_list))


# ═══════════════════════════════════════════════════════
# EMPLOYEE DELETE TESTS
# ═══════════════════════════════════════════════════════


class EmployeeDeleteTest(TestCase):
    """Test employee_delete view."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )
        self.employee = User.objects.create_user(
            username="delemp", password="TestPass123!", role=UserRoles.CASHIER
        )

    def test_requires_login(self):
        response = self.client.get(reverse("employee_delete", args=[self.employee.pk]))
        self.assertRedirects(
            response,
            "/?next=/employee/%d/delete/" % self.employee.pk,
            fetch_redirect_response=False,
        )

    def test_ceo_can_see_delete_page(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.get(reverse("employee_delete", args=[self.employee.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_removes_employee(self):
        self.client.login(username="ceo", password="TestPass123!")
        response = self.client.post(reverse("employee_delete", args=[self.employee.pk]))
        self.assertRedirects(
            response, reverse("employee_dashboard"), fetch_redirect_response=False
        )
        self.assertFalse(User.objects.filter(pk=self.employee.pk).exists())

    def test_get_does_not_delete(self):
        self.client.login(username="ceo", password="TestPass123!")
        self.client.get(reverse("employee_delete", args=[self.employee.pk]))
        self.assertTrue(User.objects.filter(pk=self.employee.pk).exists())


# ═══════════════════════════════════════════════════════
# ROLES_REQUIRED DECORATOR TESTS
# ═══════════════════════════════════════════════════════


class RolesRequiredDecoratorTest(TestCase):
    """Test roles_required decorator across different views."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )
        self.accountant = User.objects.create_user(
            username="accountant", password="TestPass123!", role=UserRoles.ACCOUNTANT
        )
        self.hr = User.objects.create_user(
            username="hr", password="TestPass123!", role=UserRoles.HR_MANAGER
        )
        self.cashier = User.objects.create_user(
            username="cashier", password="TestPass123!", role=UserRoles.CASHIER
        )
        self.customer = User.objects.create_user(
            username="customer", password="TestPass123!", role=UserRoles.CUSTOMER
        )

    def test_ceo_access_employee_dashboard(self):
        self.client.login(username="ceo", password="TestPass123!")
        self.assertEqual(
            self.client.get(reverse("employee_dashboard")).status_code, 200
        )

    def test_accountant_access_employee_dashboard(self):
        self.client.login(username="accountant", password="TestPass123!")
        self.assertEqual(
            self.client.get(reverse("employee_dashboard")).status_code, 200
        )

    def test_hr_access_employee_dashboard(self):
        self.client.login(username="hr", password="TestPass123!")
        self.assertEqual(
            self.client.get(reverse("employee_dashboard")).status_code, 200
        )

    def test_cashier_denied_employee_dashboard(self):
        self.client.login(username="cashier", password="TestPass123!")
        self.assertEqual(
            self.client.get(reverse("employee_dashboard")).status_code, 403
        )

    def test_ceo_access_employee_create(self):
        self.client.login(username="ceo", password="TestPass123!")
        self.assertEqual(self.client.get(reverse("employee_create")).status_code, 200)

    def test_hr_access_employee_create(self):
        self.client.login(username="hr", password="TestPass123!")
        self.assertEqual(self.client.get(reverse("employee_create")).status_code, 200)

    def test_accountant_denied_employee_create(self):
        self.client.login(username="accountant", password="TestPass123!")
        self.assertEqual(self.client.get(reverse("employee_create")).status_code, 403)


# ═══════════════════════════════════════════════════════
# INTEGRATION / EDGE CASE TESTS
# ═══════════════════════════════════════════════════════


class IntegrationTest(TestCase):
    """End-to-end integration tests."""

    def setUp(self):
        self.client = Client()
        self.ceo = User.objects.create_user(
            username="ceo", password="TestPass123!", role=UserRoles.CEO
        )

    def test_full_employee_lifecycle(self):
        """Create -> View -> Edit -> Delete an employee."""
        self.client.login(username="ceo", password="TestPass123!")

        # Create
        response = self.client.post(
            reverse("employee_create"),
            {
                "first_name": "Lifecycle",
                "last_name": "Test",
                "username": "lifecycle_emp",
                "email": "lifecycle@test.com",
                "role": UserRoles.CASHIER,
                "password": "StrongPass123!",
                "phone_number": "+923011234567",
            },
        )
        emp = User.objects.get(username="lifecycle_emp")
        self.assertEqual(response.status_code, 302)

        # View
        response = self.client.get(reverse("employee_detail", args=[emp.pk]))
        self.assertEqual(response.status_code, 200)

        # Edit
        response = self.client.post(
            reverse("employee_edit", args=[emp.pk]),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@test.com",
                "role": UserRoles.ACCOUNTANT,
                "phone_number": "+923019876543",
            },
        )
        emp.refresh_from_db()
        self.assertEqual(emp.first_name, "Updated")

        # Delete
        response = self.client.post(reverse("employee_delete", args=[emp.pk]))
        self.assertFalse(User.objects.filter(pk=emp.pk).exists())

    def test_login_change_password_logout_flow(self):
        """Login -> Change Password -> Logout -> Login with new password."""
        user = User.objects.create_user(
            username="flowtest", password="OldPass123!", role=UserRoles.CASHIER
        )

        # Login
        self.client.login(username="flowtest", password="OldPass123!")
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)

        # Change password
        response = self.client.post(
            reverse("change_password"),
            {
                "current_password": "OldPass123!",
                "new_password": "NewPass456!",
                "confirm_password": "NewPass456!",
            },
        )
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

        # Logout
        self.client.get(reverse("logout"))

        # Login with new password
        response = self.client.post(
            reverse("login"),
            {
                "username": "flowtest",
                "password": "NewPass456!",
            },
        )
        self.assertRedirects(
            response, reverse("dashboard"), fetch_redirect_response=False
        )

        # Old password no longer works
        self.client.get(reverse("logout"))
        response = self.client.post(
            reverse("login"),
            {
                "username": "flowtest",
                "password": "OldPass123!",
            },
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid" in str(m) for m in messages_list))
