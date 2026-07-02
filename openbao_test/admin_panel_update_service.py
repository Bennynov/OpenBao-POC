"""Request parsing and update workflow helpers for admin panel secret writes."""

import json


class SecretUpdateError(Exception):
    """Expected update failures mapped to HTTP responses by the view layer."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_request_json(request):
    if not request.body:
        raise SecretUpdateError("Request body is required.", 400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise SecretUpdateError("Malformed JSON payload.", 400) from exc

    if not isinstance(payload, dict):
        raise SecretUpdateError("JSON payload must be an object.", 400)

    return payload


def _parse_update_payload(request):
    content_type = (request.content_type or "").split(";")[0].strip().lower()

    if content_type == "application/json":
        return _parse_request_json(request)

    if request.POST:
        return request.POST.dict()

    return _parse_request_json(request)


def parse_secret_update_request(request):
    """Parse and validate update request payload into typed values."""
    payload = _parse_update_payload(request)

    section_id = str(payload.get("section_id") or payload.get("sectionId") or "").strip()
    secret_id = str(payload.get("secret_id") or payload.get("secretId") or "").strip()
    value = payload.get("value")

    if value is None:
        value = payload.get("secret_value")

    if value is None:
        value = payload.get("secretValue")

    if not section_id or not secret_id:
        raise SecretUpdateError("Secret selection is missing. Please reselect and try again.", 400)

    if value is None:
        raise SecretUpdateError("Missing required field: value", 400)

    if not isinstance(value, str):
        raise SecretUpdateError("Field 'value' must be a string.", 400)

    return section_id, secret_id, value


def _get_secret_config(secret_index, section_id, secret_id):
    section_secret_index = secret_index.get(section_id)
    if section_secret_index is None:
        return None

    return section_secret_index.get(secret_id)


def update_secret_value(openbao_client, secret_index, section_id, secret_id, new_value):
    """Apply a value-only secret update with server-side path enforcement."""
    secret_config = _get_secret_config(secret_index, section_id, secret_id)
    if secret_config is None:
        raise SecretUpdateError("Section or secret identifier not found.", 404)

    path = secret_config["path"]
    if not openbao_client.is_editable_path(path):
        raise SecretUpdateError("Configured secret path is not editable.", 403)

    try:
        write_succeeded = openbao_client.write_secret(path, {secret_config["key"]: new_value})
    except Exception as exc:
        raise SecretUpdateError("Failed to write secret.", 500) from exc

    if not write_succeeded:
        raise SecretUpdateError("Failed to write secret.", 500)
