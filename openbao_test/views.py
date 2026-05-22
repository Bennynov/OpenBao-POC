from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from test_app.openbao_client import openbao
from .admin_panel_sections import SECTION_CONFIG
from .admin_panel_service import SECRET_INDEX, build_sections_payload
from django.contrib.auth.decorators import login_required
from .admin_panel_update_service import (
    SecretUpdateError,
    parse_secret_update_request,
    update_secret_value,
)


def _error_response(message, status_code):
    return JsonResponse({"status": "error", "message": message}, status=status_code)


def _handle_secret_update(request):
    try:
        section_id, secret_id, new_value = parse_secret_update_request(request)
        update_secret_value(openbao, SECRET_INDEX, section_id, secret_id, new_value)
    except SecretUpdateError as exc:
        return _error_response(exc.message, exc.status_code)

    return JsonResponse({"status": "success", "message": "Secret updated"})

@login_required
@require_http_methods(["GET", "POST"])
def secret_updater(request):
    """Display and manage all secrets from OpenBao."""

    # POST handles save requests from the editor form.
    if request.method == "POST":
        return _handle_secret_update(request)

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

import jwt
import requests as _requests
from django.conf import settings as _settings

@login_required
def debug_token(request):
    id_token = request.session.get("oidc_id_token")
    access_token = request.session.get("oidc_access_token")

    out = {
        "configured_scopes": getattr(_settings, "OIDC_RP_SCOPES", None),
        "id_token_claims": None,
        "access_token_claims": None,
        "userinfo": None,
        "userinfo_error": None,
    }

    if id_token:
        out["id_token_claims"] = jwt.decode(id_token, options={"verify_signature": False})

    if access_token:
        try:
            out["access_token_claims"] = jwt.decode(access_token, options={"verify_signature": False})
        except Exception as e:
            out["access_token_claims"] = {"_decode_error": str(e), "_raw_prefix": access_token[:20]}

        try:
            resp = _requests.get(
                _settings.OIDC_OP_USER_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5,
            )
            try:
                out["userinfo"] = resp.json()
            except Exception:
                out["userinfo"] = {"_status": resp.status_code, "_body": resp.text}
        except Exception as e:
            out["userinfo_error"] = str(e)

    return JsonResponse(out, json_dumps_params={"indent": 2})