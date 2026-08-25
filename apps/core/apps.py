from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared, cross-module plumbing for PharmaFlowAI."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
