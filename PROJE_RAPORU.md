# Proje Raporu

## 1. Dosya Yapısı

```
okuma-analizi/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Konfigürasyon ayarları
│   │   ├── crud.py                   # CRUD operasyonları
│   │   ├── db.py                     # MongoDB bağlantısı
│   │   ├── db_init_guard.py          # Veritabanı index yönetimi
│   │   ├── logging_config.py         # Loguru loglama
│   │   ├── main.py                   # FastAPI uygulaması
│   │   ├── middleware.py             # Request logging middleware
│   │   ├── schemas.py                # Pydantic şemaları
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── documents.py          # Beanie ODM modelleri
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── analyses.py           # Analiz API endpoints
│   │   │   ├── audio.py              # Ses dosyası API endpoints
│   │   │   ├── sessions.py           # Okuma oturumu API endpoints
│   │   │   ├── texts.py              # Metin API endpoints
│   │   │   └── upload.py             # Upload API endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── alignment.py          # Metin hizalama servisi
│   │   │   └── scoring.py            # Skorlama servisi
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── gcs.py                # Google Cloud Storage
│   │   └── utils/
│   │       └── text_tokenizer.py     # Türkçe metin tokenizer
│   ├── Dockerfile
│   ├── requirements.txt
│   └── scripts/                      # Veritabanı yönetim scriptleri
├── frontend/                         # Next.js Frontend
│   ├── app/
│   │   ├── analyses/page.tsx         # Analiz listesi sayfası
│   │   ├── analysis/[id]/page.tsx    # Analiz detay sayfası
│   │   ├── texts/page.tsx            # Metin yönetimi sayfası
│   │   ├── page.tsx                  # Ana sayfa (upload)
│   │   ├── layout.tsx                # Layout component
│   │   └── globals.css               # Global CSS
│   ├── components/
│   │   ├── DebugButton.tsx           # Debug paneli butonu
│   │   ├── DebugPanel.tsx            # Debug paneli
│   │   └── Navigation.tsx            # Navigasyon
│   ├── lib/
│   │   ├── api.ts                    # API client
│   │   ├── dateUtils.ts              # Tarih yardımcıları
│   │   ├── debug-store.ts            # Debug state
│   │   ├── store.ts                  # Zustand state management
│   │   └── tokenize.ts               # Frontend tokenizer
│   ├── Dockerfile
│   └── package.json
├── worker/                           # Python Worker
│   ├── __init__.py
│   ├── config.py                     # Worker konfigürasyonu
│   ├── db.py                         # Worker DB bağlantısı
│   ├── jobs.py                       # RQ job işleyicileri
│   ├── main.py                       # Worker entry point
│   ├── requirements.txt
│   └── services/
│       ├── __init__.py
│       ├── alignment.py              # Levenshtein hizalama (geliştirilmiş)
│       ├── elevenlabs_stt.py         # ElevenLabs STT API
│       ├── pauses.py                 # Duraksama tespiti
│       └── scoring.py                # WER/Accuracy hesaplama
├── docker-compose.yml                # Docker Compose konfigürasyonu
├── Makefile                          # Proje yönetim komutları
└── tests/                            # Test dosyaları
    ├── conftest.py
    ├── test_alignment_no_merge.py
    ├── test_analysis_pipeline_events.py
    ├── test_api_sessions.py
    ├── test_migration_v2.py
    ├── test_models_indexes.py
    └── test_stt_passthrough.py
```

## 2. Backend

### Kullanılan Framework ve Teknolojiler
- **FastAPI**: Web framework
- **Beanie**: MongoDB ODM (Object Document Mapper)
- **Pydantic**: Veri validasyonu ve serialization
- **Redis**: Job queue (RQ - Redis Queue)
- **Google Cloud Storage**: Dosya depolama
- **Loguru**: Gelişmiş loglama
- **SlowAPI**: Rate limiting

### Mevcut Modeller

