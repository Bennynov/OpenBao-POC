"""Builds the IdP logout URL used by mozilla-django-oidc.

Wired up through the OIDC_OP_LOGOUT_URL_METHOD setting.
"""
from urllib.parse import urlencode
from django.conf import settings

def build_logout_url(request):
    """Return the IdP end-session URL so logout also ends the IdP session.

    Args:
        request: The current Django request with a session.

    Returns:
        The end-session endpoint with id_token_hint (if available) and
        post_logout_redirect_uri as query parameters, or "/" if no
        end-session endpoint is configured.
    """
    base = getattr(settings, "OIDC_OP_END_SESSION_ENDPOINT", None)
    if not base:
        return "/"
    params = {}
    id_token = request.session.get("oidc_id_token")
    if id_token:
        params["id_token_hint"] = id_token
    params["post_logout_redirect_uri"] = request.build_absolute_uri("/")
    return base + ("?" + urlencode(params) if params else "")