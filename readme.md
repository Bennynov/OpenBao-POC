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
- `vault` = Mount point for KV v2 (example: `secret`)
- `OIDC_RP_CLIENT_ID` = OIDC client id
- `OIDC_RP_CLIENT_SECRET` = OIDC client secret
- `db_sk` = Django secret key
- `DEBUG` = `True` or `False`
- `ALLOWED_HOSTS` = Comma-separated list

## Run Locally
```bash
# 1) Create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install django python-dotenv hvac mozilla-django-oidc pyjwt

# 3) Export env vars (or use a .env file)
export OPENBAO_ADDR="https://your-openbao"
export OPENBAO_TOKEN="your-token"
export vault="secret"
export OIDC_RP_CLIENT_ID="your-client-id"
export OIDC_RP_CLIENT_SECRET="your-client-secret"
export db_sk="your-django-secret"
export DEBUG=True
export ALLOWED_HOSTS="localhost,127.0.0.1"

# 4) Start the server
python manage.py runserver
```

If `python` does not point to Python 3 on your system, use:

```bash
python3 manage.py runserver
```
## Endpoints
- `/` admin panel
- `/debug/token/` returns decoded ID token claims

## Tests
To run the test cases run

`python manage.py test`

## Project Structure
- `openbao_test/` admin panel app
- `test_app/` Django project settings and OpenBao client