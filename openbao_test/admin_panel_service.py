"""Service helpers for admin panel section payload and secret lookup."""

from .admin_panel_sections import SECTION_CONFIG


def _get_local_secret_id(secret, position):
    """Return configured section-local secret id or deterministic fallback."""
    return str(secret.get("id") or f"secret_{position + 1}")


def build_secret_index(section_config):
    """Build nested section/secret lookup for save operations."""
    secret_index = {}

    for section in section_config:
        section_id = str(section["id"])
        section_secret_index = {}
        seen_local_ids = set()

        for position, secret in enumerate(section.get("secrets", [])):
            local_secret_id = _get_local_secret_id(secret, position)
            if local_secret_id in seen_local_ids:
                raise ValueError(
                    f"Duplicate secret id in section '{section_id}': '{local_secret_id}'"
                )

            seen_local_ids.add(local_secret_id)
            section_secret_index[local_secret_id] = {
                "path": secret["path"],
                "key": secret["key"],
                "label": secret["label"],
            }

        secret_index[section_id] = section_secret_index

    return secret_index


def build_sections_payload(openbao_client, section_config):
    """Build UI payload from section config plus current OpenBao values."""
    sections_payload = []

    for section in section_config:
        section_id = str(section["id"])
        section_payload = {
            "id": section_id,
            "title": section["title"],
            "icon": section["icon"],
            "card_helper": section["card_helper"],
            "workspace_title": section["workspace_title"],
            "workspace_subtitle": section["workspace_subtitle"],
            "secrets": [],
        }

        seen_local_ids = set()

        for position, secret in enumerate(section.get("secrets", [])):
            local_secret_id = _get_local_secret_id(secret, position)
            if local_secret_id in seen_local_ids:
                raise ValueError(
                    f"Duplicate secret id in section '{section_id}': '{local_secret_id}'"
                )

            seen_local_ids.add(local_secret_id)

            path = secret["path"]
            if not openbao_client.is_editable_path(path):
                continue

            secret_data = openbao_client.get_secret(path)
            current_value = ""
            if isinstance(secret_data, dict):
                current_value = secret_data.get(secret["key"], "")

            section_payload["secrets"].append(
                {
                    "id": local_secret_id,
                    "label": secret["label"],
                    "value": current_value,
                }
            )

        section_payload["secret_count"] = len(section_payload["secrets"])
        sections_payload.append(section_payload)

    return sections_payload


SECRET_INDEX = build_secret_index(SECTION_CONFIG)
