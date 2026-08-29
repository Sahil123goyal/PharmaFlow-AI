"""Medicine catalogue views.

Thin wrappers around Django's generic views: the interesting logic lives in the
queryset helpers on ``MedicineQuerySet`` and in the forms, so it stays testable
without a request.
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from .forms import SORT_ORDERING, MedicineFilterForm, MedicineForm
from .models import Medicine

logger = logging.getLogger(__name__)


class MedicineListView(LoginRequiredMixin, ListView):
    """Searchable, filterable, paginated catalogue listing.

    Pagination and filtering are required by the proposal (section 7) so the page
    stays usable as the catalogue grows.
    """

    model = Medicine
    template_name = "medicines/medicine_list.html"
    context_object_name = "medicines"
    paginate_by = 20

    def get_categories(self):
        if not hasattr(self, "_categories"):
            self._categories = list(Medicine.objects.categories())
        return self._categories

    def get_filter_form(self):
        if not hasattr(self, "_filter_form"):
            self._filter_form = MedicineFilterForm(
                self.request.GET, categories=self.get_categories()
            )
        return self._filter_form

    def get_queryset(self):
        selected = self.get_filter_form().filters()
        queryset = Medicine.objects.all()

        if selected["status"] == "active":
            queryset = queryset.active()
        elif selected["status"] == "inactive":
            queryset = queryset.inactive()

        if selected["category"]:
            queryset = queryset.filter(category=selected["category"])

        queryset = queryset.search(selected["q"])
        # filters() only ever returns a whitelisted sort key.
        return queryset.order_by(*SORT_ORDERING[selected["sort"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected = self.get_filter_form().filters()
        context.update(
            filter_form=self.get_filter_form(),
            categories=self.get_categories(),
            selected=selected,
            # Distinguishes "the catalogue is empty" from "this search found nothing".
            catalogue_is_empty=not Medicine.objects.exists(),
            is_filtered=bool(
                selected["q"] or selected["category"] or selected["status"] != "active"
            ),
            total_count=context["paginator"].count if context.get("paginator") else 0,
        )
        return context


class MedicineDetailView(LoginRequiredMixin, DetailView):
    model = Medicine
    template_name = "medicines/medicine_detail.html"
    context_object_name = "medicine"


class MedicineFormMixin:
    """Shared configuration for the create and update screens."""

    model = Medicine
    form_class = MedicineForm
    template_name = "medicines/medicine_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Feeds the <datalist> behind the category field.
        context["categories"] = list(Medicine.objects.categories())
        return context


class MedicineCreateView(LoginRequiredMixin, MedicineFormMixin, SuccessMessageMixin, CreateView):
    success_message = "%(name)s was added to the catalogue."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title="Add medicine", submit_label="Add medicine")
        return context


class MedicineUpdateView(LoginRequiredMixin, MedicineFormMixin, SuccessMessageMixin, UpdateView):
    success_message = "%(name)s was updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(page_title="Edit medicine", submit_label="Save changes")
        return context


class MedicineStatusView(LoginRequiredMixin, SingleObjectMixin, View):
    """Toggle a medicine between active and inactive.

    POST only: a GET must never change data, so a crawler or a stray link cannot
    deactivate stock. Mirrors the discipline used by the sign-out view.
    """

    model = Medicine
    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        medicine = self.get_object()
        medicine.is_active = not medicine.is_active
        medicine.save(update_fields=["is_active", "updated_at"])

        logger.info(
            "Medicine %s (%s) set to %s by %s",
            medicine.pk,
            medicine.label,
            medicine.status_label.lower(),
            request.user.get_username(),
        )
        messages.success(
            request,
            f"{medicine.label} is now {medicine.status_label.lower()}.",
        )
        return redirect(self.get_redirect_url(medicine))

    def get_redirect_url(self, medicine):
        """Return to wherever the action was triggered from, when it is safe to."""
        next_url = self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse("medicines:detail", args=[medicine.pk])
