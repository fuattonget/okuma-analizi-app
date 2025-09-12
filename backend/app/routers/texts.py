from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.models.documents import TextDoc
from typing import Union
from loguru import logger
import hashlib

router = APIRouter()


class TextCreate(BaseModel):
    title: str
    grade: int
    body: str
    comment: Optional[str] = None


class TextResponse(BaseModel):
    id: str
    text_id: str
    title: str
    grade: int
    body: str
    comment: Optional[str] = None
    created_at: str
    active: bool

class TextUpdate(BaseModel):
    title: str
    grade: int
    body: str
    comment: Optional[str] = None


@router.get("/", response_model=List[TextResponse])
async def get_texts():
    """Get all active texts, newest first"""
    texts = await TextDoc.find(TextDoc.active == True).sort("-created_at").to_list()
    logger.info(f"DEBUG: Found {len(texts)} active texts")
    for i, text in enumerate(texts):
        logger.info(f"DEBUG: Text {i}: id={text.id}, text_id={text.text_id}, title={text.title}")
    
    result = []
    for text in texts:
        logger.info(f"DEBUG: Processing text: {text.title}, id type: {type(text.id)}, id value: {text.id}")
        text_response = TextResponse(
            id=text.id.__str__(),
            text_id=text.text_id,
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=text.created_at.isoformat(),
            active=text.active
        )
        result.append(text_response)
    logger.info(f"DEBUG: Returning {len(result)} text responses")
    return result


def generate_text_id(title: str, grade: int) -> str:
    """Generate a consistent text_id based on grade and title"""
    # Create a consistent string from grade and title
    base_string = f"{grade}_{title}"
    # Generate MD5 hash and take first 12 characters
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()[:12]

@router.post("/", response_model=TextResponse)
async def create_text(text_data: TextCreate):
    """Create a new text"""
    # Generate consistent text_id
    text_id = generate_text_id(text_data.title, text_data.grade)
    
    # Check if text already exists
    existing_text = await TextDoc.find_one(TextDoc.text_id == text_id)
    if existing_text:
        logger.info(f"Text already exists with text_id: {text_id}")
        return TextResponse(
            id=str(existing_text.id),
            text_id=existing_text.text_id,
            title=existing_text.title,
            grade=existing_text.grade,
            body=existing_text.body,
            comment=existing_text.comment,
            created_at=existing_text.created_at.isoformat(),
            active=existing_text.active
        )
    
    text_doc = TextDoc(
        text_id=text_id,
        title=text_data.title,
        grade=text_data.grade,
        body=text_data.body,
        comment=text_data.comment,
        active=True
    )
    await text_doc.insert()
    
    logger.info(f"Created new text with text_id: {text_id}")
    return TextResponse(
        id=str(text_doc.id),
        text_id=text_doc.text_id,
        title=text_doc.title,
        grade=text_doc.grade,
        body=text_doc.body,
        comment=text_doc.comment,
        created_at=text_doc.created_at.isoformat(),
        active=text_doc.active
    )


@router.get("/{text_id}")
async def get_text(text_id: str):
    """Get a specific text by text_id"""
    try:
        text = await TextDoc.find_one(TextDoc.text_id == text_id)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        return TextResponse(
            id=str(text.id),
            text_id=text.text_id,
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=text.created_at.isoformat(),
            active=text.active
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")


@router.put("/{text_id}", response_model=TextResponse)
async def update_text(text_id: str, text_data: TextUpdate):
    """Update a specific text by text_id"""
    try:
        text = await TextDoc.find_one(TextDoc.text_id == text_id)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Generate new text_id if title or grade changed
        new_text_id = generate_text_id(text_data.title, text_data.grade)
        
        text.text_id = new_text_id
        text.title = text_data.title
        text.grade = text_data.grade
        text.body = text_data.body
        text.comment = text_data.comment
        await text.save()
        
        return TextResponse(
            id=str(text.id),
            text_id=text.text_id,
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=text.created_at.isoformat(),
            active=text.active
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")


@router.delete("/{text_id}")
async def delete_text(text_id: str):
    """Deactivate a specific text by text_id (soft delete)"""
    try:
        text = await TextDoc.find_one(TextDoc.text_id == text_id)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        text.active = False
        await text.save()
        return {"message": "Text deactivated successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")
