from django.test import RequestFactory, SimpleTestCase

from openbao_test.authz import extract_roles_from_claims, get_request_roles, is_authorized

PRIMARY_KEY = "urn:zitadel:iam:org:project:374057818900136573:roles"
FALLBACK_KEY = "urn:zitadel:iam:org:project:roles"


class ExtractRolesTests(SimpleTestCase):
    def test_extracts_from_primary_claim_key(self):
        claims = {PRIMARY_KEY: {"docs_admin": {}, "viewer": {}}}
        self.assertEqual(extract_roles_from_claims(claims), {"docs_admin", "viewer"})

    def test_extracts_from_fallback_claim_key(self):
        claims = {FALLBACK_KEY: {"editor": {}}}
        self.assertEqual(extract_roles_from_claims(claims), {"editor"})

    def test_merges_both_keys(self):
        claims = {
            PRIMARY_KEY: {"docs_admin": {}},
            FALLBACK_KEY: {"viewer": {}},
        }
        self.assertEqual(extract_roles_from_claims(claims), {"docs_admin", "viewer"})

    def test_empty_when_no_known_keys(self):
        claims = {"some_other_claim": {"role_a": {}}}
        self.assertEqual(extract_roles_from_claims(claims), set())

    def test_roles_are_lowercased(self):
        claims = {PRIMARY_KEY: {"Docs_Admin": {}, "VIEWER": {}}}
        self.assertEqual(extract_roles_from_claims(claims), {"docs_admin", "viewer"})


class IsAuthorizedTests(SimpleTestCase):
    def test_matching_role_returns_true(self):
        self.assertTrue(is_authorized({"docs_admin"}, {"docs_admin"}))

    def test_no_matching_role_returns_false(self):
        self.assertFalse(is_authorized({"viewer"}, {"docs_admin"}))

    def test_super_admin_bypasses_all_checks(self):
        self.assertTrue(is_authorized({"super_admin"}, {"docs_admin"}))

    def test_empty_required_roles_returns_false(self):
        self.assertFalse(is_authorized({"docs_admin"}, set()))


class GetRequestRolesTests(SimpleTestCase):
    def test_no_token_returns_empty_set(self):
        request = RequestFactory().get("/")
        request.session = {}
        self.assertEqual(get_request_roles(request), set())
