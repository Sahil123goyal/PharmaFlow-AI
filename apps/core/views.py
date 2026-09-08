"""Core views for the dashboard and its lightweight prototype modules."""

import json
from copy import deepcopy

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from apps.medicines.models import Medicine


# These records intentionally live in session state. They make the unfinished
# modules useful in a demo without pretending they are persisted business data.
MODULE_DEFINITIONS = {
    "inventory": {
        "label": "Inventory",
        "description": "Track on-hand quantities and reorder points at a glance.",
        "primary_key": "medicine",
        "fields": [
            {"key": "medicine", "label": "Medicine", "placeholder": "e.g. Paracetamol 500 mg"},
            {"key": "quantity", "label": "Quantity", "input_type": "number", "placeholder": "0"},
            {"key": "reorder_level", "label": "Reorder level", "input_type": "number", "placeholder": "0"},
            {"key": "status", "label": "Status", "placeholder": "Healthy, Low stock or Expiring"},
            {"key": "location", "label": "Shelf / location", "placeholder": "e.g. A-12"},
        ],
        "rows": [
            {"id": "inv-1", "medicine": "Paracetamol 500 mg", "quantity": "124", "reorder_level": "40", "status": "Healthy", "location": "A-12"},
            {"id": "inv-2", "medicine": "Amoxicillin 250 mg", "quantity": "18", "reorder_level": "25", "status": "Low stock", "location": "B-04"},
            {"id": "inv-3", "medicine": "Cetirizine 10 mg", "quantity": "62", "reorder_level": "20", "status": "Healthy", "location": "A-18"},
            {"id": "inv-4", "medicine": "Insulin Glargine", "quantity": "9", "reorder_level": "12", "status": "Expiring soon", "location": "Cold-02"},
        ],
    },
    "billing": {
        "label": "Billing",
        "description": "Review recent bills and keep the counter queue moving.",
        "primary_key": "invoice",
        "fields": [
            {"key": "invoice", "label": "Invoice number", "placeholder": "e.g. INV-1048"},
            {"key": "customer", "label": "Customer", "placeholder": "Customer name"},
            {"key": "items", "label": "Items", "placeholder": "e.g. 3 items"},
            {"key": "amount", "label": "Amount", "placeholder": "e.g. Rs 420"},
            {"key": "status", "label": "Status", "placeholder": "Paid, Pending or Refunded"},
        ],
        "rows": [
            {"id": "bill-1", "invoice": "INV-1048", "customer": "Aarav Mehta", "items": "3 items", "amount": "Rs 420", "status": "Paid"},
            {"id": "bill-2", "invoice": "INV-1047", "customer": "Maya Shah", "items": "5 items", "amount": "Rs 1,180", "status": "Paid"},
            {"id": "bill-3", "invoice": "INV-1046", "customer": "Walk-in customer", "items": "1 item", "amount": "Rs 95", "status": "Pending"},
        ],
    },
    "suppliers": {
        "label": "Suppliers",
        "description": "Keep your medicine partners and their current standing together.",
        "primary_key": "name",
        "fields": [
            {"key": "name", "label": "Supplier", "placeholder": "Company name"},
            {"key": "contact", "label": "Contact", "placeholder": "Phone or email"},
            {"key": "medicines", "label": "Medicine lines", "placeholder": "e.g. 24"},
            {"key": "status", "label": "Status", "placeholder": "Active or On hold"},
        ],
        "rows": [
            {"id": "sup-1", "name": "Cipla Distribution", "contact": "orders@cipla.example", "medicines": "24", "status": "Active"},
            {"id": "sup-2", "name": "Sun Pharma Wholesale", "contact": "+91 98765 10203", "medicines": "18", "status": "Active"},
            {"id": "sup-3", "name": "MedCart Logistics", "contact": "dispatch@medcart.example", "medicines": "8", "status": "On hold"},
        ],
    },
    "customers": {
        "label": "Customers",
        "description": "A simple view of regular customers and their recent activity.",
        "primary_key": "name",
        "fields": [
            {"key": "name", "label": "Customer", "placeholder": "Full name"},
            {"key": "phone", "label": "Phone", "placeholder": "+91 ..."},
            {"key": "last_order", "label": "Last order", "placeholder": "e.g. Today"},
            {"key": "status", "label": "Status", "placeholder": "Active or Inactive"},
        ],
        "rows": [
            {"id": "cust-1", "name": "Aarav Mehta", "phone": "+91 98765 44551", "last_order": "Today", "status": "Active"},
            {"id": "cust-2", "name": "Maya Shah", "phone": "+91 98111 22014", "last_order": "Yesterday", "status": "Active"},
            {"id": "cust-3", "name": "Rohan Kapoor", "phone": "+91 99003 18420", "last_order": "12 Aug 2026", "status": "Inactive"},
        ],
    },
    "analytics": {
        "label": "Analytics",
        "description": "A compact pulse check for the pharmacy owner.",
        "primary_key": "metric",
        "read_only": True,
        "fields": [],
        "rows": [
            {"id": "metric-1", "metric": "Sales this month", "value": "Rs 84,260", "change": "+12.4%", "period": "vs last month"},
            {"id": "metric-2", "metric": "Average bill value", "value": "Rs 386", "change": "+4.8%", "period": "vs last month"},
            {"id": "metric-3", "metric": "Top category", "value": "Pain relief", "change": "28% of sales", "period": "this month"},
            {"id": "metric-4", "metric": "Returning customers", "value": "64", "change": "+9", "period": "this month"},
        ],
    },
}

