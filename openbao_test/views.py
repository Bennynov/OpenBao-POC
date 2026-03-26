from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
import json

SECRETS = {
    "secret_1": {
        "path": "editable/test",
        "key": "test",
        "label": "Test Secret"
    },
    "secret_2": {
        "path": "editable/test_2",
        "key": "test 2",
        "label": "test 2"
    },
    "secret_3": {
        "path": "locked/db_sk",
        "key": "db_sk",
        "label": "should not show secret"
    },
}

@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets from OpenBao."""
    
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
    
     # GET - Load all secrets WITH their current values
    secrets_with_values = []
    for secret_id, secret_config in SECRETS.items():
        # Load current value from OpenBao
        secret_data = openbao.get_secret(secret_config["path"])
        current_value = ""
        
        if secret_data:
            current_value = secret_data.get(secret_config["key"], "")
        
        # Add to list
        secrets_with_values.append({
            "id": secret_id,
            "label": secret_config["label"],
            "value": current_value,
        })
    
    context = {
        "csrf_token": get_token(request),
        "secrets": secrets_with_values
    }
    
    return render(request, "admin_panel/admin_panel.html", context)

def placeholder(request):
    return render(request, "admin_panel/admin_panel.html")

