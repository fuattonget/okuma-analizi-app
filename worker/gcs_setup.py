"""
GCS Setup Utility for Worker
Creates GCS service account JSON file from environment variable
"""
import os
import json
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
            # Parse JSON to validate
            credentials = json.loads(gcs_json)
            
            # Write to file
            with open(gcs_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            logger.info(f"✅ GCS credentials file created at {gcs_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid GCS_SERVICE_ACCOUNT_JSON: {e}")
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