MODULE_ORDER = ("inventory", "billing", "suppliers", "customers", "analytics")


def get_module_definition(slug):
    try:
        return MODULE_DEFINITIONS[slug]
    except KeyError as exc:
        raise Http404("That dashboard module does not exist.") from exc


def get_module_rows(request, slug):
    stored = request.session.get("prototype_modules", {})
    if slug not in stored:
        stored[slug] = deepcopy(get_module_definition(slug)["rows"])
        request.session["prototype_modules"] = stored
        request.session.modified = True
    return stored[slug]


def save_module_rows(request, slug, rows):
    stored = request.session.get("prototype_modules", {})
    stored[slug] = rows
    request.session["prototype_modules"] = stored
    request.session.modified = True


def build_module_rows(definition, rows):
    columns = definition.get("columns") or definition.get("fields")
    if not columns:
        columns = [
            {"key": "metric", "label": "Metric"},
            {"key": "value", "label": "Value"},
            {"key": "change", "label": "Change"},
            {"key": "period", "label": "Period"},
        ]
    return [
        {
            "id": row["id"],
            "cells": [row.get(column["key"], "-") or "-" for column in columns],
            "primary": row.get(definition["primary_key"], "-"),
            "status": row.get("status", ""),
        }
        for row in rows
    ]


def module_summary(slug, rows):
    if slug == "inventory":
        attention = sum(row.get("status") != "Healthy" for row in rows)
        return {"total": len(rows), "total_label": "Tracked items", "attention": attention, "attention_label": "Need attention"}
    if slug == "billing":
        paid = sum(row.get("status") == "Paid" for row in rows)
        return {"total": len(rows), "total_label": "Recent bills", "attention": paid, "attention_label": "Paid"}
    if slug == "analytics":
        return {"total": len(rows), "total_label": "Key metrics", "attention": 12, "attention_label": "Sales growth %"}
    active = sum(row.get("status") == "Active" for row in rows)
    return {"total": len(rows), "total_label": "Records", "attention": active, "attention_label": "Active"}


