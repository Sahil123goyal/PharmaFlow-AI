"""Authentication forms.

Built on Django's :class:`~django.contrib.auth.forms.AuthenticationForm` so all
of the framework's checks (inactive users, backend permission checks, session
handling) keep working. Only presentation, labels and the "Remember me" option
are added on top.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm


class PharmacyLoginForm(AuthenticationForm):
    """Sign-in form for the pharmacy Owner/Admin."""

    error_messages = {
        # Deliberately generic: do not reveal whether the account exists.
        # Django's ModelBackend refuses inactive users before the form runs, so
        # a deactivated account also lands on this message.
        "invalid_login": (
            "The email/username or password you entered is incorrect. "
            "Please check and try again."
        ),
        "inactive": (
            "This account has been deactivated. Contact the store owner to "
            "restore access."
        ),
    }

    remember_me = forms.BooleanField(
        label="Remember me",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "checkbox__input"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)

        self.fields["username"].label = "Email or username"
        self.fields["username"].error_messages["required"] = (
            "Enter your email address or username."
        )
        # AuthenticationForm caps this at the username column's length (150);
        # an email address may legitimately be longer.
        self.fields["username"].max_length = 254
        self.fields["username"].widget.attrs.update(
            {
                "class": "field__input",
                "placeholder": "owner@pharmacy.com",
                "autocomplete": "username",
                "autocapitalize": "none",
                "autocorrect": "off",
                "spellcheck": "false",
                "inputmode": "email",
                "maxlength": "254",
                "autofocus": True,
            }
        )

        self.fields["password"].label = "Password"
        self.fields["password"].error_messages["required"] = "Enter your password."
        self.fields["password"].widget.attrs.update(
            {
                "class": "field__input field__input--password",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        )
