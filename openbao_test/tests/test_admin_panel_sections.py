from django.test import SimpleTestCase

from openbao_test.admin_panel_service import _validate_and_index_sections
from openbao_test.admin_panel_service import build_secret_index
from openbao_test.admin_panel_service import build_sections_payload

from .helpers import FakeClient


class SectionConfigValidationTests(SimpleTestCase):
    def test_missing_section_id_raises_value_error(self):
        bad_config = [
            {
                "title": "Docs",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [],
            }
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)

    def test_duplicate_section_ids(self):
        bad_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [],
            },
            {
                "title": "Docs_2",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [],
            },
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)

    def test_missing_secret_id(self):
        bad_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    }
                ],
            }
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)

    def test_missing_secret_description(self):
        bad_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                    }
                ],
            }
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)

    def test_duplicate_secret_id(self):
        bad_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    },
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    },
                ],
            },
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)

    def test_missing_required_roles_raises_value_error(self):
        bad_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "secrets": [],
            }
        ]

        with self.assertRaises(ValueError):
            _validate_and_index_sections(bad_config)


class BuildSecretIndexTests(SimpleTestCase):
    def test_build_secret_index_with_valid_config(self):
        valid_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    },
                ],
            },
        ]

        result = build_secret_index(valid_config)
        self.assertIsInstance(result, dict)
        self.assertIn("section_1", result)
        self.assertIn("secret_1", result["section_1"])

        secret_entry = result["section_1"]["secret_1"]
        self.assertEqual(secret_entry["path"], "editable/docs/test_1")
        self.assertEqual(secret_entry["key"], "test 1")
        self.assertEqual(secret_entry["label"], "test secret message test")
        self.assertEqual(
            secret_entry["description"],
            "Used by the docs service for API authentication.",
        )


class BuildSectionsPayloadFilterTests(SimpleTestCase):
    def test_build_sections_payload_filters_non_editable_paths(self):
        valid_config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "Editable secret",
                        "description": "Used by the docs service for API authentication.",
                    },
                    {
                        "id": "secret_2",
                        "path": "readonly/docs/test_2",
                        "key": "test 2",
                        "label": "Hidden secret",
                        "description": "This should be filtered out.",
                    },
                ],
            }
        ]

        result = build_sections_payload(FakeClient(), valid_config, {"docs_admin"})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "section_1")
        self.assertEqual(result[0]["secret_count"], 1)
        self.assertEqual(len(result[0]["secrets"]), 1)
        self.assertEqual(result[0]["secrets"][0]["id"], "secret_1")
        self.assertEqual(result[0]["secrets"][0]["value"], "current value")

    def test_build_sections_payload_filters_unauthorized_section(self):
        config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    }
                ],
            }
        ]

        result = build_sections_payload(FakeClient(), config, {"viewer"})

        self.assertEqual(len(result), 0)


class BuildSectionsPayloadGetSecretTests(SimpleTestCase):
    def test_get_secret_returns_none_shows_empty_value(self):
        class NullClient(FakeClient):
            def get_secret(self, path):
                return None

        config = [
            {
                "title": "Docs",
                "id": "section_1",
                "icon": "📄",
                "card_helper": "Document service credentials",
                "workspace_title": "Docs Secrets",
                "workspace_subtitle": "Manage document service secrets.",
                "required_roles": {"docs_admin"},
                "secrets": [
                    {
                        "id": "secret_1",
                        "path": "editable/docs/test_1",
                        "key": "test 1",
                        "label": "test secret message test",
                        "description": "Used by the docs service for API authentication.",
                    }
                ],
            }
        ]

        result = build_sections_payload(NullClient(), config, {"docs_admin"})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["secrets"][0]["value"], "")
