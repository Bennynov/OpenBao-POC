from django.test import RequestFactory
from django.test import SimpleTestCase

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
