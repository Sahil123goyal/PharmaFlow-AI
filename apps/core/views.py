"""Core views.

Only the entry-point redirect and a deliberately empty ``/dashboard/`` landing
stub live here. The real dashboard is a later iteration; this stub exists so the
post-login redirect required by the login flow resolves to a real page.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View


class RootRedirectView(View):
    """Send visitors to the dashboard when signed in, otherwise to login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("core:dashboard"))
        return redirect(reverse("accounts:login"))


class DashboardPlaceholderView(LoginRequiredMixin, TemplateView):
    """Placeholder for the owner dashboard.

    Intentionally contains no dashboard functionality — no medicine, inventory,
    billing, supplier, customer or analytics data. It only confirms that
    session authentication worked and gives the user a way to sign out.
    """

    template_name = "core/dashboard_placeholder.html"
