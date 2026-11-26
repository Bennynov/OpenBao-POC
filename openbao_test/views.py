"""HTTP views for the admin panel.

Views only handle HTTP concerns. Business logic lives in the service,
authz and introspection modules. JSON responses use the shape
{"status": "success" | "error" | "ok" | "logout", "message": ...}.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
from .admin_panel_sections import SECTION_CONFIG
from .admin_panel_service import SECRET_INDEX, SECTION_ROLES, build_sections_payload
from .authz import get_request_roles, is_authorized
from .introspection import roles_changed_or_failed
from django.contrib.auth.decorators import login_required
from .admin_panel_update_service import (
    SecretUpdateError,
    parse_secret_update_request,
    update_secret_value,
)


def _error_response(message, status_code):
    """Return a JSON error response in the standard shape.

    Args:
        message: Human-readable error shown in the editor.
        status_code: HTTP status code to send.

    Returns:
        A JsonResponse with {"status": "error", "message": message}.
    """
    return JsonResponse({"status": "error", "message": message}, status=status_code)


def _handle_secret_update(request, user_roles):
    """Handle a save request from the editor form.

    Order of checks: parse the request, check the section's roles locally,
    then confirm the roles with the IdP before writing to OpenBao.

    Args:
        request: The POST request from the editor.
        user_roles: The user's roles from the session token.

    Returns:
        A JsonResponse: success, error (400/403/404/500), or logout (401).
    """
    try:
        section_id, secret_id, new_value = parse_secret_update_request(request)

        if not is_authorized(user_roles, SECTION_ROLES.get(section_id, set())):
            raise SecretUpdateError("You do not have permission to update this section.", 403)

        if roles_changed_or_failed(request):
            return JsonResponse({"status": "logout"}, status=401)

        update_secret_value(openbao, SECRET_INDEX, section_id, secret_id, new_value)
    except SecretUpdateError as exc:
        return _error_response(exc.message, exc.status_code)

    return JsonResponse({"status": "success", "message": "Secret updated"})


@login_required
@require_http_methods(["POST"])
def introspect_check(request):
    """Tell the frontend whether the user's roles are still valid.

    Called by admin_panel.js before showing a secret's current value.

    Args:
        request: The POST request from the frontend.

    Returns:
        {"status": "ok"} (200) or {"status": "logout"} (401).
    """
    if roles_changed_or_failed(request):
        return JsonResponse({"status": "logout"}, status=401)
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets the user may access.

    GET renders the admin panel with only the sections the user's roles
    allow. POST saves a single secret value (see _handle_secret_update).

    Args:
        request: The current request.

    Returns:
        The rendered admin panel (GET) or a JsonResponse (POST).
    """
    user_roles = get_request_roles(request)

    # POST handles save requests from the editor form.
    if request.method == "POST":
        return _handle_secret_update(request, user_roles)

    sections = build_sections_payload(openbao, SECTION_CONFIG, user_roles)

    # Context sent to Django template. "sections" renders the cards;
    # "admin_panel_data" is passed to the JS through json_script.
    context = {
        "csrf_token": get_token(request),
        "sections": sections,
        "admin_panel_data": {
            "sections": sections,
        },
    }

    return render(request, "admin_panel/admin_panel.html", context)

@login_required
def placeholder(request):
    """Render the admin panel template with no sections.

    Args:
        request: The current request.

    Returns:
        The rendered admin panel showing the empty state.
    """
    context = {
        "csrf_token": get_token(request),
        "sections": [],
        "admin_panel_data": {"sections": []},
    }
    return render(request, "admin_panel/admin_panel.html", context)