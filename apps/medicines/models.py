"""Medicine catalogue models.

The medicine record is the master data every later PharmaFlowAI module points at:
batches belong to a medicine, and bill lines reference a medicine. Deliberately no
stock, quantity or price fields — those belong to batch inventory in the next
iteration, because a medicine can have many batches at different prices.

Proposal reference (UCS503P, section 4.4): "Medicine — Name, generic name, category,
manufacturer, unit, status. Maintains the master medicine catalogue."
"""

import re

from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse

#: Runs of whitespace, including newlines pasted in from a spreadsheet.
_WHITESPACE = re.compile(r"\s+")


def squash_whitespace(value):
    """Trim a text value and collapse internal whitespace runs to one space.

    Free-text fields invite inconsistent entry ("Cipla  Ltd" vs "Cipla Ltd"), which
    would fragment the category filter and defeat duplicate detection. Normalising on
    save keeps the catalogue tidy without forcing the owner to be careful.
    """
    if not value:
        return value
    return _WHITESPACE.sub(" ", value).strip()


class MedicineQuerySet(models.QuerySet):
    """Query helpers shared by the views, the seed command and the tests."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def search(self, term):
        """Match a term against the fields an owner would actually search by.

        Name, generic name and manufacturer — brand or molecule, whichever the owner
        remembers. Category is excluded on purpose: it has its own filter.
        """
        term = (term or "").strip()
        if not term:
            return self
        return self.filter(
            models.Q(name__icontains=term)
            | models.Q(generic_name__icontains=term)
            | models.Q(manufacturer__icontains=term)
        )

    def categories(self):
        """Distinct non-empty categories in use, for filters and autocomplete."""
        return (
            self.exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )


class Medicine(models.Model):
    """A product in the pharmacy's catalogue.

    Medicines are deactivated rather than deleted (proposal section 9.1: "create,
    view, update and deactivate operations"). A discontinued medicine still has to
    remain readable, because past bills and batches refer to it.
    """

    class Unit(models.TextChoices):
        """How the medicine is dispensed. Drives batch quantities later."""

        TABLET = "TABLET", "Tablet"
        CAPSULE = "CAPSULE", "Capsule"
        SYRUP = "SYRUP", "Syrup / bottle"
        INJECTION = "INJECTION", "Injection / vial"
        OINTMENT = "OINTMENT", "Cream / ointment"
        DROPS = "DROPS", "Drops"
        SACHET = "SACHET", "Sachet / powder"
        OTHER = "OTHER", "Other"

    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Brand name as printed on the pack, e.g. Crocin.",
    )
    generic_name = models.CharField(
        "generic name",
        max_length=200,
        blank=True,
        help_text="Molecule or composition, e.g. Paracetamol. Used for substitution.",
    )
    strength = models.CharField(
        max_length=50,
        blank=True,
        help_text="Dosage per unit, e.g. 500 mg or 10 mg/5 ml.",
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Therapeutic group, e.g. Analgesic. Reused across medicines.",
    )
    manufacturer = models.CharField(max_length=150, blank=True)
    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.TABLET,
        help_text="How this medicine is counted and sold.",
    )
    prescription_required = models.BooleanField(
        "prescription required",
        default=False,
        help_text="Tick for medicines that may only be sold against a prescription.",
    )
    # The proposal's "status" field. A boolean rather than a choice because there are
    # only ever two states, and it keeps the list query indexable.
    is_active = models.BooleanField(
        "active",
        default=True,
        db_index=True,
        help_text="Inactive medicines stay on record but are hidden from daily use.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MedicineQuerySet.as_manager()

    class Meta:
        ordering = ["name", "strength"]
        verbose_name = "medicine"
        verbose_name_plural = "medicines"
        constraints = [
            # Case-insensitive, so "crocin" cannot be added alongside "Crocin".
            # Strength and manufacturer are part of the key because Paracetamol 500
            # and Paracetamol 650 are genuinely different products, as are the same
            # brand from two manufacturers.
            models.UniqueConstraint(
                Lower("name"),
                Lower("strength"),
                Lower("manufacturer"),
                name="medicine_unique_name_strength_manufacturer",
                violation_error_message=(
                    "A medicine with this name, strength and manufacturer already "
                    "exists in the catalogue."
                ),
            ),
        ]
        indexes = [
            # Matches the default list query: active medicines ordered by name.
            models.Index(fields=["is_active", "name"], name="medicine_active_name_idx"),
        ]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        for field in ("name", "generic_name", "strength", "category", "manufacturer"):
            setattr(self, field, squash_whitespace(getattr(self, field)))
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("medicines:detail", args=[self.pk])

    @property
    def label(self):
        """Name and strength together, as staff would say it at the counter."""
        return f"{self.name} {self.strength}".strip() if self.strength else self.name

    @property
    def status_label(self):
        return "Active" if self.is_active else "Inactive"
