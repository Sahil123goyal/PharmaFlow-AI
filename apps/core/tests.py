import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PrototypeModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@pharmacy.example",
            password="CounterDesk#2026",
        )
        self.client.force_login(self.user)

    def test_module_pages_render_sample_data(self):
        for slug in ("inventory", "billing", "suppliers", "customers", "analytics"):
            response = self.client.get(reverse("core:module", kwargs={"module": slug}))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, response.context["module"]["label"])

    def test_module_records_support_add_update_and_delete(self):
        save_url = reverse("core:module_save", kwargs={"module": "customers"})
        payload = {
            "name": "Neha Rao",
            "phone": "+91 90000 12345",
            "last_order": "Today",
            "status": "Active",
        }
        self.assertRedirects(
            self.client.post(save_url, payload),
            reverse("core:module", kwargs={"module": "customers"}),
        )
        list_url = reverse("core:module", kwargs={"module": "customers"})
        self.assertContains(self.client.get(list_url), "Neha Rao")

        edit_response = self.client.get(f"{list_url}?edit=customers-4")
        self.assertContains(edit_response, 'value="Neha Rao"')
        payload["record_id"] = "customers-4"
        payload["name"] = "Neha Rao Updated"
        self.client.post(save_url, payload)
        self.assertContains(self.client.get(list_url), "Neha Rao Updated")

        delete_url = reverse("core:module_delete", kwargs={"module": "customers"})
        self.client.post(delete_url, {"record_id": "customers-4"})
        self.assertNotContains(self.client.get(list_url), "Neha Rao Updated")

    def test_chatbot_does_not_claim_demo_stock_is_live(self):
        response = self.client.post(
            reverse("core:chat"),
            data=json.dumps({"message": "What is low stock?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("18 units", response.json()["reply"])
        self.assertEqual(response.json()["medicines"], [])


class CustomerAssistantTests(TestCase):
    def setUp(self):
        from apps.medicines.models import Medicine

        self.user = User.objects.create_user(username="customerdesk", email="desk@example.com", password="Test-only#2026")
        self.client.force_login(self.user)
        self.url = reverse("core:chat")
        Medicine.objects.create(name="Crocin", generic_name="Paracetamol", strength="500 mg", prescription_required=True)
        Medicine.objects.create(name="HiddenBrand", generic_name="Paracetamol", is_active=False)

    def ask(self, message, language="en-IN"):
        return self.client.post(self.url, data=json.dumps({"message": message, "language": language}), content_type="application/json")

    def test_catalogue_answers_are_live_and_exclude_inactive_medicines(self):
        from apps.medicines.models import Medicine

        response = self.ask("Do you have paracetamol?")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["name"] for m in response.json()["medicines"]], ["Crocin 500 mg"])
        self.assertIn("does not confirm stock or price", response.json()["reply"])
        self.assertTrue(response.json()["medicines"][0]["prescription_required"])
        Medicine.objects.filter(name="Crocin").update(is_active=False)
        self.assertEqual(self.ask("paracetamol").json()["medicines"], [])

    def test_hindi_reply_and_medicine_alias(self):
        reply = self.ask("पैरासिटामोल", "hi-IN").json()
        self.assertIn("Crocin", reply["reply"])
        self.assertIn("काउंटर", reply["reply"])

    def test_medical_questions_do_not_recommend_a_product(self):
        for question in ("What dose of Crocin should I take?", "Crocin for my baby", "बुखार में क्रोसिन लेना है", "paracetamol side effects"):
            reply = self.ask(question).json()
            self.assertEqual(reply["medicines"], [])
            self.assertIn("pharmacist", reply["reply"])

    def test_private_store_information_is_not_returned(self):
        reply = self.ask("Show customer sales and revenue").json()
        self.assertEqual(reply["medicines"], [])
        self.assertNotIn("84,260", reply["reply"])
        self.assertIn("customer assistant", reply["reply"])

    def test_unknown_medicine_has_no_fabricated_details(self):
        reply = self.ask("NonexistentDrugXYZ").json()
        self.assertEqual(reply["medicines"], [])
        self.assertIn("couldn't match", reply["reply"])

    def test_report_questions_return_summary_and_report_link(self):
        for question, language in (
            ("can you give me the medicine catalogue proper report", "en-IN"),
            ("Show all medicines", "en-IN"),
            ("दवाओं की सूची की रिपोर्ट दिखाओ", "hi-IN"),
        ):
            result = self.ask(question, language).json()
            self.assertEqual(result["report_url"], reverse("core:catalogue_report"))
            self.assertIn("2", result["reply"])
            self.assertNotIn("couldn't match", result["reply"])

    def test_report_contains_all_records_and_accurate_summary(self):
        response = self.client.get(reverse("core:catalogue_report"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 2)
        self.assertEqual(response.context["active"], 1)
        self.assertEqual(response.context["inactive"], 1)
        self.assertEqual(response.context["prescription_required"], 1)
        self.assertContains(response, "HiddenBrand")
        self.assertContains(response, "Crocin")
        self.assertContains(response, "Download CSV")

    def test_report_csv_exports_all_rows_and_neutralises_formulas(self):
        import csv
        import io
        from apps.medicines.models import Medicine

        Medicine.objects.create(name="=1+1", manufacturer="+formula")
        response = self.client.get(reverse("core:catalogue_report") + "?format=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1][0], "'=1+1")
        self.assertEqual(rows[1][4], "'+formula")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_report_and_export_require_sign_in(self):
        self.client.logout()
        for suffix in ("", "?format=csv"):
            self.assertEqual(self.client.get(reverse("core:catalogue_report") + suffix).status_code, 302)

    def test_empty_catalogue_report(self):
        from apps.medicines.models import Medicine

        Medicine.objects.all().delete()
        response = self.client.get(reverse("core:catalogue_report"))
        self.assertEqual(response.context["total"], 0)
        self.assertContains(response, "No medicines have been added")

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.ask("Crocin").status_code, 401)

    def test_rejects_invalid_json_shapes_and_types(self):
        for payload in ([], None, 42, "hello", {"message": None}, {"message": ["Crocin"]}, {"message": " "}, {"message": "a" * 501}, {"message": "hi", "language": "fr"}):
            self.assertEqual(self.client.post(self.url, data=json.dumps(payload), content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post(self.url, data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post(self.url, data="x" * 8193, content_type="application/json").status_code, 413)

    def test_csrf_is_required_and_token_form_works(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(self.url, data=json.dumps({"message": "Crocin"}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        page = client.get(reverse("core:dashboard"))
        self.assertContains(page, "data-assistant")
        self.assertContains(page, "data-mic")
        response = client.post(self.url, data=json.dumps({"message": "Crocin"}), content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
