class FakeClient:
    def is_editable_path(self, path):
        return path == "editable/docs/test_1"

    def get_secret(self, path):
        return {"test 1": "current value"} if path == "editable/docs/test_1" else None
