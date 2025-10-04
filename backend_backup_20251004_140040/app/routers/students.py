from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
from datetime import datetime, timezone
from app.models.student import (
    StudentDoc, 
    StudentCreate, 
    StudentUpdate, 
    StudentResponse, 
    StudentListResponse
)
from app.models.user import get_admin_user, UserDoc
import math

router = APIRouter()

@router.get("/", response_model=StudentListResponse)
async def get_students(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of students per page"),
    grade: Optional[int] = Query(None, ge=1, le=12, description="Filter by grade"),
    search: Optional[str] = Query(None, description="Search in first_name and last_name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[str] = Query(None, description="Filter by creation date (after)"),
    created_before: Optional[str] = Query(None, description="Filter by creation date (before)"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: UserDoc = Depends(get_admin_user)
):
    """
    Get list of students with pagination and filtering (Admin only)
    """
    try:
        print(f"🔍 get_students called with: page={page}, page_size={page_size}, grade={grade}, search='{search}', is_active={is_active}, created_after={created_after}, created_before={created_before}, sort_by={sort_by}, sort_order={sort_order}")
        
        # Build query
        query = {}
        if grade is not None:
            if grade == "other":
                # For "other" grade, we'll use grade 0 or any grade > 6
                query["$or"] = [
                    {"grade": 0},
                    {"grade": {"$gt": 6}}
                ]
            else:
                query["grade"] = grade
        if is_active is not None:
            query["is_active"] = is_active
        
        # Handle date range filtering
        if created_after or created_before:
            date_query = {}
            if created_after:
                from datetime import datetime
                try:
                    date_after = datetime.fromisoformat(created_after)
                    date_query["$gte"] = date_after
                except ValueError:
                    print(f"❌ Invalid created_after date format: {created_after}")
            if created_before:
                from datetime import datetime
                try:
                    date_before = datetime.fromisoformat(created_before)
                    date_query["$lte"] = date_before
                except ValueError:
                    print(f"❌ Invalid created_before date format: {created_before}")
            
            if date_query:
                query["created_at"] = date_query
        
        # Handle search functionality
        if search:
            print(f"🔍 Processing search: '{search}'")
            # Use MongoDB regex pattern for name search
            or_conditions = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]
            
            # Add registration number search if search is numeric
            if search.isdigit():
                or_conditions.append({"registration_number": int(search)})
            
            query["$or"] = or_conditions
            print(f"🔍 Final query with search: {query}")
        else:
            print(f"🔍 Final query without search: {query}")
        
        # Get total count
        print(f"🔍 Getting total count...")
        total = len(await StudentDoc.find(query).to_list())
        print(f"🔍 Total count: {total}")
        
        # Handle sorting
        sort_field = sort_by if sort_by in ["created_at", "first_name", "last_name", "grade", "is_active"] else "created_at"
        sort_direction = -1 if sort_order == "desc" else 1
        sort_criteria = [(sort_field, sort_direction)]
        
        # For name sorting, we need to sort by first_name + last_name
        if sort_field == "name":
            sort_criteria = [("first_name", sort_direction), ("last_name", sort_direction)]
        
        print(f"🔍 Sorting by: {sort_criteria}")
        
        # Get students with pagination and sorting
        skip = (page - 1) * page_size
        print(f"🔍 Getting students with skip={skip}, limit={page_size}")
        students = await StudentDoc.find(query).sort(sort_criteria).skip(skip).limit(page_size).to_list()
        print(f"🔍 Found {len(students)} students")
        
        # Convert to response format
        student_responses = [StudentResponse.from_doc(student) for student in students]
        
        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        return StudentListResponse(
            students=student_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        print(f"❌ Error in get_students: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching students: {str(e)}"
        )

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate, 
    current_user: UserDoc = Depends(get_admin_user)
):
    """
    Create a new student (Admin only)
    """
    try:
        # Generate registration number
        registration_number = await StudentDoc.generate_registration_number()
        print(f"🔢 Generated registration number: {registration_number}")
        
        # Create student data dict
        student_data_dict = {
            "first_name": student_data.first_name,
            "last_name": student_data.last_name,
            "grade": student_data.grade,
            "registration_number": registration_number,
            "created_by": current_user.username  # Kayıt eden kişi
        }
        
        # Create new student
        student = StudentDoc(**student_data_dict)
        
        await student.insert()
        print(f"✅ Student created successfully")
        
        return StudentResponse.from_doc(student)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in create_student: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating student: {str(e)}"
        )

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str, 
    current_user: UserDoc = Depends(get_admin_user)
):
    """
    Get a specific student by ID (Admin only)
    """
    try:
        from bson import ObjectId
        student = await StudentDoc.get(ObjectId(student_id))
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return StudentResponse.from_doc(student)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching student: {str(e)}"
        )

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str, 
    student_data: StudentUpdate, 
    current_user: UserDoc = Depends(get_admin_user)
):
    """
    Update a student (Admin only)
    """
    try:
        from bson import ObjectId
        print(f"🔄 Updating student {student_id} with data: {student_data.dict()}")
        
        student = await StudentDoc.get(ObjectId(student_id))
        
        if not student:
            print(f"❌ Student {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        print(f"📊 Found student: {student.first_name} {student.last_name}, is_active: {student.is_active}")
        
        # Update fields
        update_data = student_data.dict(exclude_unset=True)
        print(f"📝 Update data: {update_data}")
        
        for field, value in update_data.items():
            setattr(student, field, value)
            print(f"✅ Set {field} = {value}")
        
        student.updated_at = datetime.now(timezone.utc)
        await student.save()
        
        print(f"✅ Student updated successfully: {student.first_name} {student.last_name}, is_active: {student.is_active}")
        return StudentResponse.from_doc(student)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating student: {str(e)}"
        )

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str, 
    current_user: UserDoc = Depends(get_admin_user)
):
    """
    Soft delete a student (Admin only)
    """
    try:
        from bson import ObjectId
        student = await StudentDoc.get(ObjectId(student_id))
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Soft delete
        student.is_active = False
        student.updated_at = datetime.now(timezone.utc)
        await student.save()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting student: {str(e)}"
        )