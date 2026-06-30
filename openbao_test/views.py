from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
from .admin_panel_sections import SECTION_CONFIG
from .admin_panel_service import SECRET_INDEX, SECTION_ROLES, build_sections_payload
from .authz import get_request_roles, is_authorized
from django.contrib.auth.decorators import login_required
from .admin_panel_update_service import (
    SecretUpdateError,
    parse_secret_update_request,
    update_secret_value,
)


def _error_response(message, status_code):
    return JsonResponse({"status": "error", "message": message}, status=status_code)


def _handle_secret_update(request, user_roles):
    try:
        section_id, secret_id, new_value = parse_secret_update_request(request)

        if not is_authorized(user_roles, SECTION_ROLES.get(section_id, set())):
            raise SecretUpdateError("You do not have permission to update this section.", 403)

        update_secret_value(openbao, SECRET_INDEX, section_id, secret_id, new_value)
    except SecretUpdateError as exc:
        return _error_response(exc.message, exc.status_code)

    return JsonResponse({"status": "success", "message": "Secret updated"})

@login_required
@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets from OpenBao."""
    user_roles = get_request_roles(request)

    # POST handles save requests from the editor form.
    if request.method == "POST":
        return _handle_secret_update(request, user_roles)

    sections = build_sections_payload(openbao, SECTION_CONFIG, user_roles)

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