#### TextDoc
```python
class TextDoc(Document):
    slug: str                          # Unique slug identifier
    grade: int                         # Sınıf seviyesi (1-4)
    title: str                         # Metin başlığı
    body: str                          # Metin içeriği
    canonical: CanonicalTokens         # Canonical tokenization
    comment: Optional[str]             # Yorum
    created_at: datetime               # Oluşturulma tarihi
    active: bool                       # Aktif/pasif durumu
```

#### AudioFileDoc
```python
class AudioFileDoc(Document):
    # Core fields
    original_name: str                 # Orijinal dosya adı
    duration_ms: Optional[int]         # Süre (milisaniye)
    sr: Optional[int]                  # Sample rate
    uploaded_at: datetime              # Yüklenme tarihi
    
    # GCS metadata fields
    text_id: Optional[ObjectId]        # İlişkili metin ID
    storage_name: str                  # GCS blob adı
    gcs_uri: str                       # GCS URI
    content_type: Optional[str]        # MIME type
    size_bytes: Optional[int]          # Dosya boyutu
    duration_sec: Optional[float]      # Süre (saniye)
    
    # Hash information
    hash: HashInfo                     # MD5/SHA256 hash bilgileri
    
    # Privacy and ownership
    privacy: PrivacyInfo               # Gizlilik politikası
    owner: OwnerInfo                   # Sahip bilgileri
```

#### AnalysisDoc
```python
class AnalysisDoc(Document):
    session_id: ObjectId               # ReadingSessionDoc referansı
    status: Literal["queued", "running", "done", "failed"]
    started_at: Optional[datetime]     # Başlama zamanı
    finished_at: Optional[datetime]    # Bitiş zamanı
    summary: Dict[str, Any]            # Analiz sonuçları
    error: Optional[str]               # Hata mesajı
    created_at: datetime               # Oluşturulma tarihi
```

#### ReadingSessionDoc
```python
class ReadingSessionDoc(Document):
    text_id: ObjectId                  # TextDoc referansı
    audio_id: ObjectId                 # AudioFileDoc referansı
    reader_id: Optional[str]           # Okuyucu ID
    status: Literal["active", "completed", "cancelled"]
    created_at: datetime               # Oluşturulma tarihi
    completed_at: Optional[datetime]   # Tamamlanma tarihi
```

#### WordEventDoc
```python
class WordEventDoc(Document):
    analysis_id: ObjectId              # AnalysisDoc referansı
    position: int                      # Metindeki pozisyon
    ref_token: Optional[str]           # Referans token
    hyp_token: Optional[str]           # Hipotez token
    type: Literal["correct", "missing", "extra", "substitution"]
    sub_type: Optional[str]            # Detaylı alt tür sınıflandırması
    timing: Optional[Dict[str, float]] # start_ms, end_ms
    char_diff: Optional[int]           # Karakter seviyesi fark
```

#### PauseEventDoc
```python
class PauseEventDoc(Document):
    analysis_id: ObjectId              # AnalysisDoc referansı
    after_position: int                # Duraksama sonrası pozisyon
    duration_ms: float                 # Duraksama süresi (milisaniye)
    class_: Literal["short", "medium", "long", "very_long"]
    start_ms: float                    # Başlangıç zamanı (milisaniye)
    end_ms: float                      # Bitiş zamanı (milisaniye)
```

#### SttResultDoc
```python
class SttResultDoc(Document):
    session_id: ObjectId               # ReadingSessionDoc referansı
    provider: str                      # STT sağlayıcısı (elevenlabs, whisper)
    model: str                         # Model adı/versiyonu
    language: str                      # Tespit edilen dil kodu
    transcript: str                    # Tam transkript metni
    words: List[WordData]              # Kelime seviyesi veri
    created_at: datetime               # Oluşturulma tarihi
```

### Settings.indexes İçeriği

