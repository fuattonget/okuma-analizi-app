#!/usr/bin/env python3
"""
Script to create default score feedback configuration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.score_feedback import ScoreFeedbackDoc, ScoreRange, ErrorTypeComment
from app.utils.timezone import get_turkish_now
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_default_score_feedback():
    """Create default score feedback configuration"""
    
    # Connect to MongoDB
    mongo_url = os.getenv("MONGO_URI", settings.mongo_url or settings.mongo_uri)
    mongo_db = os.getenv("MONGO_DB", settings.mongo_db)
    logger.info(f"Connecting to MongoDB: {mongo_url}, database: {mongo_db}")
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[mongo_db]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[ScoreFeedbackDoc])
    
    # Create detailed comments first
    detailed_comments = []
    
    # Doğru Okunan Kelime Sayısı (0-50 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=50, max_score=50,
            comment="Okumada kelimelerin tamamı / tamamına yakını doğru telaffuz edilmiştir. Sınıf düzeyine göre istenilen seviyede okunmuştur. Öğrencinin doğru okuma oranı iyidir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=40, max_score=49,
            comment="Okumada kelimelerin neredeyse tamamı doğru telaffuz edilmiştir. Ufak tefek hatalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre beklenen düzeydedir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=30, max_score=39,
            comment="Okumada kelimelerin telaffuzunda hatalar vardır. Yanlış okumalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre ortalamanın biraz altındadır.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=20, max_score=29,
            comment="Okumada kelimelerin telaffuzunda hatalar sınıf düzeyine göre fazladır. Öğrencinin okumasındaki hata oranı yaşına ve sınıf düzeyine uygun oranda değildir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=10, max_score=19,
            comment="Okumada kelimelerin telaffuzunda hata oranı yüksektir. Sınıf düzeyinin epey aşağısında bir okuma sergilenmiştir. Hata oranı çok fazladır.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=0, max_score=9,
            comment="Okumada kelimelerin telaffuzları çok hatalıdır. Öğrenci sınıf düzeyine göre yetersiz ve kabul edilemeyecek bir okuma sergilemiştir.",
            max_possible_score=50
        )
    ])
    
    # Harf Eksiltme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=5, max_score=5,
            comment="Okumada harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenilen şekilde harf eksiltme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=4, max_score=4,
            comment="Okumada birkaç yer hariç harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenildiği gibi fazlaca harf eksiltme yapmamıştır. Bir iki yerde harf eksiltme yapmıştır. Bu da normal olarak kabul edilebilir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=3, max_score=3,
            comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen orandan daha fazla harf eksiltme yapmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=2, max_score=2,
            comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Harf eksiltme hataları fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=1, max_score=1,
            comment="Okumada harf eksiltme hataları fazladır. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Bu hatalar yaşına ve sınıf düzeyine göre ortalamanın altındadır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=0, max_score=0,
            comment="Okumada harf eksiltme hataları çok fazladır. Öğrencinin yaşından ve sınıf düzeyinden beklenilen oranın epey altında kalmıştır. Okumasında birçok yerde harf eksiltme görülmüştür.",
            max_possible_score=5
        )
    ])

    # Check if default config already exists
    existing_config = await ScoreFeedbackDoc.find_one({"name": "Varsayılan Puan Dönütü"})
    if existing_config:
        logger.info("Default score feedback configuration already exists, updating with detailed comments...")
        # Update existing config with detailed comments
        existing_config.detailed_comments = detailed_comments
        existing_config.updated_at = get_turkish_now()
        await existing_config.save()
        logger.info("✅ Updated existing score feedback configuration with detailed comments")
        mongo_client.close()
        return
    
    # Create default score ranges
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
    
    # Create detailed comments
    detailed_comments = []
    
    # Doğru Okunan Kelime Sayısı (0-50 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=50, max_score=50,
            comment="Okumada kelimelerin tamamı / tamamına yakını doğru telaffuz edilmiştir. Sınıf düzeyine göre istenilen seviyede okunmuştur. Öğrencinin doğru okuma oranı iyidir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=40, max_score=49,
            comment="Okumada kelimelerin neredeyse tamamı doğru telaffuz edilmiştir. Ufak tefek hatalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre beklenen düzeydedir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=30, max_score=39,
            comment="Okumada kelimelerin telaffuzunda hatalar vardır. Yanlış okumalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre ortalamanın biraz altındadır.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=20, max_score=29,
            comment="Okumada kelimelerin telaffuzunda hatalar sınıf düzeyine göre fazladır. Öğrencinin okumasındaki hata oranı yaşına ve sınıf düzeyine uygun oranda değildir.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=10, max_score=19,
            comment="Okumada kelimelerin telaffuzunda hata oranı yüksektir. Sınıf düzeyinin epey aşağısında bir okuma sergilenmiştir. Hata oranı çok fazladır.",
            max_possible_score=50
        ),
        ErrorTypeComment(
            error_type="correct_words",
            error_type_display="Doğru Okunan Kelime Sayısı",
            min_score=0, max_score=9,
            comment="Okumada kelimelerin telaffuzları çok hatalıdır. Öğrenci sınıf düzeyine göre yetersiz ve kabul edilemeyecek bir okuma sergilemiştir.",
            max_possible_score=50
        )
    ])
    
    # Harf Eksiltme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=5, max_score=5,
            comment="Okumada harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenilen şekilde harf eksiltme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=4, max_score=4,
            comment="Okumada birkaç yer hariç harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenildiği gibi fazlaca harf eksiltme yapmamıştır. Bir iki yerde harf eksiltme yapmıştır. Bu da normal olarak kabul edilebilir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=3, max_score=3,
            comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen orandan daha fazla harf eksiltme yapmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=2, max_score=2,
            comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Harf eksiltme hataları fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=1, max_score=1,
            comment="Okumada harf eksiltme hataları fazladır. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Bu hatalar yaşına ve sınıf düzeyine göre ortalamanın altındadır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_eksiltme",
            error_type_display="Harf Eksiltme",
            min_score=0, max_score=0,
            comment="Okumada harf eksiltme hataları çok fazladır. Öğrencinin yaşından ve sınıf düzeyinden beklenilen oranın epey altında kalmıştır. Okumasında birçok yerde harf eksiltme görülmüştür.",
            max_possible_score=5
        )
    ])
    
    # Create score feedback document
    config = ScoreFeedbackDoc(
        name="Varsayılan Puan Dönütü",
        description="Sistem için varsayılan puan dönütü konfigürasyonu",
        score_ranges=score_ranges,
        detailed_comments=detailed_comments,
        is_active=True
    )
    
    # Insert into database
    await config.insert()
    logger.info("✅ Default score feedback configuration created successfully")
    
    # Close MongoDB connection
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(create_default_score_feedback())
