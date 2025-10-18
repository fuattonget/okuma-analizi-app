from beanie import Document
from pydantic import Field, BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class ScoreRange(BaseModel):
    """Score range definition"""
    min_score: int = Field(ge=0, le=100, description="Minimum score (inclusive)")
    max_score: int = Field(ge=0, le=100, description="Maximum score (inclusive)")
    color: str = Field(description="Background color for this range")
    feedback: str = Field(description="Feedback text for this score range")
    
    def contains_score(self, score: int) -> bool:
        """Check if a score falls within this range"""
        return self.min_score <= score <= self.max_score


class ErrorTypeComment(BaseModel):
    """Comment for a specific error type and score"""
    error_type: str = Field(..., description="Error type name (e.g., 'harf_eksiltme', 'harf_ekleme')")
    error_type_display: str = Field(..., description="Display name for error type (e.g., 'Harf Eksiltme')")
    min_score: int = Field(..., description="Minimum score for this comment (inclusive)")
    max_score: int = Field(..., description="Maximum score for this comment (inclusive)")
    comment: str = Field(..., description="Comment text for this error type and score range")
    max_possible_score: int = Field(..., description="Maximum possible score for this error type")

    def contains_score(self, score: int) -> bool:
        return self.min_score <= score <= self.max_score


class ScoreFeedbackDoc(Document):
    """Score feedback configuration document - All dates stored in UTC"""
    name: str = Field(description="Name of this feedback configuration")
    description: Optional[str] = Field(None, description="Description of this configuration")
    is_active: bool = Field(True, description="Whether this configuration is active")
    score_ranges: List[ScoreRange] = Field(description="List of score ranges and their feedback")
    detailed_comments: Optional[List[ErrorTypeComment]] = Field(None, description="Detailed comments for error types")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "score_feedback"
        indexes = [
            [("name", 1)],
            [("is_active", 1)],
        ]
    
    def get_feedback_for_score(self, score: int) -> Optional[ScoreRange]:
        """Get feedback for a given score"""
        for range_def in self.score_ranges:
            if range_def.contains_score(score):
                return range_def
        return None
    
    def get_comment_for_error_type(self, error_type: str, score: int) -> Optional[str]:
        """Get comment for a specific error type and score"""
        if not self.detailed_comments:
            return None
        
        for comment in self.detailed_comments:
            if comment.error_type == error_type and comment.contains_score(score):
                return comment.comment
        return None
    
    def get_all_error_type_comments(self, error_scores: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """Get all error type comments for given scores"""
        if not self.detailed_comments:
            return {}
        
        result = {}
        for error_type, score in error_scores.items():
            comment = self.get_comment_for_error_type(error_type, score)
            if comment:
                # Find the error type display name
                error_type_display = next(
                    (c.error_type_display for c in self.detailed_comments if c.error_type == error_type),
                    error_type.replace("_", " ").title()
                )
                result[error_type] = {
                    "score": score,
                    "comment": comment,
                    "error_type_display": error_type_display
                }
        return result
    
    def save_with_timestamp(self):
        """Save with updated timestamp"""
        self.updated_at = datetime.now(timezone.utc)
        return self.save()


class ScoreFeedbackResponse(BaseModel):
    """Response model for score feedback"""
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    score_ranges: List[ScoreRange]
    created_at: str
    updated_at: str
    
    @classmethod
    def from_doc(cls, doc: ScoreFeedbackDoc) -> "ScoreFeedbackResponse":
        return cls(
            id=str(doc.id),
            name=doc.name,
            description=doc.description,
            is_active=doc.is_active,
            score_ranges=doc.score_ranges,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat()
        )
