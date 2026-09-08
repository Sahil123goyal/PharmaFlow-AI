from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.RootRedirectView.as_view(), name="root"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("modules/<slug:module>/", views.ModuleView.as_view(), name="module"),
    path("modules/<slug:module>/save/", views.ModuleSaveView.as_view(), name="module_save"),
    path("modules/<slug:module>/delete/", views.ModuleDeleteView.as_view(), name="module_delete"),
    path("chat/", views.ChatbotView.as_view(), name="chat"),
]
