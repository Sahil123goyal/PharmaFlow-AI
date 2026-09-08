"""Tests for the medicine catalogue views."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.medicines.models import Medicine

User = get_user_model()

PASSWORD = "CounterDesk#2026"


class SignedInTestCase(TestCase):
    """Base class that signs an owner in once per test class."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="owner", email="owner@pharmacy.com", password=PASSWORD
        )

    def setUp(self):
        self.client.force_login(self.user)


class AccessControlTests(TestCase):
    """Every catalogue route is behind the session login."""

    @classmethod
    def setUpTestData(cls):
        cls.medicine = Medicine.objects.create(name="Crocin", strength="500 mg")

    def test_routes_redirect_anonymous_users_to_login(self):
        login_url = reverse("accounts:login")
        routes = [
            reverse("medicines:list"),
            reverse("medicines:add"),
            reverse("medicines:detail", args=[self.medicine.pk]),
            reverse("medicines:edit", args=[self.medicine.pk]),
        ]
        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{login_url}?next={url}")

    def test_status_toggle_redirects_anonymous_users_to_login(self):
        url = reverse("medicines:status", args=[self.medicine.pk])
        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")
        self.medicine.refresh_from_db()
        self.assertTrue(self.medicine.is_active)


class ListViewTests(SignedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.crocin = Medicine.objects.create(
            name="Crocin",
            generic_name="Paracetamol",
            strength="500 mg",
            category="Analgesic",
            manufacturer="GSK",
        )
        cls.augmentin = Medicine.objects.create(
            name="Augmentin",
            generic_name="Amoxicillin",
            strength="625 mg",
            category="Antibiotic",
            manufacturer="Cipla",
        )
        cls.retired = Medicine.objects.create(
            name="Retired Tonic",
            category="Supplement",
            manufacturer="Dabur",
            is_active=False,
        )
        cls.url = reverse("medicines:list")

    def test_page_renders_inside_the_app_shell(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "medicines/medicine_list.html")
        self.assertTemplateUsed(response, "base_app.html")
        self.assertTemplateUsed(response, "partials/_sidebar.html")

    def test_defaults_to_active_medicines_only(self):
        response = self.client.get(self.url)
        medicines = list(response.context["medicines"])
        self.assertIn(self.crocin, medicines)
        self.assertNotIn(self.retired, medicines)

    def test_search_matches_generic_name(self):
        response = self.client.get(self.url, {"q": "amoxicillin"})
        self.assertEqual(list(response.context["medicines"]), [self.augmentin])

    def test_search_matches_manufacturer(self):
        response = self.client.get(self.url, {"q": "gsk"})
        self.assertEqual(list(response.context["medicines"]), [self.crocin])

    def test_category_filter_narrows_the_list(self):
        response = self.client.get(self.url, {"category": "Antibiotic"})
        self.assertEqual(list(response.context["medicines"]), [self.augmentin])

    def test_inactive_status_filter_shows_only_withdrawn_records(self):
        response = self.client.get(self.url, {"status": "inactive"})
        self.assertEqual(list(response.context["medicines"]), [self.retired])

    def test_all_status_filter_shows_everything(self):
        response = self.client.get(self.url, {"status": "all"})
        self.assertEqual(len(response.context["medicines"]), 3)

    def test_unrecognised_filter_values_fall_back_to_defaults(self):
        # A hand-edited querystring must not produce an error page.
        response = self.client.get(self.url, {"status": "bogus", "sort": "nonsense"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected"]["status"], "active")
        self.assertNotIn(self.retired, list(response.context["medicines"]))

    def test_sort_by_name_descending(self):
        response = self.client.get(self.url, {"sort": "-name"})
        names = [medicine.name for medicine in response.context["medicines"]]
        self.assertEqual(names, ["Crocin", "Augmentin"])

    def test_empty_catalogue_shows_the_first_run_prompt(self):
        Medicine.objects.all().delete()
        response = self.client.get(self.url)
        self.assertTrue(response.context["catalogue_is_empty"])
        self.assertContains(response, "No medicines yet")

    def test_fruitless_search_is_distinguished_from_an_empty_catalogue(self):
        response = self.client.get(self.url, {"q": "zzzznothing"})
        self.assertFalse(response.context["catalogue_is_empty"])
        self.assertContains(response, "No medicines match these filters")

    def test_sidebar_links_to_prototype_modules(self):
        content = self.client.get(self.url).content.decode()
        for module in ("inventory", "billing", "suppliers", "customers", "analytics"):
            self.assertIn(reverse("core:module", kwargs={"module": module}), content)
        self.assertNotIn("app__nav-item--soon", content)


class PaginationTests(SignedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for index in range(25):
            Medicine.objects.create(
                name=f"Medicine {index:02d}", category="Analgesic", manufacturer="Cipla"
            )
        cls.url = reverse("medicines:list")

    def test_first_page_holds_twenty_records(self):
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["medicines"]), 20)
        self.assertEqual(response.context["total_count"], 25)

    def test_second_page_holds_the_remainder(self):
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(response.context["medicines"]), 5)

    def test_filters_survive_a_page_change(self):
        response = self.client.get(self.url, {"q": "Medicine", "page": 2})
        self.assertEqual(response.context["page_obj"].number, 2)
        # The Previous link must carry the search term forward.
        self.assertContains(response, "q=Medicine")


class CreateViewTests(SignedInTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("medicines:add")

    def valid_payload(self, **overrides):
        payload = {
            "name": "Crocin Advance",
            "generic_name": "Paracetamol",
            "strength": "500 mg",
            "category": "Analgesic",
            "manufacturer": "GSK",
            "unit": Medicine.Unit.TABLET,
            "is_active": "on",
        }
        payload.update(overrides)
        return payload

    def test_form_renders_with_the_category_datalist(self):
        Medicine.objects.create(name="Mox", category="Antibiotic")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="category-options"')
        self.assertContains(response, '<option value="Antibiotic">')

    def test_valid_submission_creates_and_redirects_to_detail(self):
        response = self.client.post(self.url, self.valid_payload(), follow=True)
        medicine = Medicine.objects.get(name="Crocin Advance")
        self.assertRedirects(response, medicine.get_absolute_url())
        self.assertContains(response, "Crocin Advance was added to the catalogue.")

    def test_whitespace_is_normalised_on_the_way_in(self):
        self.client.post(self.url, self.valid_payload(name="  Crocin   Advance  "))
        self.assertTrue(Medicine.objects.filter(name="Crocin Advance").exists())

    def test_missing_name_is_rejected_with_a_field_error(self):
        response = self.client.post(self.url, self.valid_payload(name="   "))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Medicine.objects.exists())
        self.assertIn("name", response.context["form"].errors)

    def test_duplicate_shows_a_form_error_rather_than_a_server_error(self):
        Medicine.objects.create(name="Crocin Advance", strength="500 mg", manufacturer="GSK")

        response = self.client.post(
            self.url, self.valid_payload(name="crocin advance", manufacturer="gsk")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Medicine.objects.count(), 1)
        self.assertIn(
            "already in the catalogue", " ".join(response.context["form"].errors["name"])
        )


class UpdateViewTests(SignedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.medicine = Medicine.objects.create(
            name="Pan", strength="40 mg", category="Antacid", manufacturer="Alkem"
        )

    def test_form_is_prefilled(self):
        response = self.client.get(reverse("medicines:edit", args=[self.medicine.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["name"], "Pan")

    def test_valid_submission_updates_the_record(self):
        response = self.client.post(
            reverse("medicines:edit", args=[self.medicine.pk]),
            {
                "name": "Pan D",
                "generic_name": "Pantoprazole + Domperidone",
                "strength": "40 mg",
                "category": "Antacid",
                "manufacturer": "Alkem",
                "unit": Medicine.Unit.CAPSULE,
                "prescription_required": "on",
                "is_active": "on",
            },
            follow=True,
        )
        self.medicine.refresh_from_db()

        self.assertRedirects(response, self.medicine.get_absolute_url())
        self.assertEqual(self.medicine.name, "Pan D")
        self.assertEqual(self.medicine.unit, Medicine.Unit.CAPSULE)
        self.assertTrue(self.medicine.prescription_required)
        self.assertContains(response, "Pan D was updated.")

    def test_editing_without_changing_the_name_is_not_a_duplicate(self):
        response = self.client.post(
            reverse("medicines:edit", args=[self.medicine.pk]),
            {
                "name": "Pan",
                "strength": "40 mg",
                "manufacturer": "Alkem",
                "category": "Gastro",
                "unit": Medicine.Unit.TABLET,
                "is_active": "on",
            },
        )
        self.medicine.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.medicine.category, "Gastro")


class StatusToggleTests(SignedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.medicine = Medicine.objects.create(name="Shelcal", strength="500 mg")

    def url(self):
        return reverse("medicines:status", args=[self.medicine.pk])

    def test_post_deactivates_and_reports_back(self):
        response = self.client.post(self.url(), follow=True)
        self.medicine.refresh_from_db()

        self.assertFalse(self.medicine.is_active)
        self.assertRedirects(response, self.medicine.get_absolute_url())
        self.assertContains(response, "Shelcal 500 mg is now inactive.")

    def test_post_reactivates_an_inactive_medicine(self):
        Medicine.objects.filter(pk=self.medicine.pk).update(is_active=False)
        self.client.post(self.url())
        self.medicine.refresh_from_db()
        self.assertTrue(self.medicine.is_active)

    def test_get_is_not_allowed(self):
        # A GET must never mutate data.
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 405)
        self.medicine.refresh_from_db()
        self.assertTrue(self.medicine.is_active)

    def test_safe_next_returns_to_the_originating_page(self):
        target = f"{reverse('medicines:list')}?status=all"
        response = self.client.post(self.url(), {"next": target})
        self.assertRedirects(response, target)

    def test_unsafe_next_is_ignored(self):
        response = self.client.post(self.url(), {"next": "https://evil.example.com/"})
        self.assertRedirects(response, self.medicine.get_absolute_url())


class DetailViewTests(SignedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.medicine = Medicine.objects.create(
            name="Allegra",
            generic_name="Fexofenadine",
            strength="120 mg",
            category="Antihistamine",
            manufacturer="Sanofi",
            prescription_required=True,
        )

    def test_page_shows_the_record_and_its_actions(self):
        response = self.client.get(self.medicine.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "medicines/medicine_detail.html")
        self.assertContains(response, "Allegra 120 mg")
        self.assertContains(response, "Fexofenadine")
        self.assertContains(response, "Prescription only")
        self.assertContains(response, reverse("medicines:edit", args=[self.medicine.pk]))
        self.assertContains(response, "Deactivate")

    def test_inactive_record_offers_reactivation(self):
        Medicine.objects.filter(pk=self.medicine.pk).update(is_active=False)
        response = self.client.get(self.medicine.get_absolute_url())
        self.assertContains(response, "Reactivate")

    def test_missing_record_returns_404(self):
        response = self.client.get(reverse("medicines:detail", args=[999_999]))
        self.assertEqual(response.status_code, 404)


class DashboardTests(SignedInTestCase):
    def test_dashboard_reports_real_catalogue_counts(self):
        Medicine.objects.create(name="Crocin", category="Analgesic")
        Medicine.objects.create(name="Mox", category="Antibiotic")
        Medicine.objects.create(name="Old Tonic", category="Analgesic", is_active=False)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")
        self.assertEqual(response.context["medicine_counts"]["total"], 3)
        self.assertEqual(response.context["medicine_counts"]["active"], 2)
        self.assertEqual(response.context["medicine_counts"]["inactive"], 1)
        self.assertEqual(response.context["category_count"], 2)
        self.assertContains(response, "Recently added")
