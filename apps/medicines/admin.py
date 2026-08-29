"""Django admin registration for the medicine catalogue.

The owner-facing screens are the primary interface; the admin is a fallback for bulk
corrections and for inspecting records during development.
"""

from django.contrib import admin

from .models import Medicine


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "strength",
        "generic_name",
        "category",
        "manufacturer",
        "unit",
        "prescription_required",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active", "prescription_required", "unit", "category")
    search_fields = ("name", "generic_name", "manufacturer", "category")
    ordering = ("name", "strength")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "generic_name", "strength")}),
        ("Classification", {"fields": ("category", "manufacturer", "unit")}),
        ("Dispensing", {"fields": ("prescription_required", "is_active")}),
        ("Record", {"fields": ("created_at", "updated_at")}),
    )
