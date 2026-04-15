from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
from .admin_panel_sections import SECTION_CONFIG
from .admin_panel_service import SECRET_INDEX, build_sections_payload
import json

@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets from OpenBao."""
    
    # POST handles save requests from the editor form.
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            section_id = str(data.get("section_id", ""))
            secret_id = str(data.get("secret_id", ""))
            new_value = data.get("value", "")
            
            # Validate the section and secret id pair exists on server.
            if section_id not in SECRET_INDEX:
                raise Exception("Invalid section")

            section_secret_index = SECRET_INDEX[section_id]
            if secret_id not in section_secret_index:
                raise Exception("Invalid secret")
            
            secret_config = section_secret_index[secret_id]
            path = secret_config["path"]
            key = secret_config["key"]
            
            # Update secret in OpenBao
            if openbao.write_secret(path, {key: new_value}):
                return JsonResponse({"status": "success", "message": "Secret updated"})
            else:
                return JsonResponse({"status": "error", "message": "Failed to write secret"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=403)
    
    sections = build_sections_payload(openbao, SECTION_CONFIG)
    
    # Context sent to Django template.
    context = {
        "csrf_token": get_token(request),
        "sections": sections,
        "admin_panel_data": {
            "sections": sections,
        },
    }
    
    return render(request, "admin_panel/admin_panel.html", context)

def placeholder(request):
    context = {
        "csrf_token": get_token(request),
        "sections": [],
        "admin_panel_data": {"sections": []},
    }
    return render(request, "admin_panel/admin_panel.html", context)

