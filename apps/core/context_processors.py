"""Template context processors shared across every PharmaFlowAI page."""

from django.conf import settings


def branding(request):
    """Expose the product name and tagline to all templates."""
    return {
        "PROJECT_NAME": getattr(settings, "PROJECT_NAME", "PharmaFlowAI"),
        "PROJECT_TAGLINE": getattr(
            settings, "PROJECT_TAGLINE", "Smart Pharmacy Management, Simplified"
        ),
    }
