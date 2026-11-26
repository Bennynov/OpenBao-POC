"""Tests for request parsing and secret writes in admin_panel_update_service."""

import json

from django.test import RequestFactory
from django.test import SimpleTestCase
from unittest.mock import MagicMock

from openbao_test.admin_panel_update_service import SecretUpdateError
from openbao_test.admin_panel_update_service import parse_secret_update_request
from openbao_test.admin_panel_update_service import update_secret_value

from .helpers import FakeClient


class ParseSecretUpdateRequestTests(SimpleTestCase):
    def test_parse_update_missing_section_or_secret(self):
        req = RequestFactory().post("/", data={"value": "x"})
        with self.assertRaises(SecretUpdateError) as cm:
            parse_secret_update_request(req)
        self.assertEqual(cm.exception.status_code, 400)

    def test_parse_update_missing_value(self):
        req = RequestFactory().post("/", data={"section_id": "x", "secret_id": "y"})
        with self.assertRaises(SecretUpdateError) as cm:
            parse_secret_update_request(req)
        self.assertEqual(cm.exception.status_code, 400)

    def test_empty_body_returns_400(self):
        req = RequestFactory().post("/", content_type="application/json")
        with self.assertRaises(SecretUpdateError) as cm:
            parse_secret_update_request(req)
        self.assertEqual(cm.exception.status_code, 400)

    def test_invalid_json_body_returns_400(self):
        req = RequestFactory().post("/", data="not-json", content_type="application/json")
        with self.assertRaises(SecretUpdateError) as cm:
            parse_secret_update_request(req)
        self.assertEqual(cm.exception.status_code, 400)

    def test_camel_case_fields_are_accepted(self):
        req = RequestFactory().post(
            "/",
            data=json.dumps({"sectionId": "s1", "secretId": "sec1", "secretValue": "v"}),
            content_type="application/json",
        )
        section_id, secret_id, value = parse_secret_update_request(req)
        self.assertEqual(section_id, "s1")
        self.assertEqual(secret_id, "sec1")
        self.assertEqual(value, "v")

    def test_non_string_value_returns_400(self):
        req = RequestFactory().post(
            "/",
            data=json.dumps({"section_id": "s1", "secret_id": "sec1", "value": 123}),
            content_type="application/json",
        )
        with self.assertRaises(SecretUpdateError) as cm:
            parse_secret_update_request(req)
        self.assertEqual(cm.exception.status_code, 400)


class UpdateSecretValueTest(SimpleTestCase):
    def test_unknown_section_or_secret_returns_404(self):
        secret_index = {}
        with self.assertRaises(SecretUpdateError) as cm:
            update_secret_value(FakeClient(), secret_index, "missing_section", "missing_secret", "newval")
        self.assertEqual(cm.exception.status_code, 404)

    def test_non_editable_path_returns_403(self):
        secret_index = {
            "section_1": {
                "secret_1": {
                    "path": "readonly/docs/test_2",
                    "key": "test 1",
                }
            }
        }
        with self.assertRaises(SecretUpdateError) as cm:
            update_secret_value(FakeClient(), secret_index, "section_1", "secret_1", "newval")
        self.assertEqual(cm.exception.status_code, 403)

    def test_write_failure_returns_500(self):
        secret_index = {
            "section_1": {
                "secret_1": {"path": "editable/docs/test_1", "key": "test 1"}
            }
        }

        class BadWriter(FakeClient):
            def write_secret(self, path, payload):
                return False

        with self.assertRaises(SecretUpdateError) as cm:
            update_secret_value(BadWriter(), secret_index, "section_1", "secret_1", "v")
        self.assertEqual(cm.exception.status_code, 500)

    def test_write_exception_returns_500(self):
        secret_index = {
            "section_1": {
                "secret_1": {"path": "editable/docs/test_1", "key": "test 1"}
            }
        }

        class ExceptionWriter(FakeClient):
            def write_secret(self, path, payload):
                raise RuntimeError("boom")

        with self.assertRaises(SecretUpdateError) as cm:
            update_secret_value(ExceptionWriter(), secret_index, "section_1", "secret_1", "v")
        self.assertEqual(cm.exception.status_code, 500)

    def test_successful_write_calls_write_secret_with_correct_args(self):
        secret_index = {
            "section_1": {
                "secret_1": {"path": "editable/docs/test_1", "key": "test 1"}
            }
        }
        mock_client = MagicMock()
        mock_client.is_editable_path.return_value = True
        mock_client.write_secret.return_value = True

        update_secret_value(mock_client, secret_index, "section_1", "secret_1", "new_val")

        mock_client.write_secret.assert_called_once_with(
            "editable/docs/test_1", {"test 1": "new_val"}
        )
