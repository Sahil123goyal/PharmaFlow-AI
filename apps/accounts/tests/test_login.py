"""Tests for the PharmaFlowAI sign-in flow."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class LoginPageTests(TestCase):
    """The login page renders the elements the owner needs."""

    def setUp(self):
        self.url = reverse("accounts:login")

    def test_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_page_shows_branding_and_controls(self):
        response = self.client.get(self.url)
        content = response.content.decode()

        self.assertIn("Smart Pharmacy Management, Simplified", content)
        self.assertIn('name="username"', content)
        self.assertIn('name="password"', content)
        self.assertIn('name="remember_me"', content)
        self.assertIn("data-password-toggle", content)
        self.assertIn(reverse("accounts:password_help"), content)
        self.assertIn("csrfmiddlewaretoken", content)


class LoginFlowTests(TestCase):
    """Credential handling, validation and redirects."""

    PASSWORD = "CounterDesk#2026"

    def setUp(self):
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="owner",
            email="Owner@Pharmacy.com",
            password=self.PASSWORD,
        )

    def test_login_with_username_redirects_to_dashboard(self):
        response = self.client.post(
            self.url, {"username": "owner", "password": self.PASSWORD}
        )
        self.assertRedirects(response, "/dashboard/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_email_is_case_insensitive(self):
        response = self.client.post(
            self.url, {"username": "owner@pharmacy.com", "password": self.PASSWORD}
        )
        self.assertRedirects(response, "/dashboard/")

    def test_wrong_password_shows_generic_error(self):
        response = self.client.post(
            self.url, {"username": "owner", "password": "not-the-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email/username or password you entered is incorrect")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_account_shows_the_same_error(self):
        """The message must not reveal whether an account exists."""
        response = self.client.post(
            self.url, {"username": "nobody@pharmacy.com", "password": self.PASSWORD}
        )
        self.assertContains(response, "email/username or password you entered is incorrect")

    def test_empty_fields_are_reported_per_field(self):
        response = self.client.post(self.url, {"username": "", "password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter your email address or username.")
        self.assertContains(response, "Enter your password.")

    def test_inactive_account_is_rejected(self):
        """Deactivated accounts cannot sign in.

        Django's ModelBackend refuses inactive users, so authenticate() returns
        None and the form reports the same generic message as a wrong password.
        That is intentional — it keeps the response identical for every failure.
        """
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            self.url, {"username": "owner", "password": self.PASSWORD}
        )
        self.assertContains(response, "email/username or password you entered is incorrect")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_remember_me_keeps_the_session_alive(self):
        self.client.post(
            self.url,
            {"username": "owner", "password": self.PASSWORD, "remember_me": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_without_remember_me_session_ends_with_the_browser(self):
        self.client.post(self.url, {"username": "owner", "password": self.PASSWORD})
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_safe_next_parameter_is_honoured(self):
        response = self.client.post(
            f"{self.url}?next=/dashboard/",
            {"username": "owner", "password": self.PASSWORD},
        )
        self.assertRedirects(response, "/dashboard/")

    def test_external_next_parameter_is_ignored(self):
        response = self.client.post(
            f"{self.url}?next=https://evil.example.com/",
            {"username": "owner", "password": self.PASSWORD},
        )
        self.assertRedirects(response, "/dashboard/")

    def test_authenticated_user_is_sent_past_the_login_page(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, "/dashboard/")


class LogoutTests(TestCase):
    PASSWORD = "CounterDesk#2026"

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner", email="owner@pharmacy.com", password=self.PASSWORD
        )

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_clears_the_session_and_returns_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class AccessControlTests(TestCase):
    """The placeholder dashboard is already behind authentication."""

    def test_anonymous_visitor_is_redirected_to_login(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/dashboard/")

    def test_root_url_redirects_anonymous_visitor_to_login(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("accounts:login"))

    def test_root_url_redirects_signed_in_user_to_dashboard(self):
        user = User.objects.create_user(
            username="owner", email="owner@pharmacy.com", password="CounterDesk#2026"
        )
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertRedirects(response, "/dashboard/")
