"""
GCS Setup Utility
Creates GCS service account JSON file from environment variable
"""
import os
import json
import base64
from loguru import logger


def setup_gcs_credentials():
    """
    Create GCS service account JSON file from environment variable.
    This is used in production (Railway) to inject credentials.
    """
    gcs_json = os.getenv('GCS_SERVICE_ACCOUNT_JSON')
    gcs_path = os.getenv('GCS_CREDENTIALS_PATH', './gcs-service-account.json')
    
    if gcs_json:
        try:
            # Clean up the JSON string - remove extra quotes if present
            gcs_json = gcs_json.strip()
            
            # Check if it's Base64 encoded
            try:
                # Try to decode as Base64 first
                decoded_json = base64.b64decode(gcs_json).decode('utf-8')
                logger.info("🔓 GCS credentials detected as Base64 encoded")
                credentials = json.loads(decoded_json)
            except Exception:
                # If Base64 decode fails, try as regular JSON
                logger.info("📄 GCS credentials detected as plain JSON")
                credentials = json.loads(gcs_json)
            
            # Validate it's a service account JSON
            if 'type' not in credentials or credentials.get('type') != 'service_account':
                logger.warning("⚠️ GCS JSON might not be a valid service account file")
            
            # Fix private key newlines if present
            if 'private_key' in credentials and credentials['private_key']:
                # Replace literal \n with actual newlines
                credentials['private_key'] = credentials['private_key'].replace('\\n', '\n')
                logger.info("🔧 Fixed private key newlines")
            
            # Write to file
            with open(gcs_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            logger.info(f"✅ GCS credentials file created at {gcs_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid GCS_SERVICE_ACCOUNT_JSON format: {e}")
            logger.error(f"   First 100 chars: {gcs_json[:100] if gcs_json else 'empty'}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to create GCS credentials file: {e}")
            return False
    else:
        # Check if file already exists (local development)
        if os.path.exists(gcs_path):
            logger.info(f"✅ Using existing GCS credentials file at {gcs_path}")
            return True
        else:
            logger.warning("⚠️ No GCS credentials found (neither env var nor file)")
            return False

