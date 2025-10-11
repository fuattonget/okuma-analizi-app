#!/usr/bin/env python3
"""
Script to create complete score feedback configuration with all error types.
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


async def create_complete_score_feedback():
    """Create complete score feedback configuration with all error types"""
    
    # Connect to MongoDB
    mongo_url = os.getenv("MONGO_URI", settings.mongo_url or settings.mongo_uri)
    mongo_db = os.getenv("MONGO_DB", settings.mongo_db)
    logger.info(f"Connecting to MongoDB: {mongo_url}, database: {mongo_db}")
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[mongo_db]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[ScoreFeedbackDoc])
    
    # Create detailed comments for all error types
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
    
    # Harf Ekleme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=5, max_score=5,
            comment="Öğrenci okuma yaparken harf ekleme yapmamıştır. Sınıf seviyesi ve yaşına göre uygun bir şekilde okumuştur.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=4, max_score=4,
            comment="Öğrenci okuma yaparken birkaç yerde harf ekleme yapmıştır. Sınıf seviyesi ve yaşına göre uygun bir şekilde okumuştur. Yaptığı birkaç harf ekleme normal sayılabilir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=3, max_score=3,
            comment="Öğrenci okuma yaparken ara ara harf ekleme yapmıştır. Oransal olarak sınıf seviyesine ve yaşına göre ortalamanın biraz altında kalmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=2, max_score=2,
            comment="Öğrenci okuma yaparken harf ekleme yapmaktadır. Sınıf düzeyi ve yaşından beklenmeyecek sayıda harf ekleme hataları mevcuttur.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=1, max_score=1,
            comment="Öğrenci okuma yaparken harf ekleme yapmaktadır. Sınıf düzeyi ve yaşına göre bu kadar çok harf ekleme yapması kabul edilebilir oranda değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_ekleme",
            error_type_display="Harf Ekleme",
            min_score=0, max_score=0,
            comment="Öğrencinin okumasında çokça harf ekleme görülmüştür. Bu sınıf seviyesine ve yaşına göre yüksek oranda harf ekleme hataları mevcuttur.",
            max_possible_score=5
        )
    ])
    
    # Harf Değiştirme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=5, max_score=5,
            comment="Okuma yaparken harf değiştirme hataları gözlemlenmiştir. Öğrenci yaşından ve sınıf düzeyinden beklendiği gibi harf değiştirme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=4, max_score=4,
            comment="Okuma yaparken harf değiştirme çok nadir de olsa gözlemlenmiştir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilecek kadar az harf değiştirme hatası gözlenlenmiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=3, max_score=3,
            comment="Okuma yaparken arada bir harf değiştirme yapabilmektedir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir orandan daha fazla harf ekleme hataları mevcuttur.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=2, max_score=2,
            comment="Okuma yaparken harf değiştirme hataları gözlenlenmiştir. Bu hatalar öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir seviyede değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=1, max_score=1,
            comment="Okuma yaparken fazlaca harf değiştirme yapıldığı gözlemlenmiştir. Öğrenci yaşına ve sınıf düzeyine göre fazlaca harf değiştirme hatası yapmaktadır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="harf_degistirme",
            error_type_display="Harf Değiştirme",
            min_score=0, max_score=0,
            comment="Okuma yaparken sık sık harf değiştirme yapmaktadır. Öğrencinin yaşı ve sınıf düzeyi göz önünde buundurulduğunda öğrenci okumasında ciddi oranda harf değiştirme yapmaktadır.",
            max_possible_score=5
        )
    ])
    
    # Hece Eksiltme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=5, max_score=5,
            comment="Öğrencinin okumasında hece eksiltme, yutma gibi hatalar görülmemiştir. Öğrenci yaşına ve sınıf düzeyine göre olması gerektiği gibi hece eksiltme yapmadan okuyabilmiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=4, max_score=4,
            comment="Öğrencinin okumasında birkaç yerde hece eksiltme, yutma gibi hatalar görülmüştür. Öğrencinin yaşına ve seviyesine göre yaptığı bu eksiltme veya yutma hataları kabul edilebilir seviyededir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=3, max_score=3,
            comment="Öğrenci okumasında ara sıra hece eksiltme, yutma gibi hatalar göstermiştir. Öğrencinin yaşına ve seviyesine göre bu hatalar kabul edilebilir hata payından biraz daha fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=2, max_score=2,
            comment="Öğrenci okumasında hece eksiltme, yutma gibi hatalar sergilemiştir. Hataların sayısı bulunduğu yaş ve sınıf düzeyine göre kabul edilebilir oranda değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=1, max_score=1,
            comment="Öğrenci okuma yaparken sık sık hece eksiltme ve yutma gibi hatalar yapmaktadır. Bulunduğu sınıf düzeyi ve yaşı göz önünde bulundurulduğunda hata sayısı fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_eksiltme",
            error_type_display="Hece Eksiltme",
            min_score=0, max_score=0,
            comment="Öğrenci okuma yaparken hece eksiltmekte veya yutmaktadır. Bu yaş seviyesi ve sınıf düzeyi için oldukça fazla hece eksiltme veya yutma hataları gözlemlenmiştir.",
            max_possible_score=5
        )
    ])
    
    # Hece Ekleme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=5, max_score=5,
            comment="Öğrencinin okumasında hece ekleme hataları görülmemiştir. Öğrenci yaşına ve sınıf düzeyine göre olması gerektiği gibi hece ekleme yapmadan okuyabilmiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=4, max_score=4,
            comment="Öğrencinin okumasında birkaç yerde hece ekleme hataları görülmüştür. Öğrencinin yaşına ve seviyesine göre yaptığı bu ekleme hataları kabul edilebilir seviyededir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=3, max_score=3,
            comment="Öğrenci okumasında ara sıra hece ekleme hataları yapmıştır. Öğrencinin yaşına ve seviyesine göre bu hatalar kabul edilebilir hata payından biraz daha fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=2, max_score=2,
            comment="Öğrenci okumasında hece ekleme yapmaktadır. Hataların sayısı bulunduğu yaş ve sınıf düzeyine göre kabul edilebilir oranda değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=1, max_score=1,
            comment="Öğrenci okuma yaparken sık sık hece hece ekleme yapmaktadır. Bulunduğu sınıf düzeyi ve yaşı göz önünde bulundurulduğunda hata sayısı fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="hece_ekleme",
            error_type_display="Hece Ekleme",
            min_score=0, max_score=0,
            comment="Öğrenci okuma yaparken hece eklemektedir. Bu yaş seviyesi ve sınıf düzeyi için oldukça fazla hece ekleme hataları gözlemlenmiştir.",
            max_possible_score=5
        )
    ])
    
    # Kelime Eksiltme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=5, max_score=5,
            comment="Okuma sırasında kelime eksiltme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve kelime eksiltme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=4, max_score=4,
            comment="Okuma sırasında nadiren kelime eksiltmiştir. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=3, max_score=3,
            comment="Okuma sırasında birkaç yerde kelime eksiltmeler görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime eksiltme yapmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=2, max_score=2,
            comment="Okuma sırasında kelime eksiltme hataları mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda kelime eksiltme yapma oranı kabul edilebilir seviyede değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=1, max_score=1,
            comment="Okuma sırasında kelime eksiltme sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_eksiltme",
            error_type_display="Kelime Eksiltme",
            min_score=0, max_score=0,
            comment="Okuma sırasında kelime eksiltmeler fazladır. Öğrenci yaşına göre ve sınıf düzeyine göre bu hataları epey fazla yapmıştır.",
            max_possible_score=5
        )
    ])
    
    # Kelime Ekleme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=5, max_score=5,
            comment="Okuma yaparken kelime ekleme hataları gözlemlenmiştir. Öğrenci yaşından ve sınıf düzeyinden beklendiği gibi kelime ekleme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=4, max_score=4,
            comment="Okuma yaparken kelime ekleme çok nadir de olsa gözlemlenmiştir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilecek kadar az kelime ekleme hatası gözlenlenmiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=3, max_score=3,
            comment="Okuma yaparken arada bir kelime ekleme yapabilmektedir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir orandan daha fazla kelime ekleme hataları mevcuttur.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=2, max_score=2,
            comment="Okuma yaparken kelime ekleme hataları gözlenlenmiştir. Bu hatalar öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir seviyede değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=1, max_score=1,
            comment="Okuma yaparken fazlaca kelime ekleme yapıldığı gözlemlenmiştir. Gözlemlenen bu hataların sayısı öğrencinin sınıf düzeyi ve yaşına göre uygun değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_ekleme",
            error_type_display="Kelime Ekleme",
            min_score=0, max_score=0,
            comment="Okuma yaparken sık sık kelime ekleme yapmaktadır. Öğrencinin yaşı ve sınıf düzeyi göz önünde bulundurulduğunda öğrenci okumasında çok fazla oranda kelime ekleme yapmaktadır.",
            max_possible_score=5
        )
    ])
    
    # Kelime Değiştirme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=5, max_score=5,
            comment="Okuma sırasında kelime değiştirme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve kelime değiştirme hataları yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=4, max_score=4,
            comment="Okuma sırasında nadiren kelime değiştirmiştir. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=3, max_score=3,
            comment="Okuma sırasında birkaç yerde kelime değiştirmeler görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime değiştirme yapmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=2, max_score=2,
            comment="Okuma sırasında kelime değiştirme hataları mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda kelime değiştirme oranı kabul edilebilir seviyede değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=1, max_score=1,
            comment="Okuma sırasında kelime değiştirme sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="kelime_degistirme",
            error_type_display="Kelime Değiştirme",
            min_score=0, max_score=0,
            comment="Okuma sırasında kelime değiştirmeler fazladır. Öğrencinin yaşı ve sınıf düzeyi düşünüldüğünde kelime değiştirme sayısı kabul edilemez orandadır.",
            max_possible_score=5
        )
    ])
    
    # Kelime Tanıma (Uzun Duraksama) (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=5, max_score=5,
            comment="Öğrencinin kelime tanıma hızı yüksektir. Bulunduğu sınıf düzeyi ve yaşına uygun bir hızda kelimeyi tanıyıp okuyabilmekte ve tek seferde kelimeyi okuyabilmektedir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=4, max_score=4,
            comment="Öğrencinin kelime tanıma hızı iyidir. Nadir de olsa zorlandığı kelimeler olmuştur fakat genel anlamda bulunduğu sınıf düzeyi ve yaşına uygun bir hızda kelimeyi tanıyıp okuyabilmektedir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=3, max_score=3,
            comment="Öğrencinin kelime tanıma hızı beklenilen düzeyde değildir. Arada bir tek seferde okuyamadığı kelimeler gözlenmiştir. Gözlemlenen hata sayısı öğrencinin sınıf düzeyi ve yaşında göre beklenenden daha fazladır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=2, max_score=2,
            comment="Öğrencinin kelime tanıma hızı seviyesine göre düşüktür. Kelimeyi tek seferde okumakta zorlandığı yerler sayıca fazladır. Uzun duraksamalar gözlemlenmiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=1, max_score=1,
            comment="Öğrenci kelimeleri yaşından ve sınıf düzeyinden beklenmedik şekilde tek seferde okumakta zorlanmıştır. Sık sık duraksamalara ihtiyaç duymuştur.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="uzun_duraksama",
            error_type_display="Kelime Tanıma (Uzun Duraksama)",
            min_score=0, max_score=0,
            comment="Öğrencinin kelime tanıma hızı çok düşüktür. Bulunduğu sınıf düzeyine ve yaşına uygun bir hızda kelimeleri okuyamamıştır. Sürekli duraksamaya ihtiyaç duymuştur.",
            max_possible_score=5
        )
    ])
    
    # Tekrarlama / Heceleme (0-5 points)
    detailed_comments.extend([
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=5, max_score=5,
            comment="Okuma esnasında tekrarlama veya heceleme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve tekrarlama ya da heceleme yapmamıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=4, max_score=4,
            comment="Okuma esnasında nadiren tekrarlama veya heceleme yapmıştır. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=3, max_score=3,
            comment="Okuma esnasında birkaç yerde tekrarlama veya heceleme görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime tekrarlama veya heceleme yapmıştır.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=2, max_score=2,
            comment="Okuma esnasında tekrarlamalar veya hecelemeler mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda tekrarlama veya hecelemeye başvurma oranı kabul edilebilir oranda değildir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=1, max_score=1,
            comment="Okuma esnasında tekrarlamalar veya hecelemeler sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir.",
            max_possible_score=5
        ),
        ErrorTypeComment(
            error_type="tekrarlama",
            error_type_display="Tekrarlama / Heceleme",
            min_score=0, max_score=0,
            comment="Okuma esnasında yapılan tekrarlamalar veya hecelemeler fazladır. Öğrenci yaşına göre ve sınıf düzeyine göre bu hataları epey fazla yapmıştır.",
            max_possible_score=5
        )
    ])

    # Create score ranges
    score_ranges = [
        ScoreRange(
            min_score=100,
            max_score=100,
            color="#10B981", # Green
            feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli hızda ve doğrulukta okuma yapmaktadır. Bu okuma seviyesi Hızlı Okuma için güzel bir başlangıçtır. Öğrencinin eğitim hayatına kalıcı bir hız ve iyi bir yatırım yapmanın tam zamanı! Kurumumuzu arayarak Anlayarak Hızlı Okuma Eğitimi hakkında bilgi alabilir ve zaman kaybetmeden eğitime kaydolabilirsiniz. Unutmayın, ağaç yaşken eğilir."
        ),
        ScoreRange(
            min_score=90,
            max_score=99,
            color="#3B82F6", # Blue
            feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli sayılabilecek hızda ve doğrulukta okuma yapmaktadır. Bu okuma seviyesi Hızlı Okuma için güzel bir başlangıç olabilir. Öğrencinin eğitim hayatına kalıcı bir hız ve iyi bir yatırım yapmanın için tam zamanı! Kurumumuzu arayarak Anlayarak Hızlı Okuma Eğitimi hakkında bilgi alabilir ve zaman kaybetmeden eğitimi kaydolabilirsiniz. Unutmayın, ağaç yaşken eğilir."
        ),
        ScoreRange(
            min_score=50,
            max_score=89,
            color="#8B5CF6", # Purple
            feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre yeterli hıza ulaşmak için desteğe ihtiyaç duymaktadır. Bu konuda DOKY Eğitimi sizin için önerebileceğimiz iyi bir yatırımdır. Bu eğitimle birlikte öğrencimizin okuması istenilen düzeye çıkacak ve öğrencimiz Anlayarak Hızlı Okuma Eğitimi için hazır hale gelecektir. Sizleri daha detaylı bilgilendirebilmemiz ve sizlere destek olabilmemiz için bir telefon uzağınızdayız."
        ),
        ScoreRange(
            min_score=0,
            max_score=49,
            color="#F59E0B", # Orange
            feedback="Öğrencimiz, bulunduğu sınıf düzeyine ve yaşına göre okuma becerilerini geliştirmelidir. Bu konuda uzman eğitimci kadromuz, patentli eğitimimiz ve yıllarca süren tecrübemizle sizlere destek olmaya hazırız. İhtiyacınız olan eğitim DOKY Eğitimi'dir. Kurumumuzu arayarak bilgi alabilir, özel ders veya grup dersleri seçeneğinden sizlere uygun olan eğitimle devam edebilirsiniz. Bu süreçte hızlı olmanızı önermekteyiz. Unutmayın, vakit nakittir."
        ),
    ]
    
    # Check if default config already exists
    existing_config = await ScoreFeedbackDoc.find_one({"name": "Varsayılan Puan Dönütü"})
    if existing_config:
        logger.info("Default score feedback configuration already exists, updating with complete detailed comments...")
        # Update existing config with complete detailed comments
        existing_config.detailed_comments = detailed_comments
        existing_config.updated_at = get_turkish_now()
        await existing_config.save()
        logger.info("✅ Updated existing score feedback configuration with complete detailed comments")
        mongo_client.close()
        return
    
    # Create the default configuration
    config = ScoreFeedbackDoc(
        name="Varsayılan Puan Dönütü",
        description="Sistem için varsayılan puan dönütü konfigürasyonu",
        is_active=True,
        score_ranges=score_ranges,
        detailed_comments=detailed_comments,
        created_at=get_turkish_now(),
        updated_at=get_turkish_now()
    )
    await config.insert()
    logger.info("✅ Complete score feedback configuration created successfully")
    
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(create_complete_score_feedback())
