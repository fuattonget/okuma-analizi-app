import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
from google.cloud import storage
from google.cloud.exceptions import NotFound
from loguru import logger


def get_client() -> storage.Client:
    """Get GCS client using service account JSON or default credentials."""
    try:
        from app.config import settings
        credentials_path = settings.gcs_credentials_path
        logger.info(f"GCS credentials path: {credentials_path}")
        
        if credentials_path and os.path.exists(credentials_path):
            logger.info(f"Using service account JSON: {credentials_path}")
            try:
                client = storage.Client.from_service_account_json(credentials_path)
                logger.info("GCS client created from service account JSON")
                return client
            except Exception as e:
                logger.error(f"Failed to create GCS client from service account JSON: {e}")
                raise
        else:
            # Use default credentials (e.g., from environment or metadata server)
            logger.info("Using default GCS credentials")
            try:
                client = storage.Client()
                logger.info("GCS client created with default credentials")
                return client
            except Exception as e:
                logger.error(f"Failed to create GCS client with default credentials: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Critical error in get_client: {e}")
        raise


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


def generate_signed_url(
    bucket_name: str,
    blob_name: str,
    expiration_hours: int = 1,
    method: str = "GET"
) -> str:
    """
    Generate a signed URL for private GCS bucket access.
    
    Args:
        bucket_name: GCS bucket name
        blob_name: Blob name within the bucket
        expiration_hours: URL expiration time in hours (default: 1 hour)
        method: HTTP method (default: "GET")
    
    Returns:
        str: Signed URL for accessing the private blob
    """
    try:
        logger.info(f"Generating signed URL for {bucket_name}/{blob_name}")
        
        # Get GCS client
        client = get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Check if blob exists
        if not blob.exists():
            logger.warning(f"Blob does not exist: {bucket_name}/{blob_name}")
            raise NotFound(f"Blob {blob_name} not found in bucket {bucket_name}")
        
        # Calculate expiration time
        expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        # Generate signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method=method
        )
        
        logger.info(f"Signed URL generated successfully, expires in {expiration_hours} hours")
        return signed_url
        
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {bucket_name}/{blob_name}: {e}")
        raise


def upload_file(
    bucket_name: str,
    blob_name: str,
    file_path: str,
    content_type: Optional[str] = None,
    make_public: bool = False
) -> Dict[str, str]:
    """
    Upload file to GCS bucket and return metadata.
    
    Args:
        bucket_name: GCS bucket name
        blob_name: Blob name within the bucket
        file_path: Local file path to upload
        content_type: MIME type of the file
        make_public: Whether to make the file public (default: False for private bucket)
    
    Returns:
        dict: {
            "bucket": bucket_name,
            "blob_name": blob_name,
            "gs_uri": "gs://bucket/path",
            "size_bytes": int,
            "md5": "hash"
        }
    """
    try:
        logger.info(f"Starting file upload: {file_path} -> {bucket_name}/{blob_name}")
        
        # Get GCS client
        try:
            client = get_client()
            logger.info("GCS client obtained successfully")
        except Exception as e:
            logger.error(f"Failed to get GCS client: {e}")
            raise
        
        # Get bucket and blob
        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            logger.info(f"Bucket and blob references created: {bucket_name}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to create bucket/blob references: {e}")
            raise
        
        # Get file size and MD5
        try:
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size} bytes")
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            raise
        
        # Calculate MD5 hash
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                md5_hash = hashlib.md5(file_content).hexdigest()
            logger.info(f"MD5 hash calculated: {md5_hash}")
        except Exception as e:
            logger.error(f"Failed to calculate MD5 hash: {e}")
            raise
        
        # Upload file
        try:
            with open(file_path, 'rb') as f:
                blob.upload_from_file(f, content_type=content_type)
            logger.info("File uploaded to GCS successfully")
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            raise
        
        # Build URLs (no public URL for private bucket)
        try:
            gs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"GS URI built: {gs_uri}")
        except Exception as e:
            logger.error(f"Failed to build GS URI: {e}")
            raise
        
        result = {
            "bucket": bucket_name,
            "blob_name": blob_name,
            "gs_uri": gs_uri,
            "size_bytes": file_size,
            "md5": md5_hash
        }
        
        logger.info("File upload completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Critical error in upload_file: {e}")
        raise


def delete_file(bucket_name: str, blob_name: str) -> bool:
    """Delete file from GCS bucket."""
    try:
        logger.info(f"Starting file deletion: {bucket_name}/{blob_name}")
        
        try:
            client = get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            logger.info(f"File deleted successfully: {bucket_name}/{blob_name}")
            return True
        except NotFound:
            logger.warning(f"File not found for deletion: {bucket_name}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {bucket_name}/{blob_name}: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Critical error in delete_file: {e}")
        raise


def get_file_info(bucket_name: str, blob_name: str) -> Optional[Dict[str, str]]:
    """Get file information from GCS bucket."""
    try:
        logger.info(f"Getting file info: {bucket_name}/{blob_name}")
        
        try:
            client = get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            logger.info("GCS client and blob references created")
        except Exception as e:
            logger.error(f"Failed to create GCS client/blob references: {e}")
            raise
        
        # Check if blob exists
        try:
            if not blob.exists():
                logger.warning(f"Blob does not exist: {bucket_name}/{blob_name}")
                return None
            logger.info("Blob exists, proceeding with metadata retrieval")
        except Exception as e:
            logger.error(f"Failed to check blob existence: {e}")
            raise
        
        # Get blob metadata
        try:
            blob.reload()
            logger.info("Blob metadata reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload blob metadata: {e}")
            raise
        
        try:
            result = {
                "bucket": bucket_name,
                "blob_name": blob_name,
                "gs_uri": f"gs://{bucket_name}/{blob_name}",
                "size_bytes": blob.size,
                "md5": blob.md5_hash,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None
            }
            logger.info("File info retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to build file info result: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Critical error in get_file_info: {e}")
        return None