class RootRedirectView(View):
    """Send visitors to the dashboard when signed in, otherwise to login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("core:dashboard"))
        return redirect(reverse("accounts:login"))


class DashboardView(LoginRequiredMixin, TemplateView):
    """Owner landing page with real catalogue counts and demo module signals."""

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = Medicine.objects.aggregate(
            total=Count("pk"),
            active=Count("pk", filter=Q(is_active=True)),
            inactive=Count("pk", filter=Q(is_active=False)),
        )
        module_cards = []
        for slug in MODULE_ORDER:
            definition = get_module_definition(slug)
            rows = get_module_rows(self.request, slug)
            module_cards.append(
                {
                    "slug": slug,
                    "label": definition["label"],
                    "description": definition["description"],
                    "count": len(rows),
                }
            )
        context.update(
            medicine_counts=counts,
            category_count=Medicine.objects.categories().count(),
            recent_medicines=Medicine.objects.order_by("-created_at")[:5],
            module_cards=module_cards,
            inventory_rows=get_module_rows(self.request, "inventory"),
        )
        return context


class ModuleView(LoginRequiredMixin, TemplateView):
    """Render one session-backed module with optional add/edit form state."""

    template_name = "core/module.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs["module"]
        definition = get_module_definition(slug)
        rows = get_module_rows(self.request, slug)
        editing_id = self.request.GET.get("edit", "")
        editing = next((row for row in rows if row["id"] == editing_id), None)
        show_form = not definition.get("read_only", False) and (
            self.request.GET.get("add") == "1" or editing is not None
        )
        context.update(
            module=definition,
            module_slug=slug,
            module_columns=definition.get("fields") or [
                {"key": "metric", "label": "Metric"},
                {"key": "value", "label": "Value"},
                {"key": "change", "label": "Change"},
                {"key": "period", "label": "Period"},
            ],
            module_rows=build_module_rows(definition, rows),
            module_summary=module_summary(slug, rows),
            show_form=show_form,
            editing=editing,
            form_values=editing or {},
        )
        context["module_column_count"] = len(context["module_columns"]) + (0 if definition.get("read_only", False) else 1)
        return context


class ModuleSaveView(LoginRequiredMixin, View):
    """Add or update a demo record in the current browser session."""

    def post(self, request, module, *args, **kwargs):
        definition = get_module_definition(module)
        if definition.get("read_only", False):
            return redirect("core:module", module=module)

        values = {
            field["key"]: request.POST.get(field["key"], "").strip()
            for field in definition["fields"]
        }
        missing = [field["label"] for field in definition["fields"] if not values[field["key"]]]
        record_id = request.POST.get("record_id", "").strip()
        if missing:
            messages.error(request, f"Please complete: {', '.join(missing)}.")
            query = f"?edit={record_id}" if record_id else "?add=1"
            return redirect(f"{reverse('core:module', kwargs={'module': module})}{query}")

        rows = get_module_rows(request, module)
        if record_id:
            record = next((row for row in rows if row["id"] == record_id), None)
            if record is None:
                messages.error(request, "That record is no longer available.")
            else:
                record.update(values)
                messages.success(request, "Record updated.")
        else:
            next_number = len(rows) + 1
            existing_ids = {row["id"] for row in rows}
            while f"{module}-{next_number}" in existing_ids:
                next_number += 1
            values["id"] = f"{module}-{next_number}"
            rows.append(values)
            messages.success(request, "Record added.")
        save_module_rows(request, module, rows)
        return redirect("core:module", module=module)


class ModuleDeleteView(LoginRequiredMixin, View):
    """Delete a demo record from the current browser session."""

    def post(self, request, module, *args, **kwargs):
        definition = get_module_definition(module)
        if definition.get("read_only", False):
            return redirect("core:module", module=module)
        record_id = request.POST.get("record_id", "").strip()
        rows = get_module_rows(request, module)
        remaining = [row for row in rows if row["id"] != record_id]
        if len(remaining) == len(rows):
            messages.error(request, "That record is no longer available.")
        else:
            save_module_rows(request, module, remaining)
            messages.success(request, "Record removed.")
        return redirect("core:module", module=module)


def chatbot_reply(message):
    """Small deterministic reply service that can later call an AI provider."""
    text = message.lower()
    if "inventory" in text or "stock" in text:
        return "Inventory has 4 tracked items. Amoxicillin is low at 18 units and Insulin Glargine needs an expiry check."
    if "sales" in text or "revenue" in text:
        return "The prototype dashboard shows Rs 84,260 in sales this month, up 12.4% from last month."
    if "order" in text or "bill" in text:
        return "There are 3 recent bills in the demo view. Two are paid and one is still pending."
    if "medicine" in text or "catalog" in text:
        return "You can search, filter, add, edit, deactivate and review medicines from the Medicines module."
    if "help" in text or "hello" in text or "hi" in text:
        return "I can help with medicines, stock, bills, sales and dashboard summaries. What would you like to check?"
    return "I can help with medicines, inventory, bills and sales. Try asking about low stock or this month's sales."


class ChatbotView(LoginRequiredMixin, View):
    """JSON endpoint for the prototype assistant."""

    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid request."}, status=400)
        message = str(payload.get("message", "")).strip()
        if not message:
            return JsonResponse({"error": "Message is required."}, status=400)
        return JsonResponse({"reply": chatbot_reply(message)})
