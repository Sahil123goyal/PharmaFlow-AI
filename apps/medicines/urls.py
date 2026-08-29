from django.urls import path

from . import views

app_name = "medicines"

urlpatterns = [
    path("", views.MedicineListView.as_view(), name="list"),
    path("add/", views.MedicineCreateView.as_view(), name="add"),
    path("<int:pk>/", views.MedicineDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.MedicineUpdateView.as_view(), name="edit"),
    # POST only — flips the active flag.
    path("<int:pk>/status/", views.MedicineStatusView.as_view(), name="status"),
]
