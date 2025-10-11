from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from bson import ObjectId
from loguru import logger

from app.models.score_feedback import (
    ScoreFeedbackDoc, 
    ScoreFeedbackResponse, 
    ScoreRange
)
from app.models.user import UserDoc, get_current_user
from app.models.rbac import require_permission

router = APIRouter()


@router.get("/", response_model=List[ScoreFeedbackResponse])
@require_permission("score_feedback:read")
async def get_score_feedback_configs(
    active_only: bool = True,
    current_user: UserDoc = Depends(get_current_user)
):
    """Get all score feedback configurations"""
    try:
        query = {"is_active": True} if active_only else {}
        configs = await ScoreFeedbackDoc.find(query).sort("-created_at").to_list()
        return [ScoreFeedbackResponse.from_doc(config) for config in configs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching score feedback configs: {str(e)}"
        )


@router.get("/{config_id}", response_model=ScoreFeedbackResponse)
@require_permission("score_feedback:read")
async def get_score_feedback_config(
    config_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """Get a specific score feedback configuration"""
    try:
        config = await ScoreFeedbackDoc.get(ObjectId(config_id))
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Score feedback configuration not found"
            )
        return ScoreFeedbackResponse.from_doc(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching score feedback config: {str(e)}"
        )


@router.post("/", response_model=ScoreFeedbackResponse, status_code=status.HTTP_201_CREATED)
@require_permission("score_feedback:create")
async def create_score_feedback_config(
    name: str,
    description: Optional[str] = None,
    score_ranges: List[ScoreRange] = None,
    current_user: UserDoc = Depends(get_current_user)
):
    """Create a new score feedback configuration"""
    try:
        # Default score ranges based on the provided scale
        if not score_ranges:
            score_ranges = [
                ScoreRange(
                    min_score=100,
                    max_score=100,
                    color="#10B981",  # Green
                    feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli hızda ve doğrulukta okuma yapmaktadır. Bu okuma seviyesi Hızlı Okuma için güzel bir başlangıçtır. Öğrencinin eğitim hayatına kalıcı bir hız ve iyi bir yatırım yapmanın tam zamanı! Kurumumuzu arayarak Anlayarak Hızlı Okuma Eğitimi hakkında bilgi alabilir ve zaman kaybetmeden eğitime kaydolabilirsiniz. Unutmayın, ağaç yaşken eğilir."
                ),
                ScoreRange(
                    min_score=90,
                    max_score=99,
                    color="#3B82F6",  # Light Blue
                    feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli sayılabilecek hızda ve doğrulukta okuma yapmaktadır. Bu okuma seviyesi Hızlı Okuma için güzel bir başlangıç olabilir. Öğrencinin eğitim hayatına kalıcı bir hız ve iyi bir yatırım yapmanın için tam zamanı! Kurumumuzu arayarak Anlayarak Hızlı Okuma Eğitimi hakkında bilgi alabilir ve zaman kaybetmeden eğitimi kaydolabilirsiniz. Unutmayın, ağaç yaşken eğilir."
                ),
                ScoreRange(
                    min_score=50,
                    max_score=89,
                    color="#8B5CF6",  # Light Purple
                    feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli hıza ulaşmak için desteğe ihtiyaç duymaktadır. Bu konuda DOKY Eğitimi sizin için önerebileceğimiz iyi bir yatırımdır. Bu eğitimle birlikte öğrencimizin okuması istenilen düzeye çıkacak ve öğrencimiz Anlayarak Hızlı Okuma Eğitimi için hazır hale gelecektir. Sizleri daha detaylı bilgilendirebilmemiz ve sizlere destek olabilmemiz için bir telefon uzağınızdayız."
                ),
                ScoreRange(
                    min_score=0,
                    max_score=49,
                    color="#F59E0B",  # Orange
                    feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre okuma becerilerini geliştirmelidir. Bu konuda uzman eğitimci kadromuz, patentli eğitimimiz ve yıllarca süren tecrübemizle sizlere destek olmaya hazırız. İhtiyacınız olan eğitim DOKY Eğitimi'dir. Kurumumuzu arayarak bilgi alabilir, özel ders veya grup dersleri seçeneğinden sizlere uygun olan eğitimle devam edebilirsiniz. Bu süreçte hızlı olmanızı önermekteyiz. Unutmayın, vakit nakittir."
                )
            ]
        
        config = ScoreFeedbackDoc(
            name=name,
            description=description,
            score_ranges=score_ranges
        )
        
        await config.insert()
        return ScoreFeedbackResponse.from_doc(config)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating score feedback config: {str(e)}"
        )


