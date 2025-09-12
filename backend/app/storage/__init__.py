import os
from typing import Any, Dict, Optional
from .gcs import upload_file, build_blob_name, delete_file, get_file_info


class GCSStorage:
    """Google Cloud Storage implementation."""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
    
    def upload(self, text_id: str, original_name: str, file_path: str, 
               content_type: Optional[str] = None, make_public: bool = True) -> Dict[str, Any]:
        """Upload file with automatic naming."""
        blob_name = build_blob_name(text_id, original_name)
        return upload_file(
            bucket_name=self.bucket_name,
            blob_name=blob_name,
            file_path=file_path,
            content_type=content_type,
            make_public=make_public
        )
    
    def delete(self, blob_name: str) -> bool:
        """Delete file by blob name."""
        return delete_file(self.bucket_name, blob_name)
    
    def get_info(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """Get file information by blob name."""
        return get_file_info(self.bucket_name, blob_name)


def get_storage() -> GCSStorage:
    """
    Get storage implementation based on STORAGE_BACKEND environment variable.
    
    Currently only supports GCS. Future-proofed for other storage backends.
    """
    storage_backend = os.getenv("STORAGE_BACKEND", "gcs").lower()
    bucket_name = os.getenv("GCS_BUCKET", "doky_ai_audio_storage")
    
    if storage_backend == "gcs":
        return GCSStorage(bucket_name)
    else:
        raise ValueError(f"Unsupported storage backend: {storage_backend}")


# Convenience functions for direct usage
def upload_audio_file(text_id: str, original_name: str, file_path: str, 
                     content_type: str = "audio/mpeg") -> Dict[str, Any]:
    """Convenience function to upload audio files."""
    storage = get_storage()
    return storage.upload(text_id, original_name, file_path, content_type)


def upload_file_with_custom_name(blob_name: str, file_path: str, 
                                content_type: Optional[str] = None) -> Dict[str, Any]:
    """Upload file with custom blob name."""
    bucket_name = os.getenv("GCS_BUCKET", "doky_ai_audio_storage")
    return upload_file(bucket_name, blob_name, file_path, content_type)
