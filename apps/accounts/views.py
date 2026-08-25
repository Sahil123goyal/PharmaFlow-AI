"""Authentication views.

Thin wrappers around Django's session-based auth views. The only project
specific behaviour is the "Remember me" session lifetime and the logging of
sign-in outcomes.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView

from .forms import PharmacyLoginForm

logger = logging.getLogger(__name__)


class PharmacyLoginView(LoginView):
    """Owner/Admin sign-in.

    On success Django redirects to ``?next=`` when it is a safe local URL, and
    otherwise to ``settings.LOGIN_REDIRECT_URL`` (``/dashboard/``).
    """

    template_name = "accounts/login.html"
    authentication_form = PharmacyLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Log the user in, then apply the chosen session lifetime."""
        response = super().form_valid(form)

        remember_me = form.cleaned_data.get("remember_me")
        if remember_me:
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            # 0 -> the session cookie is discarded when the browser closes.
            self.request.session.set_expiry(0)

        logger.info(
            "Login succeeded for %s (remember_me=%s)",
            self.request.user.get_username(),
            bool(remember_me),
        )
        return response

    def form_invalid(self, form):
        logger.warning(
            "Login failed for identifier=%r", form.data.get("username", "")
        )
        return super().form_invalid(form)


class PharmacyLogoutView(LogoutView):
    """Sign out and return to the login page.

    Django only accepts POST here, which keeps sign-out safe from CSRF-style
    drive-by links.
    """

    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        # Flush the session first; the confirmation is then stored against the
        # fresh session and survives to the login page.
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been signed out.")
        return response


class PasswordHelpView(TemplateView):
    """Static guidance for the "Forgot password?" link.

    Real password recovery (email reset tokens) is intentionally out of scope for
    this iteration, so this page explains the manual reset path instead of
    pretending to send an email.
    """

    template_name = "accounts/password_help.html"
