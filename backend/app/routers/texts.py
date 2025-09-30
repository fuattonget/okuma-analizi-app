from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.models.documents import TextDoc, CanonicalTokens
from app.utils.text_tokenizer import tokenize_turkish_text, normalize_turkish_text
from app.utils.timezone import to_turkey_timezone
from typing import Union
from loguru import logger
import hashlib

router = APIRouter()


class TextCreate(BaseModel):
    title: str
    grade: int
    body: str
    comment: Optional[str] = None

class TextCopyCreate(BaseModel):
    title: str
    body: str
    grade: Optional[int] = 1
    comment: Optional[str] = "Dışardan kopyalanan metin"


class TextResponse(BaseModel):
    id: str
    text_id: str  # Keep for backward compatibility, will be same as id
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
    """Get all active texts, newest first (excluding temporary texts)"""
    texts = await TextDoc.find(TextDoc.active == True).sort("-created_at").to_list()
    logger.info(f"DEBUG: Found {len(texts)} active texts")
    
    # Filter out temporary texts (those with "Geçici Metin" in title)
    filtered_texts = [text for text in texts if not text.title.startswith("Geçici Metin")]
    logger.info(f"DEBUG: Found {len(filtered_texts)} non-temporary texts")
    
    result = []
    for text in filtered_texts:
        logger.info(f"DEBUG: Processing text: {text.title}, id type: {type(text.id)}, id value: {text.id}")
        text_response = TextResponse(
            id=str(text.id),
            text_id=str(text.id),  # Use _id as text_id for compatibility
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=to_turkey_timezone(text.created_at),
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
    # Generate slug for uniqueness check
    slug = f"{text_data.grade}-{text_data.title.lower().replace(' ', '-')}"
    
    # Check if text already exists by slug
    existing_text = await TextDoc.find_one(TextDoc.slug == slug)
    if existing_text:
        logger.info(f"Text already exists with slug: {slug}")
        return TextResponse(
            id=str(existing_text.id),
            text_id=str(existing_text.id),  # Use _id as text_id for compatibility
            title=existing_text.title,
            grade=existing_text.grade,
            body=existing_text.body,
            comment=existing_text.comment,
            created_at=to_turkey_timezone(existing_text.created_at),
            active=existing_text.active
        )
    
    # Debug: Log incoming text data
    logger.info(f"DEBUG: Received text data - title: {text_data.title}, body: {repr(text_data.body)}")
    
    # Normalize and tokenize the text
    normalized_body = normalize_turkish_text(text_data.body)
    tokenized_words = tokenize_turkish_text(normalized_body)
    
    # Debug: Log processing results
    logger.info(f"DEBUG: Normalized body: {repr(normalized_body)}")
    logger.info(f"DEBUG: Tokenized words: {tokenized_words}")
    
    text_doc = TextDoc(
        slug=slug,
        title=text_data.title,
        grade=text_data.grade,
        body=normalized_body,
        canonical=CanonicalTokens(
            tokens=tokenized_words
        ),
        comment=text_data.comment,
        active=True
    )
    await text_doc.insert()
    
    logger.info(f"Created new text with slug: {slug}")
    return TextResponse(
        id=str(text_doc.id),
        text_id=str(text_doc.id),  # Use _id as text_id for compatibility
        title=text_doc.title,
        grade=text_doc.grade,
        body=text_doc.body,
        comment=text_doc.comment,
        created_at=to_turkey_timezone(text_doc.created_at),
        active=text_doc.active
    )

@router.post("/copy", response_model=TextResponse)
async def copy_text(text_data: TextCopyCreate):
    """Copy external text for analysis"""
    try:
        # Generate slug for uniqueness check
        slug = f"{text_data.grade}-{text_data.title.lower().replace(' ', '-')}-copy"
        
        # Check if text already exists by slug
        existing_text = await TextDoc.find_one(TextDoc.slug == slug)
        if existing_text:
            logger.info(f"Text already exists with slug: {slug}")
            return TextResponse(
                id=str(existing_text.id),
                text_id=str(existing_text.id),  # Use _id as text_id for compatibility
                title=existing_text.title,
                grade=existing_text.grade,
                body=existing_text.body,
                comment=existing_text.comment,
                created_at=to_turkey_timezone(existing_text.created_at),
                active=existing_text.active
            )
        
        # Normalize and tokenize the text
        normalized_body = normalize_turkish_text(text_data.body)
        tokenized_words = tokenize_turkish_text(normalized_body)
        
        # Create text document
        text_doc = TextDoc(
            slug=slug,
            title=text_data.title,
            grade=text_data.grade,
            body=normalized_body,  # Use normalized body
            canonical=CanonicalTokens(
                tokens=tokenized_words
            ),
            comment=text_data.comment,
            active=True
        )
        await text_doc.insert()
        
        logger.info(f"Copied external text with slug: {slug}, title: {text_data.title}")
        return TextResponse(
            id=str(text_doc.id),
            text_id=str(text_doc.id),  # Use _id as text_id for compatibility
            title=text_doc.title,
            grade=text_doc.grade,
            body=text_doc.body,
            comment=text_doc.comment,
            created_at=to_turkey_timezone(text_doc.created_at),
            active=text_doc.active
        )
        
    except Exception as e:
        logger.error(f"Error copying text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to copy text: {str(e)}")


@router.get("/{text_id}")
async def get_text(text_id: str):
    """Get a specific text by text_id (which is now the same as _id)"""
    try:
        from bson import ObjectId
        text = await TextDoc.get(ObjectId(text_id))
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        return TextResponse(
            id=str(text.id),
            text_id=str(text.id),  # text_id is now same as id
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=to_turkey_timezone(text.created_at),
            active=text.active
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")


@router.put("/{text_id}", response_model=TextResponse)
async def update_text(text_id: str, text_data: TextUpdate):
    """Update a specific text by text_id (which is now the same as _id)"""
    try:
        from bson import ObjectId
        text = await TextDoc.get(ObjectId(text_id))
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Update fields
        text.title = text_data.title
        text.grade = text_data.grade
        text.comment = text_data.comment
        
        # Update body and canonical tokens if body changed
        if text.body != text_data.body:
            # Normalize and tokenize the new body
            normalized_body = normalize_turkish_text(text_data.body)
            tokenized_words = tokenize_turkish_text(normalized_body)
            
            text.body = normalized_body  # Store normalized body
            text.canonical = CanonicalTokens(
                tokens=tokenized_words
            )
        
        await text.save()
        
        return TextResponse(
            id=str(text.id),
            text_id=str(text.id),  # text_id is now same as id
            title=text.title,
            grade=text.grade,
            body=text.body,
            comment=text.comment,
            created_at=to_turkey_timezone(text.created_at),
            active=text.active
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")


@router.delete("/{text_id}")
async def delete_text(text_id: str):
    """Deactivate a specific text by text_id (soft delete)"""
    try:
        from bson import ObjectId
        text = await TextDoc.get(ObjectId(text_id))
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        text.active = False
        await text.save()
        return {"message": "Text deactivated successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid text ID")