#### TextDoc Indexes
- `texts_slug_asc` (unique): slug alanı
- `texts_grade_asc`: grade alanı
- `texts_created_at_desc`: created_at alanı (descending)
- `texts_active_asc`: active alanı

#### AudioFileDoc Indexes
- `audios_storage_name_asc` (unique): storage_name alanı
- `audios_gcs_uri_asc` (unique): gcs_uri alanı
- `audios_text_id_asc`: text_id alanı
- `audios_uploaded_at_desc`: uploaded_at alanı (descending)
- `audios_owner_reader_id_asc`: owner.reader_id alanı

#### AnalysisDoc Indexes
- `analyses_session_id_asc`: session_id alanı
- `analyses_created_at_desc`: created_at alanı (descending)
- `analyses_status_asc`: status alanı

#### ReadingSessionDoc Indexes
- `sessions_text_id_asc`: text_id alanı
- `sessions_audio_id_asc`: audio_id alanı
- `sessions_reader_id_asc`: reader_id alanı
- `sessions_status_asc`: status alanı
- `sessions_created_at_desc`: created_at alanı (descending)

#### WordEventDoc Indexes
- `word_events_analysis_id_asc`: analysis_id alanı
- `word_events_position_asc`: position alanı
- `word_events_type_asc`: type alanı
- `word_events_analysis_position_asc`: analysis_id + position composite

#### PauseEventDoc Indexes
- `pause_events_analysis_id_asc`: analysis_id alanı
- `pause_events_after_position_asc`: after_position alanı
- `pause_events_class_asc`: class_ alanı
- `pause_events_duration_ms_desc`: duration_ms alanı (descending)

#### SttResultDoc Indexes
- `stt_results_session_id_asc`: session_id alanı
- `stt_results_provider_asc`: provider alanı
- `stt_results_language_asc`: language alanı
- `stt_results_created_at_desc`: created_at alanı (descending)

### API Endpoints

#### Text Endpoints (`/v1/texts`)
- `GET /` - Tüm aktif metinleri listele
- `POST /` - Yeni metin oluştur
- `POST /copy` - Dışarıdan metin kopyala
- `GET /{text_id}` - Belirli metni getir
- `PUT /{text_id}` - Metni güncelle
- `DELETE /{text_id}` - Metni pasifleştir (soft delete)

#### Upload Endpoints (`/v1/upload`)
- `POST /` - Ses dosyası yükle ve analiz başlat
- `POST /audios` - Standalone ses dosyası yükle
- `GET /status/{analysis_id}` - Analiz durumunu sorgula

#### Analysis Endpoints (`/v1/analyses`)
- `GET /` - Analiz listesi (pagination ile)
- `GET /{analysis_id}` - Analiz detayı
- `POST /file` - Dosya analizi (text_id veya custom_text ile)
- `GET /{analysis_id}/audio-url` - Signed URL oluştur

#### Audio Endpoints (`/v1/audio`)
- `GET /` - Ses dosyalarını listele
- `GET /{audio_id}` - Ses dosyası detayı
- `PUT /{audio_id}` - Ses dosyası güncelle
- `DELETE /{audio_id}` - Ses dosyası sil
- `GET /text/{text_id}` - Metne ait ses dosyaları
- `GET /text/{text_id}/count` - Metne ait ses dosyası sayısı

#### Session Endpoints (`/v1/sessions`)
- `GET /` - Okuma oturumlarını listele
- `POST /` - Yeni okuma oturumu oluştur
- `GET /{session_id}` - Oturum detayı
- `PUT /{session_id}` - Oturum güncelle
- `DELETE /{session_id}` - Oturum sil

## 3. Frontend

### Teknoloji Stack
- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Zustand**: State management
- **Axios**: HTTP client

### Sayfalar ve Bileşenler

#### Ana Sayfa (`/`)
- **Fonksiyon**: Ses dosyası yükleme ve analiz başlatma
- **Özellikler**:
  - Drag & drop dosya yükleme
  - Metin seçimi (grade bazında filtreleme)
  - Custom metin girişi
  - Real-time analiz durumu takibi
  - Debug paneli

