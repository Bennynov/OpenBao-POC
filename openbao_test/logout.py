import requests
from django.shortcuts import redirect
from django.contrib.auth import logout
from urllib.parse import urlencode
from django.conf import settings

def revoke_and_logout(request):
    access = request.session.get("oidc_access_token")
    refresh = request.session.get("oidc_refresh_token")
    rev = getattr(settings, "OIDC_OP_REVOCATION_ENDPOINT", None)
    auth = (settings.OIDC_RP_CLIENT_ID, settings.OIDC_RP_CLIENT_SECRET)
    if rev:
        for token, hint in ((access, "access_token"), (refresh, "refresh_token")):
            if token:
                requests.post(rev, data={"token": token, "token_type_hint": hint}, auth=auth)
    logout(request)
    return redirect("/") 

def build_op_logout_url(request):
    base = settings.OIDC_OP_END_SESSION_ENDPOINT
    params = {}
    id_token = request.session.get("oidc_id_token")
    if id_token:
        params["id_token_hint"] = id_token
    params["post_logout_redirect_uri"] = request.build_absolute_uri("/")  
    url = base + ("?" + urlencode(params) if params else "")
    return url

def full_logout(request):
    revoke_and_logout(request)                    
    return redirect(build_op_logout_url(request))