@router.put("/{config_id}", response_model=ScoreFeedbackResponse)
@require_permission("score_feedback:update")
async def update_score_feedback_config(
    config_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    score_ranges: Optional[List[ScoreRange]] = None,
    is_active: Optional[bool] = None,
    current_user: UserDoc = Depends(get_current_user)
):
    """Update a score feedback configuration"""
    try:
        config = await ScoreFeedbackDoc.get(ObjectId(config_id))
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Score feedback configuration not found"
            )
        
        # Update fields
        if name is not None:
            config.name = name
        if description is not None:
            config.description = description
        if score_ranges is not None:
            config.score_ranges = score_ranges
        if is_active is not None:
            config.is_active = is_active
        
        await config.save_with_timestamp()
        return ScoreFeedbackResponse.from_doc(config)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating score feedback config: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("score_feedback:delete")
async def delete_score_feedback_config(
    config_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """Delete a score feedback configuration"""
    try:
        config = await ScoreFeedbackDoc.get(ObjectId(config_id))
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Score feedback configuration not found"
            )
        
        await config.delete()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting score feedback config: {str(e)}"
        )


@router.get("/score/{score}/feedback", response_model=dict)
@require_permission("score_feedback:read")
async def get_feedback_for_score(
    score: int,
    config_name: Optional[str] = None,
    current_user: UserDoc = Depends(get_current_user)
):
    """Get feedback for a specific score"""
    try:
        print(f"🔍 Getting feedback for score: {score}, config_name: {config_name}")
        
        # Find active configuration
        if config_name:
            config = await ScoreFeedbackDoc.find_one({"name": config_name, "is_active": True})
        else:
            config = await ScoreFeedbackDoc.find_one({"is_active": True})
        
        print(f"🔍 Found config: {config is not None}")
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active score feedback configuration found"
            )
        
        feedback_range = config.get_feedback_for_score(score)
        print(f"🔍 Feedback range: {feedback_range}")
        
        if not feedback_range:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No feedback found for score {score}"
            )
        
        result = {
            "score": score,
            "feedback": feedback_range.feedback,
            "color": feedback_range.color,
            "range": f"{feedback_range.min_score}-{feedback_range.max_score}",
            "config_name": config.name
        }
        
        print(f"🔍 Returning result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting feedback for score: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting feedback for score: {str(e)}"
        )