#### Analiz Listesi (`/analyses`)
- **Fonksiyon**: Geçmiş analizleri görüntüleme
- **Özellikler**:
  - Durum bazında filtreleme (all, queued, running, done, failed)
  - Pagination (50 analiz limit)
  - Real-time güncellemeler
  - Analiz detayına yönlendirme

#### Analiz Detayı (`/analysis/[id]`)
- **Fonksiyon**: Detaylı analiz sonuçları
- **Özellikler**:
  - WER, Accuracy, WPM metrikleri
  - Kelime seviyesi hata analizi
  - Ses dosyası oynatma (signed URL ile)
  - Duraksama analizi

#### Metin Yönetimi (`/texts`)
- **Fonksiyon**: Metin CRUD operasyonları
- **Özellikler**:
  - Metin oluşturma/düzenleme
  - Dışarıdan metin kopyalama
  - Soft delete (pasifleştirme)
  - Grade bazında organizasyon

### Veri Çekme (api.ts)

#### API Client Fonksiyonları
```typescript
// Texts
getTexts(): Promise<Text[]>
createText(text: TextCreate): Promise<Text>
copyText(text: TextCopyCreate): Promise<Text>
updateText(id: string, text: TextUpdate): Promise<Text>
deleteText(id: string): Promise<void>

// Upload
uploadAudio(file: File, textId: string): Promise<UploadResponse>

// Audio URL
getAnalysisAudioUrl(analysisId: string, expirationHours: number): Promise<AudioUrlResponse>

// Analyses
getAnalyses(limit: number): Promise<AnalysisSummary[]>
getAnalysis(id: string): Promise<AnalysisDetail>
getAnalysisStatus(id: string): Promise<{ status: string }>

// Sessions
getSessions(): Promise<Session[]>
createSession(session: SessionCreate): Promise<Session>
updateSession(id: string, session: SessionUpdate): Promise<Session>
deleteSession(id: string): Promise<void>
```

### Ses Oynatma
- **GCS URL Kullanımı**: Hayır, public URL kullanılmıyor
- **Signed URL**: Evet, `getAnalysisAudioUrl` endpoint'i ile 1-24 saat arası geçerli signed URL oluşturuluyor
- **Güvenlik**: Ses dosyaları private, sadece signed URL ile erişilebiliyor

## 4. Analiz Akışı

### STT → Hizalama → Skor Pipeline

#### 1. STT (Speech-to-Text) - ElevenLabs
**Dosya**: `worker/services/elevenlabs_stt.py`
- **API**: ElevenLabs Speech-to-Text API
- **Model**: `scribe_v1` (varsayılan)
- **Dil**: Türkçe (`tr`)
- **Özellikler**:
  - Word-level timestamps
  - Language detection
  - Confidence scores
  - Character-level timestamps (`timestamps_granularity: "character"`)

#### 2. Hizalama (Alignment) - Levenshtein (Geliştirilmiş)
**Dosya**: `worker/services/alignment.py`
- **Algoritma**: Dynamic Programming Levenshtein Distance
- **Yeni Özellikler**:
  - **Normalizasyon**: Case-insensitive ve noktalama işareti göz ardı etme
  - **Stopword Ağırlıklandırma**: "ve", "de", "da", "ile", "mi/mı/mu/mü", "ki" için düşük maliyet
  - **Akıllı Hizalama**: Stopword'ler yanlışlıkla substitution yaratmıyor
- **Fonksiyonlar**:
  - `_norm_token()`: Token normalizasyonu
  - `_is_stop()`: Stopword kontrolü
  - `_get_operation_cost()`: Stopword-aware maliyet hesaplama
  - `levenshtein_align()`: Geliştirilmiş hizalama
  - `classify_replace()`: Hata türü sınıflandırması
  - `build_word_events()`: Kelime seviyesi olaylar

