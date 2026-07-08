import requests

from django.test import RequestFactory, SimpleTestCase
from unittest.mock import MagicMock, patch

from openbao_test.introspection import roles_changed_or_failed

PRIMARY_KEY = "urn:zitadel:iam:org:project:374057818900136573:roles"


class RolesChangedOrFailedTests(SimpleTestCase):
    def test_no_token_returns_true(self):
        request = RequestFactory().get("/")
        request.session = {}
        self.assertTrue(roles_changed_or_failed(request))

    @patch("openbao_test.introspection.get_request_roles", return_value={"docs_admin"})
    @patch("openbao_test.introspection.requests.post")
    def test_active_matching_roles_returns_false(self, mock_post, mock_get_roles):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"active": True, PRIMARY_KEY: {"docs_admin": {}}}
        mock_post.return_value = mock_resp

        request = RequestFactory().get("/")
        request.session = {"oidc_access_token": "fake_token"}

        self.assertFalse(roles_changed_or_failed(request))

    @patch("openbao_test.introspection.requests.post")
    def test_inactive_token_returns_true(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"active": False}
        mock_post.return_value = mock_resp

        request = RequestFactory().get("/")
        request.session = {"oidc_access_token": "fake_token"}

        self.assertTrue(roles_changed_or_failed(request))

    @patch("openbao_test.introspection.get_request_roles", return_value={"docs_admin"})
    @patch("openbao_test.introspection.requests.post")
    def test_roles_changed_returns_true(self, mock_post, mock_get_roles):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"active": True, PRIMARY_KEY: {"different_role": {}}}
        mock_post.return_value = mock_resp

        request = RequestFactory().get("/")
        request.session = {"oidc_access_token": "fake_token"}

        self.assertTrue(roles_changed_or_failed(request))

    @patch("openbao_test.introspection.requests.post")
    def test_network_error_returns_true(self, mock_post):
        mock_post.side_effect = requests.RequestException()

        request = RequestFactory().get("/")
        request.session = {"oidc_access_token": "fake_token"}

        self.assertTrue(roles_changed_or_failed(request))

    @patch("openbao_test.introspection.requests.post")
    def test_http_error_returns_true(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError()
        mock_post.return_value = mock_resp

        request = RequestFactory().get("/")
        request.session = {"oidc_access_token": "fake_token"}

        self.assertTrue(roles_changed_or_failed(request))
