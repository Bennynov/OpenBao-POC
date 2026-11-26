"""Authorization helpers: role extraction and simple checks.

This module normalizes role extraction from Zitadel token claims and
provides small helpers for authorization checks.

Roles are always lowercased so comparisons are case-insensitive.
"""
from typing import Any, Dict, Iterable, Set
import jwt
from django.conf import settings

# Claim keys Zitadel may put roles under. The project-scoped key is checked
# first; the generic key is a fallback for tokens without a project id.
ROLE_CLAIM_KEYS = (
    f"urn:zitadel:iam:org:project:{settings.OIDC_PROJECT_ID}:roles",
    "urn:zitadel:iam:org:project:roles",
)

# --- Getting a user's roles -------------------------------------------------

def _roles_from_claim(claims: Dict[str, Any], claim_key: str) -> Set[str]:
    """Return the lowercased role names stored under one claim key.

    Args:
        claims: Decoded token claims or an introspection response.
        claim_key: The claim to read. Its value is expected to be a mapping
            of role_name -> metadata.

    Returns:
        A set of role names, or an empty set if the claims or the key's
        value are not mappings.
    """
    if not isinstance(claims, dict):
        return set()

    raw = claims.get(claim_key)
    if not isinstance(raw, dict):
        return set()

    return {str(k).lower() for k in raw.keys()}


def extract_roles_from_claims(claims: Dict[str, Any]) -> Set[str]:
    """Return all roles found under any of the ROLE_CLAIM_KEYS.

    Args:
        claims: Decoded token claims or an introspection response.

    Returns:
        The merged, lowercased set of role names. Empty if none are found.
    """
    roles: Set[str] = set()
    for key in ROLE_CLAIM_KEYS:
        roles.update(_roles_from_claim(claims, key))

    return roles

def get_request_roles(request) -> Set[str]:
    """Return the current user's roles, decoded from the session's access token.

    Reads the access token mozilla-django-oidc stores on login, so no call to
    the identity provider is made. The signature is not verified here because
    the token was already validated by mozilla-django-oidc at login.

    Args:
        request: The current Django request with a session.

    Returns:
        The user's lowercased roles, or an empty set if there is no token or
        it can't be decoded.
    """
    token = request.session.get("oidc_access_token")
    if not token:
        return set()

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return set()

    return extract_roles_from_claims(claims)

# --- Checking a user's roles -------------------------------------------------

def is_authorized(roles: Iterable[str], required_roles: Iterable[str]) -> bool:
    """Return True if the user has any required role or is super admin.

    Args:
        roles: Roles the user currently has.
        required_roles: Roles that grant access. Empty means nobody is
            allowed (fail closed).

    Returns:
        True if access is allowed, otherwise False.
    """
    role_set = {r.lower() for r in roles}
    required_set = {r.lower() for r in required_roles}

    if not required_set:
        return False

    if "super_admin" in role_set:
        return True

    return bool(role_set & required_set)