#### 3. Skorlama (Scoring)
**Dosya**: `worker/services/scoring.py`
- **Metrikler**:
  - WER (Word Error Rate)
  - Accuracy (Doğruluk yüzdesi)
  - WPM (Words Per Minute)
- **Hesaplama**: Subs, dels, ins sayılarından

#### 4. Duraksama Tespiti
**Dosya**: `worker/services/pauses.py`
- **Kaynak**: ElevenLabs spacing data
- **Threshold**: 500ms (varsayılan)
- **Sınıflandırma**: short, medium, long, very_long
- **Çıktı**: PauseEventDoc listesi

### Worker Job İşleme
**Dosya**: `worker/jobs.py`
- **Queue**: Redis Queue (RQ)
- **Job Function**: `analyze_audio(analysis_id)`
- **İşlem Sırası**:
  1. AnalysisDoc durumunu "running" yap
  2. ReadingSessionDoc, AudioFileDoc ve TextDoc'u getir
  3. GCS'den ses dosyasını indir
  4. ElevenLabs ile transkripsiyon
  5. Levenshtein hizalama (geliştirilmiş)
  6. Metrik hesaplama
  7. Duraksama tespiti
  8. WordEventDoc ve PauseEventDoc oluştur
  9. Sonuçları AnalysisDoc'a kaydet

## 5. Teknik Borçlar / Riskler

### 🟢 Çözülen Riskler

#### 1. Public URL Kullanımı
- **Durum**: ✅ Çözüldü - Signed URL kullanılıyor
- **Önceki Durum**: GCS public URL'leri kullanılıyordu
- **Mevcut**: `generate_signed_url()` ile güvenli erişim

#### 2. IndexModel Hataları
- **Durum**: ✅ Çözüldü - `db_init_guard.py` ile normalize ediliyor
- **Sorun**: Beanie index tanımları MongoDB'de doğru oluşturulmuyordu
- **Çözüm**: `normalize_beanie_indexes()` fonksiyonu

#### 3. Alignment İyileştirmeleri
- **Durum**: ✅ Çözüldü - Gelişmiş alignment algoritması
- **Önceki Sorun**: Case/punctuation farkları yanlış substitution yaratıyordu
- **Mevcut**: Normalize karşılaştırma ve stopword-aware maliyet hesaplama

### 🟡 Orta Riskler

#### 1. ID Yönetimi Karmaşıklığı
- **Sorun**: `text_id` (string) vs MongoDB `_id` (ObjectId) karışıklığı
- **Etki**: Upload endpoint'inde text validation hatası
- **Çözüm**: `ObjectId(text_id)` ile dönüşüm

#### 2. Error Handling
- **Sorun**: Bazı exception'lar generic mesajlarla yakalanıyor
- **Etki**: Debug zorluğu
- **Öneri**: Daha spesifik error mesajları

#### 3. Rate Limiting
- **Durum**: ✅ Mevcut - SlowAPI ile
- **Limitler**: Upload 5/dakika, Audio 10/dakika
- **Risk**: Production'da yetersiz olabilir

### 🟢 Düşük Riskler

#### 1. Logging
- **Durum**: ✅ İyi - Loguru ile structured logging
- **Özellikler**: Request ID binding, JSON format, file rotation

#### 2. Configuration
- **Durum**: ✅ İyi - Pydantic Settings
- **Özellikler**: Environment variables, .env support

#### 3. Docker Setup
- **Durum**: ✅ İyi - Docker Compose ile
- **Servisler**: Backend, Frontend, Worker, MongoDB, Redis

## 6. Özet Tablo

