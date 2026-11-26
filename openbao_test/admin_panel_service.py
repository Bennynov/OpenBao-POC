"""Service helpers for admin panel section payload and secret lookup.

SECRET_INDEX and SECTION_ROLES are built once at import time, so an invalid
SECTION_CONFIG raises ValueError when the server starts.
"""

from .admin_panel_sections import SECTION_CONFIG
from .authz import is_authorized


def _validate_and_index_sections(section_config):
    """Validate the section config and index each section's secrets.

    Args:
        section_config: A list of section dicts in the SECTION_CONFIG format.

    Returns:
        A list of dicts, one per section, with keys "section" (the original
        dict), "section_id" (the stripped id) and "secret_index" (a mapping
        of secret_id -> {"path", "key", "label", "description"}).

    Raises:
        ValueError: If a section id is missing or duplicated, a section has
            no required_roles, or a secret id is missing, duplicated within
            its section, or has no description.
    """
    normalized_sections = []
    seen_section_ids = set()

    for section_position, section in enumerate(section_config):
        raw_section_id = section.get("id")
        section_id = "" if raw_section_id is None else str(raw_section_id).strip()
        if not section_id:
            raise ValueError(f"Missing required section id at index {section_position}.")

        if section_id in seen_section_ids:
            raise ValueError(f"Duplicate section id: '{section_id}'")

        if not section.get("required_roles"):
            raise ValueError(
                f"Missing required field 'required_roles' in section '{section_id}'. "
                "Every section must declare at least one role allowed to access it."
            )

        seen_section_ids.add(section_id)
        section_secret_index = {}
        seen_local_secret_ids = set()

        # Secret ids only need to be unique within their own section.
        for secret_position, secret in enumerate(section.get("secrets", [])):
            raw_secret_id = secret.get("id")
            local_secret_id = "" if raw_secret_id is None else str(raw_secret_id).strip()
            if not local_secret_id:
                raise ValueError(
                    f"Missing required secret id in section '{section_id}' at index {secret_position}."
                )

            if "description" not in secret:
                raise ValueError(
                    f"Missing required field 'description' in section '{section_id}' secret '{local_secret_id}'. "
                    "Add a description for every secret entry."
                )

            if local_secret_id in seen_local_secret_ids:
                raise ValueError(
                    f"Duplicate secret id in section '{section_id}': '{local_secret_id}'"
                )

            seen_local_secret_ids.add(local_secret_id)
            section_secret_index[local_secret_id] = {
                "path": secret["path"],
                "key": secret["key"],
                "label": secret["label"],
                "description": str(secret.get("description") or "").strip(),
            }

        normalized_sections.append(
            {
                "section": section,
                "section_id": section_id,
                "secret_index": section_secret_index,
            }
        )

    return normalized_sections


def build_secret_index(section_config):
    """Build the nested section/secret lookup used by save operations.

    Args:
        section_config: A list of section dicts in the SECTION_CONFIG format.

    Returns:
        A dict of section_id -> secret_id -> secret config.

    Raises:
        ValueError: If the config is invalid (see _validate_and_index_sections).
    """
    return {
        section_data["section_id"]: section_data["secret_index"]
        for section_data in _validate_and_index_sections(section_config)
    }


def build_section_roles_index(section_config):
    """Build the section_id -> required_roles lookup for authorization checks.

    Args:
        section_config: A list of section dicts in the SECTION_CONFIG format.

    Returns:
        A dict of section_id -> set of role names.

    Raises:
        ValueError: If the config is invalid (see _validate_and_index_sections).
    """
    return {
        section_data["section_id"]: section_data["section"]["required_roles"]
        for section_data in _validate_and_index_sections(section_config)
    }


def build_sections_payload(openbao_client, section_config, user_roles):
    """Build the UI payload from the section config plus current OpenBao values.

    Sections the user isn't authorized for are skipped before any secret
    values are fetched from OpenBao. Secrets outside editable paths are
    left out.

    Args:
        openbao_client: Client with is_editable_path(path) and get_secret(path).
        section_config: A list of section dicts in the SECTION_CONFIG format.
        user_roles: The current user's roles.

    Returns:
        A list of section dicts for the template and JS, each with display
        fields, a "secrets" list (id, label, description, value) and a
        "secret_count".

    Raises:
        ValueError: If the config is invalid (see _validate_and_index_sections).
    """
    sections_payload = []

    for section_data in _validate_and_index_sections(section_config):
        section = section_data["section"]

        if not is_authorized(user_roles, section["required_roles"]):
            continue

        section_payload = {
            "id": section_data["section_id"],
            "title": section["title"],
            "icon": section["icon"],
            "card_helper": section["card_helper"],
            "workspace_title": section["workspace_title"],
            "workspace_subtitle": section["workspace_subtitle"],
            "secrets": [],
        }

        for local_secret_id, secret_config in section_data["secret_index"].items():
            path = secret_config["path"]
            if not openbao_client.is_editable_path(path):
                continue

            # A missing or unreadable secret shows as an empty value.
            secret_data = openbao_client.get_secret(path)
            current_value = ""
            if isinstance(secret_data, dict):
                current_value = secret_data.get(secret_config["key"], "")

            section_payload["secrets"].append(
                {
                    "id": local_secret_id,
                    "label": secret_config["label"],
                    "description": secret_config.get("description", ""),
                    "value": current_value,
                }
            )

        section_payload["secret_count"] = len(section_payload["secrets"])
        sections_payload.append(section_payload)

    return sections_payload


# Built at import time so config errors surface on startup.
SECRET_INDEX = build_secret_index(SECTION_CONFIG)
SECTION_ROLES = build_section_roles_index(SECTION_CONFIG)
