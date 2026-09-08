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

    def test_chatbot_returns_a_contextual_prototype_reply(self):
        response = self.client.post(
            reverse("core:chat"),
            data=json.dumps({"message": "What is low stock?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Amoxicillin", response.json()["reply"])