@router.get("/analysis/{analysis_id}/detailed-comments", response_model=dict)
@require_permission("score_feedback:read")
async def get_analysis_detailed_comments(
    analysis_id: str,
    config_name: Optional[str] = None,
    current_user: UserDoc = Depends(get_current_user)
):
    """Get detailed comments for a specific analysis based on error counts and scores"""
    try:
        from app.models.documents import AnalysisDoc, WordEventDoc, PauseEventDoc
        from app.services.scoring import recompute_counts
        from beanie import PydanticObjectId
        
        # Get analysis
        analysis = await AnalysisDoc.get(PydanticObjectId(analysis_id))
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Get active configuration
        if config_name:
            config = await ScoreFeedbackDoc.find_one({"name": config_name, "is_active": True})
        else:
            config = await ScoreFeedbackDoc.find_one({"is_active": True})
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active score feedback configuration found"
            )
        
        # Get word events for this analysis
        word_events = await WordEventDoc.find({"analysis_id": PydanticObjectId(analysis_id)}).to_list()
        
        # Calculate counts
        counts = recompute_counts(word_events)
        
        # Get pause events for long pauses
        pause_events = await PauseEventDoc.find({"analysis_id": PydanticObjectId(analysis_id)}).to_list()
        long_pauses = len([p for p in pause_events if p.class_ in ["long", "very_long"]])
        
        # Use grade_score breakdown if available, otherwise calculate scores
        error_scores = {}
        
        logger.info(f"🔍 Analysis summary: {analysis.summary}")
        logger.info(f"🔍 Grade score: {analysis.summary.get('grade_score') if analysis.summary else None}")
        
        # Helper function to normalize Turkish characters in keys
        def normalize_key(key: str) -> str:
            """Normalize Turkish characters in error type keys"""
            replacements = {
                'ğ': 'g',
                'ü': 'u',
                'ş': 's',
                'ı': 'i',
                'ö': 'o',
                'ç': 'c',
                'Ğ': 'G',
                'Ü': 'U',
                'Ş': 'S',
                'İ': 'I',
                'Ö': 'O',
                'Ç': 'C'
            }
            for tr_char, en_char in replacements.items():
                key = key.replace(tr_char, en_char)
            return key
        
        if analysis.summary and analysis.summary.get("grade_score") and analysis.summary["grade_score"].get("breakdown"):
            # Use existing grade_score breakdown
            logger.info("🔍 Using grade_score breakdown")
            breakdown = analysis.summary["grade_score"]["breakdown"]
            for error_type, data in breakdown.items():
                if isinstance(data, dict) and "score" in data:
                    # Normalize the error_type key to match database keys
                    normalized_key = normalize_key(error_type)
                    # Map doğru_kelime to correct_words
                    if normalized_key == "dogru_kelime":
                        normalized_key = "correct_words"
                    error_scores[normalized_key] = data["score"]
                    logger.info(f"🔍 Mapped {error_type} -> {normalized_key}: {data['score']}")
        else:
            logger.info("🔍 Using fallback calculation")
            # Fallback to manual calculation if grade_score breakdown is not available
            # Calculate correct words score (0-50 points)
            total_words = counts.get("total_words", 0)
            correct_words = counts.get("correct", 0)
            if total_words > 0:
                correct_percentage = (correct_words / total_words) * 100
                if correct_percentage >= 95:
                    error_scores["correct_words"] = 50
                elif correct_percentage >= 90:
                    error_scores["correct_words"] = 40
                elif correct_percentage >= 80:
                    error_scores["correct_words"] = 30
                elif correct_percentage >= 70:
                    error_scores["correct_words"] = 20
                elif correct_percentage >= 60:
                    error_scores["correct_words"] = 10
                else:
                    error_scores["correct_words"] = 0
            
            # Calculate error type scores (0-5 points each)
            error_types = {
                "harf_eksiltme": counts.get("missing", 0),
                "harf_ekleme": counts.get("extra", 0),
                "harf_degistirme": counts.get("substitution", 0),
                "kelime_eksiltme": counts.get("missing", 0),  # Same as harf_eksiltme for now
                "kelime_ekleme": counts.get("extra", 0),      # Same as harf_ekleme for now
                "kelime_degistirme": counts.get("substitution", 0),  # Same as harf_degistirme for now
                "uzun_duraksama": long_pauses,
                "tekrarlama": counts.get("repetition", 0)
            }
            
            # Calculate scores for each error type
            for error_type, count in error_types.items():
                if count == 0:
                    error_scores[error_type] = 5
                elif count <= 2:
                    error_scores[error_type] = 4
                elif count <= 5:
                    error_scores[error_type] = 3
                elif count <= 10:
                    error_scores[error_type] = 2
                elif count <= 15:
                    error_scores[error_type] = 1
                else:
                    error_scores[error_type] = 0
        
        # Get detailed comments for each error type
        error_comments = config.get_all_error_type_comments(error_scores)
        
        result = {
            "analysis_id": analysis_id,
            "config_name": config.name,
            "error_scores": error_scores,
            "error_comments": error_comments,
            "total_score": sum(error_scores.values()),
            "max_possible_score": 90  # 50 for correct words + 5*8 for error types
        }
        
        logger.info(f"Generated detailed comments for analysis {analysis_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating detailed comments for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating detailed comments: {str(e)}"
        )
