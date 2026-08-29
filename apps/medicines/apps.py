from django.apps import AppConfig


class MedicinesConfig(AppConfig):
    """Master medicine catalogue."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.medicines"
    verbose_name = "Medicines"
