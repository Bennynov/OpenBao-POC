"""Live OIDC introspection: compares the IdP's current view of a user's roles
against the roles already on their session, used to catch role revocation
before the session token naturally expires.
"""
import requests
from django.conf import settings

from .authz import get_request_roles, extract_roles_from_claims


def roles_changed_or_failed(request) -> bool:
    """Return True if the IdP can't confirm the user's roles are unchanged.

    Sends the session's access token to the IdP introspection endpoint and
    compares the roles it reports with the roles in the session token. Any
    failure counts as "changed" so the caller fails closed.

    Args:
        request: The current Django request with a session.

    Returns:
        True if the caller should log the user out: no token, network or
        HTTP error, inactive token, or different roles. False only when the
        IdP confirms the same roles.
    """
    local_roles = get_request_roles(request)
    token = request.session.get("oidc_access_token")
    if not token:
        return True

    try:
        resp = requests.post(
            settings.OIDC_OP_INTROSPECTION_ENDPOINT,
            data={"token": token},
            timeout=5,
            auth=(settings.OIDC_RP_CLIENT_ID, settings.OIDC_RP_CLIENT_SECRET),
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return True

    if not data.get("active"):
        return True

    return extract_roles_from_claims(data) != local_roles
