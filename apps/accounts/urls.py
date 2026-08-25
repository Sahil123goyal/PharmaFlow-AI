from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.PharmacyLoginView.as_view(), name="login"),
    path("logout/", views.PharmacyLogoutView.as_view(), name="logout"),
    path("password-help/", views.PasswordHelpView.as_view(), name="password_help"),
    # Bare /accounts/ is not a page; send it to the sign-in form.
    path("", RedirectView.as_view(pattern_name="accounts:login"), name="index"),
]
