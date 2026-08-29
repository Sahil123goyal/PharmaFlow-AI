"""Tests for the Medicine model and its queryset helpers."""

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.medicines.models import Medicine, squash_whitespace


class SqueezeWhitespaceTests(TestCase):
    def test_collapses_runs_and_strips_edges(self):
        self.assertEqual(squash_whitespace("  Crocin   Advance  "), "Crocin Advance")

    def test_passes_empty_values_through(self):
        self.assertEqual(squash_whitespace(""), "")
        self.assertIsNone(squash_whitespace(None))


class MedicineModelTests(TestCase):
    def test_save_normalises_text_fields(self):
        medicine = Medicine.objects.create(
            name="  Crocin   Advance ",
            generic_name=" Paracetamol  ",
            strength=" 500   mg ",
            category="  Analgesic ",
            manufacturer=" GSK  ",
        )
        medicine.refresh_from_db()

        self.assertEqual(medicine.name, "Crocin Advance")
        self.assertEqual(medicine.generic_name, "Paracetamol")
        self.assertEqual(medicine.strength, "500 mg")
        self.assertEqual(medicine.category, "Analgesic")
        self.assertEqual(medicine.manufacturer, "GSK")

    def test_label_includes_strength_when_present(self):
        medicine = Medicine(name="Crocin", strength="500 mg")
        self.assertEqual(medicine.label, "Crocin 500 mg")
        self.assertEqual(str(medicine), "Crocin 500 mg")

    def test_label_falls_back_to_name_without_strength(self):
        self.assertEqual(Medicine(name="Betadine").label, "Betadine")

    def test_status_label_tracks_is_active(self):
        self.assertEqual(Medicine(is_active=True).status_label, "Active")
        self.assertEqual(Medicine(is_active=False).status_label, "Inactive")

    def test_defaults_are_active_tablet_and_non_prescription(self):
        medicine = Medicine.objects.create(name="Vitamin C")
        self.assertTrue(medicine.is_active)
        self.assertEqual(medicine.unit, Medicine.Unit.TABLET)
        self.assertFalse(medicine.prescription_required)

    def test_duplicate_is_rejected_case_insensitively(self):
        Medicine.objects.create(name="Crocin", strength="500 mg", manufacturer="GSK")

        # The database constraint is the last line of defence behind form validation.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Medicine.objects.create(
                name="crocin", strength="500 MG", manufacturer="gsk"
            )

    def test_same_name_with_different_strength_is_allowed(self):
        Medicine.objects.create(name="Dolo", strength="650 mg", manufacturer="Micro")
        Medicine.objects.create(name="Dolo", strength="500 mg", manufacturer="Micro")
        self.assertEqual(Medicine.objects.filter(name="Dolo").count(), 2)

    def test_same_name_from_a_different_manufacturer_is_allowed(self):
        Medicine.objects.create(name="Paracetamol", strength="500 mg", manufacturer="Cipla")
        Medicine.objects.create(name="Paracetamol", strength="500 mg", manufacturer="Sun")
        self.assertEqual(Medicine.objects.filter(name="Paracetamol").count(), 2)

    def test_default_ordering_is_by_name_then_strength(self):
        Medicine.objects.create(name="Zincovit")
        Medicine.objects.create(name="Aspirin", strength="150 mg")
        Medicine.objects.create(name="Aspirin", strength="075 mg")

        labels = [medicine.label for medicine in Medicine.objects.all()]
        self.assertEqual(labels, ["Aspirin 075 mg", "Aspirin 150 mg", "Zincovit"])


class MedicineQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active = Medicine.objects.create(
            name="Augmentin",
            generic_name="Amoxicillin + Clavulanic acid",
            strength="625 mg",
            category="Antibiotic",
            manufacturer="GSK",
        )
        cls.inactive = Medicine.objects.create(
            name="Withdrawn Syrup",
            category="Respiratory",
            manufacturer="Cipla",
            is_active=False,
        )
        cls.uncategorised = Medicine.objects.create(name="Saline Drops")

    def test_active_and_inactive_split_the_catalogue(self):
        self.assertNotIn(self.inactive, Medicine.objects.active())
        self.assertIn(self.active, Medicine.objects.active())
        self.assertEqual(list(Medicine.objects.inactive()), [self.inactive])

    def test_search_matches_brand_name(self):
        self.assertEqual(list(Medicine.objects.search("augment")), [self.active])

    def test_search_matches_generic_name(self):
        self.assertEqual(list(Medicine.objects.search("clavulanic")), [self.active])

    def test_search_matches_manufacturer(self):
        self.assertEqual(list(Medicine.objects.search("gsk")), [self.active])

    def test_blank_search_returns_everything(self):
        self.assertEqual(Medicine.objects.search("   ").count(), 3)
        self.assertEqual(Medicine.objects.search(None).count(), 3)

    def test_categories_are_distinct_sorted_and_exclude_blanks(self):
        Medicine.objects.create(name="Mox", category="Antibiotic", manufacturer="Ranbaxy")
        self.assertEqual(
            list(Medicine.objects.categories()), ["Antibiotic", "Respiratory"]
        )
