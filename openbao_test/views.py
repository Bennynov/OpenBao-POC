from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
import json

# Server-side secret registry.
# Each entry defines where the secret lives (path),
# which field key is updated (key), and how it is labeled in the UI (label).
SECRETS = {
    # IMPORTANT: top-level IDs must be unique, otherwise Python dicts overwrite earlier entries.
    "secret_1": {
        "path": "editable/test",
        "key": "test",
        "label": "Test Secret"
    },
    "secret_2": {
        "path": "editable/test_2",
        "key": "test 2",
        "label": "test secret 2"
    },
    "secret_3": {
        "path": "editable/message/test",
        "key": "test",
        "label": "test secret message"
    },
     "secret_4": {
        "path": "editable/docs/test_1",
        "key": "test 1",
        "label": "test secret message"
    },
     "secret_5": {
        "path": "editable/meet/test",
        "key": "test",
        "label": "test secret message"
    },
     "secret_6": {
        "path": "editable/drive/test",
        "key": "test 1",
        "label": "test secret message"
    },
}

# The fixed section ordering used by the UI cards.
SECTION_ORDER = ("docs", "drive", "meet", "message", "extra")


def get_section_for_path(path):
    """Map an editable vault path to exactly one UI section.

    Allowed path shapes:
    - editable/docs/<secret>
    - editable/drive/<secret>
    - editable/meet/<secret>
    - editable/message/<secret>
    - editable/<secret>  -> extra

    Any deeper or unexpected shape returns None and is not shown.
    """
    # Split path into clean non-empty pieces: "editable/docs/key" -> ["editable", "docs", "key"]
    parts = [part for part in path.split("/") if part]

    # Sectioned paths must be exactly 3 segments.
    if len(parts) == 3 and parts[0] == "editable":
        app_section = parts[1]
        if app_section in {"docs", "drive", "meet", "message"} and parts[2]:
            return app_section

    # Root editable secrets must be exactly 2 segments and belong to Extra.
    if len(parts) == 2 and parts[0] == "editable" and parts[1]:
        return "extra"

    # Everything else is intentionally excluded from the UI.
    return None

@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets from OpenBao."""
    
    # POST handles save requests from the editor form.
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            secret_id = data.get("id", "")
            new_value = data.get("value", "")
            
            # Validate secret_id exists on server
            if secret_id not in SECRETS:
                raise Exception("Invalid secret")
            
            secret_config = SECRETS[secret_id]
            path = secret_config["path"]
            key = secret_config["key"]
            
            # Update secret in OpenBao
            if openbao.write_secret(path, {key: new_value}):
                return JsonResponse({"status": "success", "message": "Secret updated"})
            else:
                return JsonResponse({"status": "error", "message": "Failed to write secret"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
    
    # GET builds data for initial page render.
    # Start with an empty list per section so the UI always has consistent keys.
    secrets_by_section = {section: [] for section in SECTION_ORDER}

    # Iterate all configured server-side secrets.
    for secret_id, secret_config in SECRETS.items():
        path = secret_config["path"]

        # Security/visibility guard: only editable paths are allowed in this UI.
        if not openbao.is_editable_path(path):
            continue

        # Strictly map path to one section; skip anything unexpected.
        section = get_section_for_path(path)
        if section is None:
            continue

        # Read current value from OpenBao so user can see current placeholder.
        secret_data = openbao.get_secret(path)
        current_value = ""
        if secret_data:
            current_value = secret_data.get(secret_config["key"], "")

        # Keep payload presentation-oriented and lightweight.
        # Do not expose internal vault paths to the UI payload.
        secrets_by_section[section].append({
            "id": secret_id,
            "label": secret_config["label"],
            "value": current_value,
        })
    
    # Context sent to Django template.
    context = {
        "csrf_token": get_token(request),
        "secrets_by_section": secrets_by_section,
    }
    
    return render(request, "admin_panel/admin_panel.html", context)

def placeholder(request):
    return render(request, "admin_panel/admin_panel.html")

