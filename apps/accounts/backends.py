"""Authentication backends."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate against either the username or the email address.

    The login form has a single "Email or username" field, so the value has to
    be matched against both columns. Matching is case-insensitive, which is what
    users expect from an email address.

    Everything security-relevant (password hashing, ``is_active`` handling,
    permissions) is inherited from Django's :class:`ModelBackend`.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD) or kwargs.get("email")

        if not username or password is None:
            return None

        lookup = Q(**{f"{UserModel.USERNAME_FIELD}__iexact": username}) | Q(
            email__iexact=username
        )
        candidates = list(UserModel._default_manager.filter(lookup).order_by("pk")[:2])

        if not candidates:
            # Run the hasher anyway so a missing account and a wrong password
            # take a comparable amount of time (see Django's ModelBackend).
            UserModel().set_password(password)
            return None

        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
