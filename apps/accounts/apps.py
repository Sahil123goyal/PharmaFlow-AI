from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Owner/Admin authentication and user management."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"
