import os
import hvac
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OpenBaoClient:
    
    def __init__(self):
        """Initialize the OpenBao client with credentials from environment."""
        self.client = hvac.Client(
            url = os.getenv('OPENBAO_ADDR'),
            token = os.getenv('OPENBAO_TOKEN')
        )
        # Set the mount point for all secret operations
        self.mount_point = os.getenv('vault')
    
    def get_secret(self, path):
        try:
            # Read from KV v2 engine with custom mount point
            # hvac automatically adds '/data/' for KV v2
            secret = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            # KV v2 structure: response['data']['data'] contains the actual secrets
            return secret['data']['data']
        except Exception as e:
            print(f"Error retrieving secret from OpenBao at {self.mount_point}/{path}: {e}")
            return None
    
    def is_authenticated(self):
        """Check if OpenBao client is properly authenticated."""
        try:
            auth_check = self.client.is_authenticated()
            if auth_check:
                print(f"✓ Successfully authenticated to OpenBao at {os.getenv('OPENBAO_ADDR')}")
            return auth_check
        except Exception as e:
            print(f"✗ Authentication check failed: {e}")
            return False
    
    def write_secret(self, path, secret_data):
        """Write/update a secret in OpenBao."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                mount_point=self.mount_point
            )
            return True
        except Exception as e:
            print(f"Error writing secret to OpenBao at {self.mount_point}/{path}: {e}")
            return False

    def is_locked_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").lstrip("/")
        return normalized.startswith("locked/")

    def is_editable_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").lstrip("/")
        return normalized.startswith("editable/")


# Initialize the OpenBao client globally so Django can use it
openbao = OpenBaoClient()

def get_secret(secret_path, default=None):
    if not openbao.is_authenticated():
        raise Exception("CRITICAL: Cannot authenticate to OpenBao")
    
    secret = openbao.get_secret(secret_path)
    if secret and isinstance(secret, dict):
        return next(iter(secret.values()))
    
    raise Exception(f"CRITICAL: Secret not found at {secret_path}")