| Koleksiyon | Model Dosyası | Alanlar | İndeksler |
|------------|---------------|---------|-----------|
| **texts** | `TextDoc` | slug, grade, title, body, canonical, comment, created_at, active | slug (unique), grade, created_at (desc), active |
| **audio_files** | `AudioFileDoc` | original_name, duration_ms, sr, text_id, storage_name, gcs_uri, content_type, size_bytes, duration_sec, hash, privacy, owner, uploaded_at | storage_name (unique), gcs_uri (unique), text_id, uploaded_at (desc), owner.reader_id |
| **analyses** | `AnalysisDoc` | session_id, status, started_at, finished_at, summary, error, created_at | session_id, created_at (desc), status |
| **reading_sessions** | `ReadingSessionDoc` | text_id, audio_id, reader_id, status, created_at, completed_at | text_id, audio_id, reader_id, status, created_at (desc) |
| **word_events** | `WordEventDoc` | analysis_id, position, ref_token, hyp_token, type, sub_type, timing, char_diff | analysis_id, position, type, analysis_id+position composite |
| **pause_events** | `PauseEventDoc` | analysis_id, after_position, duration_ms, class_, start_ms, end_ms | analysis_id, after_position, class_, duration_ms (desc) |
| **stt_results** | `SttResultDoc` | session_id, provider, model, language, transcript, words, created_at | session_id, provider, language, created_at (desc) |

## 7. Sistem Akışı

### Upload → Analysis Pipeline
1. **Frontend**: Kullanıcı ses dosyası + metin seçer
2. **Backend**: 
   - ReadingSessionDoc oluşturur
   - Ses dosyasını GCS'e yükler
   - AudioFileDoc oluşturur
   - AnalysisDoc oluşturur (status: "queued")
   - Redis'e job ekler
3. **Worker**: 
   - Job'u işler
   - ElevenLabs STT çağırır
   - Geliştirilmiş Levenshtein hizalama yapar
   - Metrikleri hesaplar
   - WordEventDoc ve PauseEventDoc oluşturur
   - Sonuçları AnalysisDoc'a kaydeder
4. **Frontend**: Polling ile durumu takip eder

### Veri Güvenliği
- **Ses Dosyaları**: Private GCS bucket, signed URL ile erişim
- **Veritabanı**: MongoDB authentication (production'da)
- **API**: Rate limiting, input validation
- **Logging**: Request ID tracking, structured logs

## 8. Performans Notları

### Optimizasyonlar
- **Batch Queries**: Analysis listesinde text/audio lookup'ları batch'lenmiş
- **Indexing**: Tüm sorgu alanları için index'ler mevcut
- **Caching**: Redis job queue
- **File Cleanup**: Temporary dosyalar otomatik temizleniyor
- **Alignment**: Stopword-aware maliyet hesaplama ile daha doğru hizalama

### Monitoring
- **Logging**: Request ID ile trace edilebilir
- **Metrics**: WER, Accuracy, WPM hesaplanıyor
- **Timing**: Debug mode'da detaylı timing bilgileri
- **Error Tracking**: Structured error logging

## 9. Test Coverage

### Mevcut Testler
- `test_alignment_no_merge.py`: Alignment algoritması testleri
- `test_analysis_pipeline_events.py`: Analiz pipeline testleri
- `test_api_sessions.py`: Session API testleri
- `test_migration_v2.py`: Veritabanı migrasyon testleri
- `test_models_indexes.py`: Model ve index testleri
- `test_stt_passthrough.py`: STT servis testleri

### Test Sonuçları
- **Case/Punctuation Test**: ✅ Başarılı - "Bu" vs "bu" correct olarak işaretleniyor
- **Stopword Test**: ✅ Başarılı - "ve" delete, "Kuşlar" doğru kelimeyle hizalanıyor
- **Alignment İyileştirmesi**: ✅ WER 7.2'den 6.9'a düştü, Accuracy %60'tan %90'a çıktı

---

**Rapor Tarihi**: 2025-01-19  
**Proje Durumu**: Production Ready  
**Son Güncelleme**: Alignment algoritması iyileştirildi, stopword-aware maliyet hesaplama eklendi, case/punctuation normalizasyonu implementasyonu tamamlandı