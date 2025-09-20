from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.documents import AudioFileDoc
from app.schemas import AudioCreate, AudioUpdate
from loguru import logger


async def insert_audio(payload: Dict[str, Any]) -> AudioFileDoc:
    """
    Insert a new audio file document.
    
    Args:
        payload: Dictionary containing audio file data including GCS metadata
        
    Returns:
        AudioFileDoc: The created audio file document
    """
    try:
        logger.info(f"Starting audio document insertion with payload keys: {list(payload.keys())}")
        
        try:
            # Convert text_id to ObjectId if it's a string
            if 'text_id' in payload and isinstance(payload['text_id'], str):
                logger.info(f"Converting text_id from string to ObjectId: {payload['text_id']}")
                payload['text_id'] = ObjectId(payload['text_id'])
                logger.info(f"text_id converted to ObjectId: {payload['text_id']}")
            
            # Create AudioFileDoc with all provided fields
            audio_doc = AudioFileDoc(**payload)
            logger.info(f"AudioFileDoc object created successfully")
        except Exception as e:
            logger.error(f"Failed to create AudioFileDoc object: {e}")
            logger.error(f"Payload: {payload}")
            raise
        
        try:
            await audio_doc.insert()
            logger.info(f"AudioFileDoc inserted successfully with ID: {audio_doc.id}")
            return audio_doc
        except Exception as e:
            logger.error(f"Failed to insert AudioFileDoc: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Critical error in insert_audio: {e}")
        raise


async def get_audio_by_id(audio_id: str) -> Optional[AudioFileDoc]:
    """
    Get audio file by ID.
    
    Args:
        audio_id: The audio file ID
        
    Returns:
        AudioFileDoc or None if not found
    """
    return await AudioFileDoc.get(audio_id)


async def get_audios(
    text_id: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    order_by: str = "-uploaded_at"
) -> List[AudioFileDoc]:
    """
    Get list of audio files with optional filtering and pagination.
    
    Args:
        text_id: Filter by text_id (optional)
        limit: Maximum number of results
        skip: Number of results to skip
        order_by: Field to order by (default: -uploaded_at for newest first)
        
    Returns:
        List of AudioFileDoc objects
    """
    query = {}
    if text_id:
        query["text_id"] = text_id
    
    return await AudioFileDoc.find(query).sort(order_by).skip(skip).limit(limit).to_list()


async def update_audio(audio_id: str, update_data: Dict[str, Any]) -> Optional[AudioFileDoc]:
    """
    Update audio file by ID.
    
    Args:
        audio_id: The audio file ID
        update_data: Dictionary containing fields to update
        
    Returns:
        Updated AudioFileDoc or None if not found
    """
    audio_doc = await AudioFileDoc.get(audio_id)
    if not audio_doc:
        return None
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(audio_doc, field):
            setattr(audio_doc, field, value)
    
    await audio_doc.save()
    return audio_doc


async def delete_audio(audio_id: str) -> bool:
    """
    Delete audio file by ID.
    
    Args:
        audio_id: The audio file ID
        
    Returns:
        True if deleted, False if not found
    """
    audio_doc = await AudioFileDoc.get(audio_id)
    if not audio_doc:
        return False
    
    await audio_doc.delete()
    return True


async def get_audios_by_text_id(text_id: str) -> List[AudioFileDoc]:
    """
    Get all audio files for a specific text.
    
    Args:
        text_id: The text ID
        
    Returns:
        List of AudioFileDoc objects for the text
    """
    return await AudioFileDoc.find({"text_id": text_id}).sort("-uploaded_at").to_list()


async def get_audio_count_by_text_id(text_id: str) -> int:
    """
    Get count of audio files for a specific text.
    
    Args:
        text_id: The text ID
        
    Returns:
        Number of audio files for the text
    """
    return await AudioFileDoc.find({"text_id": text_id}).count()


def audio_doc_to_response(audio_doc: AudioFileDoc) -> Dict[str, Any]:
    """
    Convert AudioFileDoc to response dictionary.
    
    Args:
        audio_doc: The AudioFileDoc object
        
    Returns:
        Dictionary with response fields
    """
    return {
        "id": str(audio_doc.id),
        "text_id": audio_doc.text_id,
        "original_name": audio_doc.original_name,
        "path": audio_doc.path,
        "storage_name": audio_doc.storage_name,
        "gcs_uri": audio_doc.gcs_uri,
        "content_type": audio_doc.content_type,
        "size_bytes": audio_doc.size_bytes,
        "md5_hash": audio_doc.md5_hash,
        "duration_ms": audio_doc.duration_ms,
        "duration_sec": audio_doc.duration_sec,
        "sr": audio_doc.sr,
        "uploaded_at": audio_doc.uploaded_at.isoformat(),
        "uploaded_by": audio_doc.uploaded_by,
        "created_at": audio_doc.created_at.isoformat() if hasattr(audio_doc, 'created_at') and audio_doc.created_at else None,
        "updated_at": audio_doc.updated_at.isoformat() if hasattr(audio_doc, 'updated_at') and audio_doc.updated_at else None
    }
