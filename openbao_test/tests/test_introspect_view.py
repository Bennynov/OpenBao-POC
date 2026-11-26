"""Tests for the introspect_check view."""

from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import patch


class IntrospectViewUnauthenticatedTests(TestCase):
    def test_unauthenticated_redirects(self):
        response = self.client.post("/introspect/")
        self.assertEqual(response.status_code, 302)


class IntrospectViewTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="testuser", password="x")
        self.client.force_login(user)

    @patch("openbao_test.views.roles_changed_or_failed", return_value=False)
    def test_roles_ok_returns_ok(self, mock_introspect):
        response = self.client.post("/introspect/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("openbao_test.views.roles_changed_or_failed", return_value=True)
    def test_roles_changed_returns_logout(self, mock_introspect):
        response = self.client.post("/introspect/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"status": "logout"})
