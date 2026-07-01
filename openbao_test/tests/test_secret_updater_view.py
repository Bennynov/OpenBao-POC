from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import ANY, patch

from openbao_test.admin_panel_update_service import SecretUpdateError


class SecretUpdaterViewTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="testuser", password="x")
        self.client.force_login(user)

    @patch("openbao_test.views.get_request_roles", return_value=set())
    @patch("openbao_test.views.build_sections_payload")
    def test_get_secret(self, mock_build_sections_payload, mock_get_roles):
        mock_build_sections_payload.return_value = [
            {
                "id": "section_1",
                "title": "Docs",
                "secrets": [],
                "secret_count": 0,
            }
        ]

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_panel/admin_panel.html")
        self.assertEqual(response.context["sections"], mock_build_sections_payload.return_value)
        self.assertEqual(
            response.context["admin_panel_data"]["sections"],
            mock_build_sections_payload.return_value,
        )

        for section in response.context["sections"]:
            self.assertEqual(section["secret_count"], len(section["secrets"]))

    @patch("openbao_test.views.roles_changed_or_failed", return_value=False)
    @patch("openbao_test.views.is_authorized", return_value=True)
    @patch("openbao_test.views.update_secret_value")
    @patch("openbao_test.views.parse_secret_update_request")
    def test_post_valid_update(self, mock_parse, mock_update, mock_authz, mock_introspect):
        post_data = {
            "section_id": "section_1",
            "secret_id": "secret_1",
            "value": "newvalue",
        }
        mock_parse.return_value = ("section_1", "secret_1", "newvalue")
        mock_update.return_value = None

        response = self.client.post("/", data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Secret updated"})
        mock_parse.assert_called_once()
        mock_update.assert_called_once_with(ANY, ANY, "section_1", "secret_1", "newvalue")

    @patch("openbao_test.views.update_secret_value")
    @patch("openbao_test.views.parse_secret_update_request")
    def test_post_invalid_update(self, mock_parse, mock_update):
        post_data = {
            "section_id": "",
            "secret_id": "",
            "value": "",
        }
        mock_parse.side_effect = SecretUpdateError("Missing section_id or secret_id", 400)

        response = self.client.post("/", data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"status": "error", "message": "Missing section_id or secret_id"})
        mock_parse.assert_called_once()
        mock_update.assert_not_called()
