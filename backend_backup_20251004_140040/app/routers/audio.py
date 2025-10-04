from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from app.schemas import AudioResponse, AudioListResponse, AudioUpdate
from app.crud import (
    get_audios, get_audio_by_id, update_audio, delete_audio,
    get_audios_by_text_id, get_audio_count_by_text_id,
    audio_doc_to_response
)

router = APIRouter()


@router.get("/", response_model=List[AudioListResponse])
async def get_audio_files(
    text_id: Optional[str] = Query(None, description="Filter by text ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    order_by: str = Query("-uploaded_at", description="Field to order by")
):
    """
    Get list of audio files with optional filtering and pagination.
    
    - **text_id**: Filter by text ID (optional)
    - **limit**: Maximum number of results (1-100)
    - **skip**: Number of results to skip for pagination
    - **order_by**: Field to order by (default: -uploaded_at for newest first)
    """
    audio_docs = await get_audios(
        text_id=text_id,
        limit=limit,
        skip=skip,
        order_by=order_by
    )
    
    return [
        AudioListResponse(
            id=str(audio.id),
            text_id=audio.text_id,
            original_name=audio.original_name,
            storage_name=audio.storage_name,
            content_type=audio.content_type,
            size_bytes=audio.size_bytes,
            duration_sec=audio.duration_sec,
            uploaded_at=audio.uploaded_at.isoformat(),
            uploaded_by=audio.uploaded_by
        )
        for audio in audio_docs
    ]


@router.get("/{audio_id}", response_model=AudioResponse)
async def get_audio_file(audio_id: str = Path(..., description="Audio file ID")):
    """
    Get audio file by ID.
    
    - **audio_id**: The audio file ID
    """
    audio_doc = await get_audio_by_id(audio_id)
    if not audio_doc:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return AudioResponse(**audio_doc_to_response(audio_doc))


@router.put("/{audio_id}", response_model=AudioResponse)
async def update_audio_file(
    audio_id: str = Path(..., description="Audio file ID"),
    update_data: AudioUpdate = None
):
    """
    Update audio file metadata.
    
    - **audio_id**: The audio file ID
    - **update_data**: Fields to update
    """
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Convert Pydantic model to dict, excluding None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    updated_audio = await update_audio(audio_id, update_dict)
    if not updated_audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return AudioResponse(**audio_doc_to_response(updated_audio))


@router.delete("/{audio_id}")
async def delete_audio_file(audio_id: str = Path(..., description="Audio file ID")):
    """
    Delete audio file.
    
    - **audio_id**: The audio file ID
    """
    success = await delete_audio(audio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return {"message": "Audio file deleted successfully"}


@router.get("/text/{text_id}", response_model=List[AudioListResponse])
async def get_audio_files_by_text(
    text_id: str = Path(..., description="Text ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return")
):
    """
    Get all audio files for a specific text.
    
    - **text_id**: The text ID
    - **limit**: Maximum number of results (1-100)
    """
    audio_docs = await get_audios_by_text_id(text_id)
    
    # Apply limit
    if limit < len(audio_docs):
        audio_docs = audio_docs[:limit]
    
    return [
        AudioListResponse(
            id=str(audio.id),
            text_id=audio.text_id,
            original_name=audio.original_name,
            storage_name=audio.storage_name,
            content_type=audio.content_type,
            size_bytes=audio.size_bytes,
            duration_sec=audio.duration_sec,
            uploaded_at=audio.uploaded_at.isoformat(),
            uploaded_by=audio.uploaded_by
        )
        for audio in audio_docs
    ]


@router.get("/text/{text_id}/count")
async def get_audio_count_by_text(
    text_id: str = Path(..., description="Text ID")
):
    """
    Get count of audio files for a specific text.
    
    - **text_id**: The text ID
    """
    count = await get_audio_count_by_text_id(text_id)
    return {"text_id": text_id, "count": count}
