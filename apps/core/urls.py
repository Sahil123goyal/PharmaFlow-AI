from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.RootRedirectView.as_view(), name="root"),
    path("dashboard/", views.DashboardPlaceholderView.as_view(), name="dashboard"),
]
