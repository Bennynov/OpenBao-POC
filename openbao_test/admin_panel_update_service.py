"""Request parsing and update workflow helpers for admin panel secret writes."""

import json


class SecretUpdateError(Exception):
    """Expected update failures mapped to HTTP responses by the view layer."""

    def __init__(self, message, status_code):
        """Store the message and the HTTP status code.

        Args:
            message: Human-readable error shown in the editor.
            status_code: HTTP status code the view should return.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_request_json(request):
    """Decode the request body as a JSON object.

    Args:
        request: The incoming request.

    Returns:
        The decoded payload dict.

    Raises:
        SecretUpdateError: (400) If the body is empty, not valid JSON, or
            not a JSON object.
    """
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
    """Return the request payload from either a JSON or a form body.

    Args:
        request: The incoming request.

    Returns:
        The payload as a dict.

    Raises:
        SecretUpdateError: (400) If a JSON body is invalid.
    """
    content_type = (request.content_type or "").split(";")[0].strip().lower()

    if content_type == "application/json":
        return _parse_request_json(request)

    if request.POST:
        return request.POST.dict()

    return _parse_request_json(request)


def parse_secret_update_request(request):
    """Parse and validate an update request into its three values.

    Accepts snake_case keys (section_id, secret_id, value or secret_value)
    and camelCase keys (sectionId, secretId, secretValue).

    Args:
        request: The incoming POST request.

    Returns:
        A tuple of (section_id, secret_id, value), all strings.

    Raises:
        SecretUpdateError: (400) If the body is invalid, an id is missing,
            or the value is missing or not a string.
    """
    payload = _parse_update_payload(request)

    section_id = str(payload.get("section_id") or payload.get("sectionId") or "").strip()
    secret_id = str(payload.get("secret_id") or payload.get("secretId") or "").strip()
    value = payload.get("value")

    # Checked with "is None" so an empty string is still a valid value.
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
    """Look up a secret's config in the nested secret index.

    Args:
        secret_index: Mapping of section_id -> secret_id -> secret config.
        section_id: The section to look in.
        secret_id: The secret within that section.

    Returns:
        The secret config dict, or None if either id is unknown.
    """
    section_secret_index = secret_index.get(section_id)
    if section_secret_index is None:
        return None

    return section_secret_index.get(secret_id)


def update_secret_value(openbao_client, secret_index, section_id, secret_id, new_value):
    """Write a new value for one secret, enforcing the editable path server-side.

    Only the value is taken from the client. The path and key come from the
    server-side config, so a client can't choose where to write.

    Args:
        openbao_client: Client with is_editable_path(path) and
            write_secret(path, data).
        secret_index: Mapping of section_id -> secret_id -> secret config.
        section_id: The section the secret belongs to.
        secret_id: The secret to update.
        new_value: The new secret value.

    Raises:
        SecretUpdateError: 404 if the section or secret is unknown, 403 if
            the path is not editable, 500 if the write fails.
    """
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
