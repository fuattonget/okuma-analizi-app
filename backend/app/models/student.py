from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.utils.timezone import get_turkish_now
from pymongo import IndexModel, ASCENDING, DESCENDING
import asyncio

class StudentDoc(Document):
    """Student document model"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    grade: int = Field(..., ge=0, le=6)  # 0=Diğer, 1-6 sınıf aralığı
    registration_number: int = Field(..., ge=0)  # Kayıt numarası (0'dan başlar)
    created_by: str = Field(..., max_length=100)  # Kayıt eden kişi
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=get_turkish_now)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "students"
        indexes = [
            IndexModel([("first_name", ASCENDING)], name="students_first_name_asc"),
            IndexModel([("last_name", ASCENDING)], name="students_last_name_asc"),
            IndexModel([("grade", ASCENDING)], name="students_grade_asc"),
            IndexModel([("registration_number", ASCENDING)], name="students_registration_number_asc", unique=True),
            IndexModel([("is_active", ASCENDING)], name="students_active_asc"),
            IndexModel([("created_at", DESCENDING)], name="students_created_at_desc"),
        ]
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.full_name} (Sınıf {self.grade})"
    
    @classmethod
    async def generate_registration_number(cls) -> int:
        """Generate next registration number starting from 0"""
        # Find the highest existing registration number
        last_student = await cls.find().sort("-registration_number").limit(1).to_list()
        
        if last_student:
            # Return next number after the highest
            return last_student[0].registration_number + 1
        else:
            # No students exist, start from 0
            return 0
    
    @classmethod
    async def generate_student_number(cls) -> str:
        """Generate automatic student number"""
        # Get current year
        current_year = datetime.now().year
        
        # Find the highest student number for this year
        year_prefix = str(current_year)[-2:]  # Last 2 digits of year
        
        # Find students with auto-generated numbers for this year
        pattern = f"{year_prefix}%"
        existing_students = await cls.find(
            {"student_number": {"$regex": f"^{year_prefix}[0-9]{{4}}$"}}
        ).sort("-student_number").limit(1).to_list()
        
        if existing_students:
            # Get the last number and increment
            last_number = existing_students[0].student_number
            if last_number and last_number.startswith(year_prefix):
                try:
                    sequence = int(last_number[2:])  # Remove year prefix
                    next_sequence = sequence + 1
                except ValueError:
                    next_sequence = 1
            else:
                next_sequence = 1
        else:
            next_sequence = 1
        
        # Format: YYNNNN (e.g., 240001, 240002, etc.)
        return f"{year_prefix}{next_sequence:04d}"

# Request/Response models
class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    grade: int

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade: Optional[int] = None
    is_active: Optional[bool] = None

class StudentResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str
    grade: int
    registration_number: int
    created_by: str
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    @classmethod
    def from_doc(cls, doc: StudentDoc) -> "StudentResponse":
        """Create response from document"""
        return cls(
            id=str(doc.id),
            first_name=doc.first_name,
            last_name=doc.last_name,
            full_name=doc.full_name,
            grade=doc.grade,
            registration_number=doc.registration_number,
            created_by=doc.created_by,
            is_active=doc.is_active,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None
        )

class StudentListResponse(BaseModel):
    students: list[StudentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
