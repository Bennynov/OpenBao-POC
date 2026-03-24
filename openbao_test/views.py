from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
import json

# Configuration - change this to your secret path
SECRET_PATH = "locked/test_secret"
SECRET_KEY_NAME = "password"  # The key within the secret dict

@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Simple UI to view and update a secret from OpenBao."""
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_value = data.get("value", "")
            
            # Update secret in OpenBao
            if openbao.write_secret(SECRET_PATH, {SECRET_KEY_NAME: new_value}):
                return JsonResponse({"status": "success", "message": "Secret updated"})
            else:
                return JsonResponse({"status": "error", "message": "Failed to write secret"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    # GET - Display form
    secret_data = openbao.get_secret(SECRET_PATH)
    current_value = ""
    
    if secret_data:
        current_value = secret_data.get(SECRET_KEY_NAME, "")
    
    context = {
        "secret_name": SECRET_KEY_NAME,
        "secret_value": current_value,
        "secret_path": SECRET_PATH,
        "csrf_token": get_token(request),
    }
    
    return render(request, "admin_panel/admin_panel.html", context)

def placeholder(request):
    return render(request, "admin_panel/admin_panel.html")

SECRET_PATH = "editable/test"
SECRET_KEY_NAME = "test"