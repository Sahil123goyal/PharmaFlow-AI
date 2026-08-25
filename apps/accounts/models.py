"""User model for PharmaFlowAI.

The project defines its own user model from day one. Swapping ``AUTH_USER_MODEL``
after tables exist is disruptive, so the model is introduced here even though
this iteration only needs sign-in. Everything else still comes from Django's
built-in auth framework (password hashing, permissions, sessions).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A person who can sign in to PharmaFlowAI.

    For a small independent pharmacy this is normally a single Owner/Admin
    account, with room for counter staff later.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner / Admin"
        PHARMACIST = "PHARMACIST", "Pharmacist"

    # Unique + required so the email can be used as a sign-in identifier.
    email = models.EmailField("email address", unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OWNER,
        help_text="Controls what the account may access in later modules.",
    )

    class Meta(AbstractUser.Meta):
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def display_name(self):
        """Short, friendly name for the UI."""
        return self.first_name or self.get_username()

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER
