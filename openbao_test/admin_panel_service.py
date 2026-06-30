"""Service helpers for admin panel section payload and secret lookup."""

from .admin_panel_sections import SECTION_CONFIG
from .authz import is_authorized


def _validate_and_index_sections(section_config):
    """Validate section config and return normalized iterable for service builders."""
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
    """Build nested section/secret lookup for save operations."""
    return {
        section_data["section_id"]: section_data["secret_index"]
        for section_data in _validate_and_index_sections(section_config)
    }


def build_section_roles_index(section_config):
    """Build section_id -> required_roles lookup for authorization checks."""
    return {
        section_data["section_id"]: section_data["section"]["required_roles"]
        for section_data in _validate_and_index_sections(section_config)
    }


def build_sections_payload(openbao_client, section_config, user_roles):
    """Build UI payload from section config plus current OpenBao values.

    Sections the user isn't authorized for are skipped before any secret
    values are fetched from OpenBao.
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


SECRET_INDEX = build_secret_index(SECTION_CONFIG)
SECTION_ROLES = build_section_roles_index(SECTION_CONFIG)
