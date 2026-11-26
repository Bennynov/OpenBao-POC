# OpenBao POC

A Django proof-of-concept for browsing and updating OpenBao secrets through a simple admin panel with OIDC login.

## What It Does
- Renders a secrets admin UI grouped by service sections
- Reads current values from OpenBao (KV v2)
- Allows updates for secrets under editable paths only
- Uses OIDC for authentication before access

## How It Works
- Section definitions live in a static config and drive the UI
- The admin panel pulls values from OpenBao and renders a single page
- Updates are posted back to the same endpoint with section + secret ids

## Prerequisites
- Python 3.x
- OpenBao (KV v2)
- OIDC provider credentials
- OIDC login is required for normal use

## Configuration (Environment Variables)
Required:
- `OPENBAO_ADDR` = OpenBao server URL
- `OPENBAO_TOKEN` = Token with read/write access
- `VAULT` = Mount point for KV v2 (example: `secret`)
- `OIDC_RP_CLIENT_ID` = OIDC client id
- `OIDC_RP_CLIENT_SECRET` = OIDC client secret
- `OIDC_OP_BASE_URL` = Base URL of your OIDC provider
- `OIDC_PROJECT_ID` = OIDC provider project/org id used in role claim scopes
- `DB_SK` = Django secret key
- `DEBUG` = `True` or `False`
- `ALLOWED_HOSTS` = Comma-separated list

Optional:
- `OIDC_REDIRECT_REQUIRE_HTTPS` = `True` or `False` (defaults to `True`; set to `False` when running locally over plain HTTP)

All variables are listed in `.env.example`.

## Run Locally
```bash
# 1) Create and activate a virtualenv
python -m venv venv
source venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Export env vars (or copy .env.example to .env and fill it in)
export OPENBAO_ADDR="https://your-openbao"
export OPENBAO_TOKEN="your-token"
export VAULT="secret"
export OIDC_RP_CLIENT_ID="your-client-id"
export OIDC_RP_CLIENT_SECRET="your-client-secret"
export OIDC_OP_BASE_URL="https://your-idp"
export OIDC_PROJECT_ID="your-project-id"
export DB_SK="your-django-secret"
export DEBUG=True
export ALLOWED_HOSTS="localhost,127.0.0.1"
export OIDC_REDIRECT_REQUIRE_HTTPS=False  # optional, for local HTTP only

# 4) Start the server
python manage.py runserver
```

If `python` does not point to Python 3 on your system, use:

```bash
python3 manage.py runserver
```
## Endpoints
- `/` admin panel (login required; GET renders the panel, POST saves a secret)
- `/introspect/` POST only, login required; checks with the OIDC provider whether the user's roles are unchanged and returns `{"status": "ok"}` or `{"status": "logout"}`
- `/legacy` placeholder page with no sections
- `/oidc/` login, callback and logout routes from mozilla-django-oidc
- `/admin/` Django admin

## Tests
To run the test cases run

`python manage.py test`

## Project Structure
- `openbao_test/` admin panel app
- `test_app/` Django project settings and OpenBao client