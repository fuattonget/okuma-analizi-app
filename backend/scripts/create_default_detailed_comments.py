import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.detailed_comments import DetailedCommentsConfig, ErrorTypeComments, CommentRange
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_default_detailed_comments():
    """Create default detailed comments configuration"""
    
    # Connect to MongoDB
    mongo_url = os.getenv("MONGO_URI", settings.mongo_url or settings.mongo_uri)
    mongo_db = os.getenv("MONGO_DB", settings.mongo_db)
    logger.info(f"Connecting to MongoDB: {mongo_url}, database: {mongo_db}")
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[mongo_db]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[DetailedCommentsConfig])
    
    # Check if default config already exists
    existing_config = await DetailedCommentsConfig.find_one({"name": "Varsayılan Detaylı Yorumlar"})
    if existing_config:
        logger.info("Default detailed comments configuration already exists")
        mongo_client.close()
        return
    
    # Create error type configurations
    error_types = []
    
    # Doğru Okunan Kelime Sayısı (0-50 points)
    correct_words_ranges = [
        CommentRange(min_score=50, max_score=50, comment="Okumada kelimelerin tamamı / tamamına yakını doğru telaffuz edilmiştir. Sınıf düzeyine göre istenilen seviyede okunmuştur. Öğrencinin doğru okuma oranı iyidir."),
        CommentRange(min_score=40, max_score=49, comment="Okumada kelimelerin neredeyse tamamı doğru telaffuz edilmiştir. Ufak tefek hatalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre beklenen düzeydedir."),
        CommentRange(min_score=30, max_score=39, comment="Okumada kelimelerin telaffuzunda hatalar vardır. Yanlış okumalar mevcuttur. Öğrencinin doğru okuma oranı sınıf düzeyine göre ortalamanın biraz altındadır."),
        CommentRange(min_score=20, max_score=29, comment="Okumada kelimelerin telaffuzunda hatalar sınıf düzeyine göre fazladır. Öğrencinin okumasındaki hata oranı yaşına ve sınıf düzeyine uygun oranda değildir."),
        CommentRange(min_score=10, max_score=19, comment="Okumada kelimelerin telaffuzunda hata oranı yüksektir. Sınıf düzeyinin epey aşağısında bir okuma sergilenmiştir. Hata oranı çok fazladır."),
        CommentRange(min_score=0, max_score=9, comment="Okumada kelimelerin telaffuzları çok hatalıdır. Öğrenci sınıf düzeyine göre yetersiz ve kabul edilemeyecek bir okuma sergilemiştir.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="correct_words",
        error_type_display="Doğru Okunan Kelime Sayısı",
        comment_ranges=correct_words_ranges,
        max_score=50
    ))
    
    # Harf Eksiltme (0-5 points)
    harf_eksiltme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okumada harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenilen şekilde harf eksiltme hataları yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okumada birkaç yer hariç harf eksiltme hataları görülmemiştir. Öğrenci yaşından ve sınıf düzeyinden beklenildiği gibi fazlaca harf eksiltme yapmamıştır. Bir iki yerde harf eksiltme yapmıştır. Bu da normal olarak kabul edilebilir."),
        CommentRange(min_score=3, max_score=3, comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen orandan daha fazla harf eksiltme yapmıştır."),
        CommentRange(min_score=2, max_score=2, comment="Okumada harf eksiltme hataları görülmüştür. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Harf eksiltme hataları fazladır."),
        CommentRange(min_score=1, max_score=1, comment="Okumada harf eksiltme hataları fazladır. Öğrenci yaşından ve sınıf düzeyinden beklenilen performansı bu konuda gösterememiştir. Bu hatalar yaşına ve sınıf düzeyine göre ortalamanın altındadır."),
        CommentRange(min_score=0, max_score=0, comment="Okumada harf eksiltme hataları çok fazladır. Öğrencinin yaşından ve sınıf düzeyinden beklenilen oranın epey altında kalmıştır. Okumasında birçok yerde harf eksiltme görülmüştür.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="harf_eksiltme",
        error_type_display="Harf Eksiltme",
        comment_ranges=harf_eksiltme_ranges,
        max_score=5
    ))
    
    # Harf Ekleme (0-5 points)
    harf_ekleme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Öğrenci okuma yaparken harf ekleme yapmamıştır. Sınıf seviyesi ve yaşına göre uygun bir şekilde okumuştur."),
        CommentRange(min_score=4, max_score=4, comment="Öğrenci okuma yaparken birkaç yerde harf ekleme yapmıştır. Sınıf seviyesi ve yaşına göre uygun bir şekilde okumuştur. Yaptığı birkaç harf ekleme normal sayılabilir."),
        CommentRange(min_score=3, max_score=3, comment="Öğrenci okuma yaparken ara ara harf ekleme yapmıştır. Oransal olarak sınıf seviyesine ve yaşına göre ortalamanın biraz altında kalmıştır."),
        CommentRange(min_score=2, max_score=2, comment="Öğrenci okuma yaparken harf ekleme yapmaktadır. Sınıf düzeyi ve yaşından beklenmeyecek sayıda harf ekleme hataları mevcuttur."),
        CommentRange(min_score=1, max_score=1, comment="Öğrenci okuma yaparken harf ekleme yapmaktadır. Sınıf düzeyi ve yaşına göre bu kadar çok harf ekleme yapması kabul edilebilir oranda değildir."),
        CommentRange(min_score=0, max_score=0, comment="Öğrencinin okumasında çokça harf ekleme görülmüştür. Bu sınıf seviyesine ve yaşına göre yüksek oranda harf ekleme hataları mevcuttur.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="harf_ekleme",
        error_type_display="Harf Ekleme",
        comment_ranges=harf_ekleme_ranges,
        max_score=5
    ))
    
    # Harf Değiştirme (0-5 points)
    harf_degistirme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okuma yaparken harf değiştirme hataları gözlemlenmiştir. Öğrenci yaşından ve sınıf düzeyinden beklendiği gibi harf değiştirme hataları yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okuma yaparken harf değiştirme çok nadir de olsa gözlemlenmiştir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilecek kadar az harf değiştirme hatası gözlenlenmiştir."),
        CommentRange(min_score=3, max_score=3, comment="Okuma yaparken arada bir harf değiştirme yapabilmektedir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir orandan daha fazla harf ekleme hataları mevcuttur."),
        CommentRange(min_score=2, max_score=2, comment="Okuma yaparken harf değiştirme hataları gözlenlenmiştir. Bu hatalar öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir seviyede değildir."),
        CommentRange(min_score=1, max_score=1, comment="Okuma yaparken fazlaca harf değiştirme yapıldığı gözlemlenmiştir. Öğrenci yaşına ve sınıf düzeyine göre fazlaca harf değiştirme hatası yapmaktadır."),
        CommentRange(min_score=0, max_score=0, comment="Okuma yaparken sık sık harf değiştirme yapmaktadır. Öğrencinin yaşı ve sınıf düzeyi göz önünde buundurulduğunda öğrenci okumasında ciddi oranda harf değiştirme yapmaktadır.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="harf_degistirme",
        error_type_display="Harf Değiştirme",
        comment_ranges=harf_degistirme_ranges,
        max_score=5
    ))
    
    # Kelime Eksiltme (0-5 points)
    kelime_eksiltme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okuma sırasında kelime eksiltme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve kelime eksiltme hataları yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okuma sırasında nadiren kelime eksiltmiştir. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir."),
        CommentRange(min_score=3, max_score=3, comment="Okuma sırasında birkaç yerde kelime eksiltmeler görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime eksiltme yapmıştır."),
        CommentRange(min_score=2, max_score=2, comment="Okuma sırasında kelime eksiltme hataları mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda kelime eksiltme yapma oranı kabul edilebilir seviyede değildir."),
        CommentRange(min_score=1, max_score=1, comment="Okuma sırasında kelime eksiltme sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir."),
        CommentRange(min_score=0, max_score=0, comment="Okuma sırasında kelime eksiltmeler fazladır. Öğrenci yaşına göre ve sınıf düzeyine göre bu hataları epey fazla yapmıştır.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="kelime_eksiltme",
        error_type_display="Kelime Eksiltme",
        comment_ranges=kelime_eksiltme_ranges,
        max_score=5
    ))
    
    # Kelime Ekleme (0-5 points)
    kelime_ekleme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okuma yaparken kelime ekleme hataları gözlemlenmiştir. Öğrenci yaşından ve sınıf düzeyinden beklendiği gibi kelime ekleme hataları yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okuma yaparken kelime ekleme çok nadir de olsa gözlemlenmiştir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilecek kadar az kelime ekleme hatası gözlenlenmiştir."),
        CommentRange(min_score=3, max_score=3, comment="Okuma yaparken arada bir kelime ekleme yapabilmektedir. Öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir orandan daha fazla kelime ekleme hataları mevcuttur."),
        CommentRange(min_score=2, max_score=2, comment="Okuma yaparken kelime ekleme hataları gözlenlenmiştir. Bu hatalar öğrencinin yaşına ve sınıf düzeyine göre kabul edilebilir seviyede değildir."),
        CommentRange(min_score=1, max_score=1, comment="Okuma yaparken fazlaca kelime ekleme yapıldığı gözlemlenmiştir. Gözlemlenen bu hataların sayısı öğrencinin sınıf düzeyi ve yaşına göre uygun değildir."),
        CommentRange(min_score=0, max_score=0, comment="Okuma yaparken sık sık kelime ekleme yapmaktadır. Öğrencinin yaşı ve sınıf düzeyi göz önünde bulundurulduğunda öğrenci okumasında çok fazla oranda kelime ekleme yapmaktadır.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="kelime_ekleme",
        error_type_display="Kelime Ekleme",
        comment_ranges=kelime_ekleme_ranges,
        max_score=5
    ))
    
    # Kelime Değiştirme (0-5 points)
    kelime_degistirme_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okuma sırasında kelime değiştirme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve kelime değiştirme hataları yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okuma sırasında nadiren kelime değiştirmiştir. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir."),
        CommentRange(min_score=3, max_score=3, comment="Okuma sırasında birkaç yerde kelime değiştirmeler görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime değiştirme yapmıştır."),
        CommentRange(min_score=2, max_score=2, comment="Okuma sırasında kelime değiştirme hataları mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda kelime değiştirme oranı kabul edilebilir seviyede değildir."),
        CommentRange(min_score=1, max_score=1, comment="Okuma sırasında kelime değiştirme sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir."),
        CommentRange(min_score=0, max_score=0, comment="Okuma sırasında kelime değiştirmeler fazladır. Öğrencinin yaşı ve sınıf düzeyi düşünüldüğünde kelime değiştirme sayısı kabul edilemez orandadır.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="kelime_degistirme",
        error_type_display="Kelime Değiştirme",
        comment_ranges=kelime_degistirme_ranges,
        max_score=5
    ))
    
    # Uzun Duraksama (0-5 points)
    uzun_duraksama_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Öğrencinin kelime tanıma hızı yüksektir. Bulunduğu sınıf düzeyi ve yaşına uygun bir hızda kelimeyi tanıyıp okuyabilmekte ve tek seferde kelimeyi okuyabilmektedir."),
        CommentRange(min_score=4, max_score=4, comment="Öğrencinin kelime tanıma hızı iyidir. Nadir de olsa zorlandığı kelimeler olmuştur fakat genel anlamda bulunduğu sınıf düzeyi ve yaşına uygun bir hızda kelimeyi tanıyıp okuyabilmektedir."),
        CommentRange(min_score=3, max_score=3, comment="Öğrencinin kelime tanıma hızı beklenilen düzeyde değildir. Arada bir tek seferde okuyamadığı kelimeler gözlenmiştir. Gözlemlenen hata sayısı öğrencinin sınıf düzeyi ve yaşında göre beklenenden daha fazladır."),
        CommentRange(min_score=2, max_score=2, comment="Öğrencinin kelime tanıma hızı seviyesine göre düşüktür. Kelimeyi tek seferde okumakta zorlandığı yerler sayıca fazladır. Uzun duraksamalar gözlemlenmiştir."),
        CommentRange(min_score=1, max_score=1, comment="Öğrenci kelimeleri yaşından ve sınıf düzeyinden beklenmedik şekilde tek seferde okumakta zorlanmıştır. Sık sık duraksamalara ihtiyaç duymuştur."),
        CommentRange(min_score=0, max_score=0, comment="Öğrencinin kelime tanıma hızı çok düşüktür. Bulunduğu sınıf düzeyine ve yaşına uygun bir hızda kelimeleri okuyamamıştır. Sürekli duraksamaya ihtiyaç duymuştur.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="uzun_duraksama",
        error_type_display="Kelime Tanıma (Uzun Duraksama)",
        comment_ranges=uzun_duraksama_ranges,
        max_score=5
    ))
    
    # Tekrarlama (0-5 points)
    tekrarlama_ranges = [
        CommentRange(min_score=5, max_score=5, comment="Okuma esnasında tekrarlama veya heceleme gibi durumlar gözlemlenmemiştir. Öğrenci sınıf düzeyine ve yaşına uygun bir şekilde okumuş ve tekrarlama ya da heceleme yapmamıştır."),
        CommentRange(min_score=4, max_score=4, comment="Okuma esnasında nadiren tekrarlama veya heceleme yapmıştır. Bu oran öğrenci sınıf düzeyine ve yaşına göre kabul edilebilir bir seviyededir."),
        CommentRange(min_score=3, max_score=3, comment="Okuma esnasında birkaç yerde tekrarlama veya heceleme görülmüştür. Öğrenci sınıf düzeyine ve yaşına göre beklenenden daha fazla kelime tekrarlama veya heceleme yapmıştır."),
        CommentRange(min_score=2, max_score=2, comment="Okuma esnasında tekrarlamalar veya hecelemeler mevcuttur. Öğrencinin sınıf düzeyi ve yaşı göz önünde bulundurulduğunda tekrarlama veya hecelemeye başvurma oranı kabul edilebilir oranda değildir."),
        CommentRange(min_score=1, max_score=1, comment="Okuma esnasında tekrarlamalar veya hecelemeler sık sık gözlemlenmiştir. Öğrenci, sınıf düzeyinden ve yaşından beklenen okuma performansını gösterememiştir."),
        CommentRange(min_score=0, max_score=0, comment="Okuma esnasında yapılan tekrarlamalar veya hecelemeler fazladır. Öğrenci yaşına göre ve sınıf düzeyine göre bu hataları epey fazla yapmıştır.")
    ]
    error_types.append(ErrorTypeComments(
        error_type="tekrarlama",
        error_type_display="Tekrarlama / Heceleme",
        comment_ranges=tekrarlama_ranges,
        max_score=5
    ))
    
    # Create the default configuration
    config = DetailedCommentsConfig(
        name="Varsayılan Detaylı Yorumlar",
        description="Sistem için varsayılan detaylı yorum konfigürasyonu",
        is_active=True,
        error_types=error_types,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await config.insert()
    logger.info("✅ Default detailed comments configuration created successfully")
    
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(create_default_detailed_comments())
