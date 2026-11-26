"""Shared test doubles for the admin panel tests."""


class FakeClient:
    """Stand-in for OpenBaoClient.

    Only "editable/docs/test_1" counts as editable, and it holds
    {"test 1": "current value"}. Subclass it in a test to simulate
    failures (for example a write_secret that returns False).
    """

    def is_editable_path(self, path):
        """Return True only for the one known editable path."""
        return path == "editable/docs/test_1"

    def get_secret(self, path):
        """Return the fixed secret for the known path, otherwise None."""
        return {"test 1": "current value"} if path == "editable/docs/test_1" else None
