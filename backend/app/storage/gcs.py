import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Optional
from google.cloud import storage
from google.cloud.exceptions import NotFound


def get_client() -> storage.Client:
    """Get GCS client using service account JSON or default credentials."""
    credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
    
    if credentials_path and os.path.exists(credentials_path):
        return storage.Client.from_service_account_json(credentials_path)
    else:
        # Use default credentials (e.g., from environment or metadata server)
        return storage.Client()


def slugify_filename(name: str) -> str:
    """Normalize Turkish characters and spaces in filename."""
    # Turkish character mappings
    turkish_chars = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'I': 'I',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }
    
    # Replace Turkish characters
    for tr_char, en_char in turkish_chars.items():
        name = name.replace(tr_char, en_char)
    
    # Replace spaces and special characters with underscores
    import re
    name = re.sub(r'[^\w\-_.]', '_', name)
    
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name


def build_blob_name(text_id: str, original_name: str) -> str:
    """Build blob name with date structure: YYYY/MM/DD/<text_or_custom>/<uuid>_<slug>.<ext>"""
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    
    # Extract file extension
    name, ext = os.path.splitext(original_name)
    if not ext:
        ext = ""
    
    # Create slug from original name
    slug = slugify_filename(name)
    
    # Generate UUID for uniqueness
    file_uuid = str(uuid.uuid4())
    
    # Determine if it's a text or custom upload
    folder = "texts" if text_id else "custom"
    
    # Build final blob name
    blob_name = f"{date_path}/{folder}/{file_uuid}_{slug}{ext}"
    
    return blob_name


def upload_file(
    bucket_name: str,
    blob_name: str,
    file_path: str,
    content_type: Optional[str] = None,
    make_public: bool = True
) -> Dict[str, str]:
    """
    Upload file to GCS bucket and return metadata.
    
    Returns:
        dict: {
            "bucket": bucket_name,
            "blob_name": blob_name,
            "gs_uri": "gs://bucket/path",
            "public_url": "https://storage.googleapis.com/...",
            "size_bytes": int,
            "md5": "hash"
        }
    """
    client = get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Get file size and MD5
    file_size = os.path.getsize(file_path)
    
    # Calculate MD5 hash
    with open(file_path, 'rb') as f:
        file_content = f.read()
        md5_hash = hashlib.md5(file_content).hexdigest()
    
    # Upload file
    with open(file_path, 'rb') as f:
        blob.upload_from_file(f, content_type=content_type)
    
    # Make public if requested
    if make_public:
        blob.make_public()
    
    # Build URLs
    gs_uri = f"gs://{bucket_name}/{blob_name}"
    public_url = blob.public_url
    
    return {
        "bucket": bucket_name,
        "blob_name": blob_name,
        "gs_uri": gs_uri,
        "public_url": public_url,
        "size_bytes": file_size,
        "md5": md5_hash
    }


def delete_file(bucket_name: str, blob_name: str) -> bool:
    """Delete file from GCS bucket."""
    try:
        client = get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except NotFound:
        return False


def get_file_info(bucket_name: str, blob_name: str) -> Optional[Dict[str, str]]:
    """Get file information from GCS bucket."""
    try:
        client = get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Check if blob exists
        if not blob.exists():
            return None
        
        # Get blob metadata
        blob.reload()
        
        return {
            "bucket": bucket_name,
            "blob_name": blob_name,
            "gs_uri": f"gs://{bucket_name}/{blob_name}",
            "public_url": blob.public_url,
            "size_bytes": blob.size,
            "md5": blob.md5_hash,
            "content_type": blob.content_type,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None
        }
    except Exception:
        return None
