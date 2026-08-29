"""Core views.

The entry-point redirect and the dashboard landing page. The dashboard summarises
whatever modules exist; today that is the medicine catalogue only, and it reports
real counts rather than placeholder figures.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from apps.medicines.models import Medicine


class RootRedirectView(View):
    """Send visitors to the dashboard when signed in, otherwise to login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("core:dashboard"))
        return redirect(reverse("accounts:login"))


class DashboardView(LoginRequiredMixin, TemplateView):
    """Owner landing page.

    Deliberately limited: it shows catalogue counts and the signed-in account,
    because those are the only facts the system currently holds. Stock levels,
    sales figures and alerts arrive with the modules that produce them.
    """

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # One query for all three figures.
        counts = Medicine.objects.aggregate(
            total=Count("pk"),
            active=Count("pk", filter=Q(is_active=True)),
            inactive=Count("pk", filter=Q(is_active=False)),
        )
        context.update(
            medicine_counts=counts,
            category_count=Medicine.objects.categories().count(),
            recent_medicines=Medicine.objects.order_by("-created_at")[:5],
        )
        return context
