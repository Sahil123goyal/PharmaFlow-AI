"""Root URL configuration for PharmaFlowAI.

Feature modules (medicines, inventory, suppliers, customers, billing,
analytics) get their own ``include()`` line here as they are built.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]
