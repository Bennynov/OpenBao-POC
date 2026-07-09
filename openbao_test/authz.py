"""Authorization helpers: role extraction and simple checks.

This module normalizes role extraction from Zitadel token claims and
provides small helpers for authorization checks.
"""
from typing import Any, Dict, Iterable, Set
import jwt
from django.conf import settings

ROLE_CLAIM_KEYS = (
    f"urn:zitadel:iam:org:project:{settings.OIDC_PROJECT_ID}:roles",
    "urn:zitadel:iam:org:project:roles",
)

# --- Getting a user's roles -------------------------------------------------

def _roles_from_claim(claims: Dict[str, Any], claim_key: str) -> Set[str]:
    """Return a set of top-level role names from a claim object.

    The claim value is expected to be a mapping of role_name -> metadata.
    If the key is missing or not a mapping, returns empty set.
    """
    if not isinstance(claims, dict):
        return set()

    raw = claims.get(claim_key)
    if not isinstance(raw, dict):
        return set()

    return {str(k).lower() for k in raw.keys()}


def extract_roles_from_claims(claims: Dict[str, Any]) -> Set[str]:
    """Extract roles from known claim keys and return a normalized set.

    Lowercases role names for consistent comparisons.
    """
    roles: Set[str] = set()
    for key in ROLE_CLAIM_KEYS:
        roles.update(_roles_from_claim(claims, key))

    return roles

def get_request_roles(request) -> Set[str]:
    """Return the current user's roles, decoded from the session's access token.

    Reads the access token mozilla-django-oidc stores on login (no extra calls to
    the identity provider). Returns an empty set if there is no token or it can't
    be decoded.
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
    """Return True if roles intersect required_roles or user is super admin."""
    role_set = {r.lower() for r in roles}
    required_set = {r.lower() for r in required_roles}

    if not required_set:
        return False

    if "super_admin" in role_set:
        return True

    return bool(role_set & required_set)
