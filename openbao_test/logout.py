from urllib.parse import urlencode
from django.conf import settings

def build_logout_url(request):
    base = getattr(settings, "OIDC_OP_END_SESSION_ENDPOINT", None)
    if not base:
        return "/"
    params = {}
    id_token = request.session.get("oidc_id_token")
    if id_token:
        params["id_token_hint"] = id_token
    params["post_logout_redirect_uri"] = request.build_absolute_uri("/")
    return base + ("?" + urlencode(params) if params else "")