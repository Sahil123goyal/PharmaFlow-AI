"""Forms for the medicine catalogue.

Widget classes are set here rather than in the templates so every field renders with
the shared primitives from static/css/base.css, and so the generic field partial can
stay dumb.
"""

from django import forms
from django.db.models.functions import Lower

from .models import Medicine, squash_whitespace

#: Sort options offered on the list page, mapped to safe ORM ordering.
SORT_CHOICES = [
    ("name", "Name (A–Z)"),
    ("-name", "Name (Z–A)"),
    ("category", "Category"),
    ("-updated_at", "Recently updated"),
]

SORT_ORDERING = {
    "name": ["name", "strength"],
    "-name": ["-name", "strength"],
    "category": ["category", "name"],
    "-updated_at": ["-updated_at"],
}

TEXT_INPUT_CLASS = "field__input field__input--bare"


class MedicineForm(forms.ModelForm):
    """Create/update form for a catalogue entry."""

    class Meta:
        model = Medicine
        fields = [
            "name",
            "generic_name",
            "strength",
            "category",
            "manufacturer",
            "unit",
            "prescription_required",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "e.g. Crocin",
                    "autofocus": True,
                    "autocomplete": "off",
                }
            ),
            "generic_name": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "e.g. Paracetamol",
                    "autocomplete": "off",
                }
            ),
            "strength": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "e.g. 500 mg",
                    "autocomplete": "off",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "e.g. Analgesic",
                    # Autocompletes from categories already in the catalogue; the
                    # datalist is rendered by the template.
                    "list": "category-options",
                    "autocomplete": "off",
                }
            ),
            "manufacturer": forms.TextInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "placeholder": "e.g. Cipla",
                    "autocomplete": "off",
                }
            ),
            "unit": forms.Select(attrs={"class": "field__select"}),
            "prescription_required": forms.CheckboxInput(
                attrs={"class": "checkbox__input"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox__input"}),
        }

    def clean_name(self):
        # Normalise before the duplicate check so " Crocin " collides with "Crocin".
        name = squash_whitespace(self.cleaned_data.get("name"))
        if not name:
            raise forms.ValidationError("Enter the medicine name.")
        return name

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        if not name:
            return cleaned

        strength = squash_whitespace(cleaned.get("strength", "")) or ""
        manufacturer = squash_whitespace(cleaned.get("manufacturer", "")) or ""

        # The database constraint is the real guarantee, but it reports at form level.
        # Checking here as well lets the message sit on the field the owner must fix.
        duplicates = Medicine.objects.annotate(
            name_lower=Lower("name"),
            strength_lower=Lower("strength"),
            manufacturer_lower=Lower("manufacturer"),
        ).filter(
            name_lower=name.lower(),
            strength_lower=strength.lower(),
            manufacturer_lower=manufacturer.lower(),
        )
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            self.add_error(
                "name",
                "This medicine is already in the catalogue with the same strength "
                "and manufacturer.",
            )
        return cleaned


class MedicineFilterForm(forms.Form):
    """Search, filter and sort controls for the list page.

    A form rather than raw ``request.GET`` reads so the values are validated and
    round-trip back into the toolbar without extra template logic.
    """

    STATUS_CHOICES = [
        ("active", "Active only"),
        ("inactive", "Inactive only"),
        ("all", "All medicines"),
    ]

    q = forms.CharField(
        required=False,
        label="Search",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "field__input",
                "type": "search",
                "placeholder": "Search name, generic name or manufacturer",
                "autocomplete": "off",
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=STATUS_CHOICES,
        initial="active",
        widget=forms.Select(attrs={"class": "field__select"}),
    )
    category = forms.ChoiceField(
        required=False,
        label="Category",
        choices=[],  # populated in __init__ from the catalogue
        widget=forms.Select(attrs={"class": "field__select"}),
    )
    sort = forms.ChoiceField(
        required=False,
        label="Sort by",
        choices=SORT_CHOICES,
        initial="name",
        widget=forms.Select(attrs={"class": "field__select"}),
    )

    def __init__(self, *args, categories=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "All categories")] + [
            (value, value) for value in categories
        ]

    def clean_status(self):
        # An unrecognised or absent value falls back to the default view.
        return self.cleaned_data.get("status") or "active"

    def clean_sort(self):
        return self.cleaned_data.get("sort") or "name"

    def filters(self):
        """Return usable filter values, defaulting anything the form rejected.

        A hand-edited querystring (``?status=bogus``) should show the default list
        rather than an error page, so invalid input is treated as absent.
        """
        defaults = {"q": "", "status": "active", "category": "", "sort": "name"}
        if not self.is_valid():
            return defaults
        data = self.cleaned_data
        return {
            "q": (data.get("q") or "").strip(),
            "status": data.get("status") or defaults["status"],
            "category": data.get("category") or defaults["category"],
            "sort": data.get("sort") or defaults["sort"],
        }
