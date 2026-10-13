"""A single catalogue snapshot for report views and assistant summaries."""

from collections import Counter

from django.utils import timezone

from apps.medicines.models import Medicine


def catalogue_snapshot():
    medicines = list(Medicine.objects.order_by("name", "strength", "pk"))
    categories = Counter(item.category or "Uncategorised" for item in medicines)
    return {
        "medicines": medicines,
        "generated_at": timezone.now(),
        "total": len(medicines),
        "active": sum(item.is_active for item in medicines),
        "inactive": sum(not item.is_active for item in medicines),
        "prescription_required": sum(item.prescription_required for item in medicines),
        "category_summary": sorted(categories.items()),
        "category_count": len(categories),
    }
