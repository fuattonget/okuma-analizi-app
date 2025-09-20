# Okuma Analizi Projesi - Sistem Mimarisi

## 📋 Genel Bakış

Bu proje, ses dosyalarını analiz ederek okuma performansını değerlendiren bir sistemdir. ElevenLabs Speech-to-Text API kullanarak Türkçe konuşmaları metne çevirir ve hedef metinle karşılaştırarak detaylı analiz raporu oluşturur.

## 🏗️ Sistem Bileşenleri

### 1. **Frontend (Next.js + TypeScript)**
- **Port:** 3000
- **Teknoloji:** Next.js 14, React, TypeScript, Tailwind CSS
- **Dosya:** `frontend/`
- **Görevler:**
  - Kullanıcı arayüzü
  - Ses dosyası yükleme
  - Analiz sonuçlarını görüntüleme
  - Metin yönetimi

### 2. **Backend API (FastAPI + Python)**
- **Port:** 8000
- **Teknoloji:** FastAPI, Pydantic, Beanie ODM
- **Dosya:** `backend/`
- **Görevler:**
  - REST API endpoints
  - Dosya yükleme ve GCS entegrasyonu
  - MongoDB veri yönetimi
  - Redis queue yönetimi

### 3. **Worker (Python + RQ)**
- **Teknoloji:** Python, RQ (Redis Queue), ElevenLabs API
- **Dosya:** `worker/`
- **Görevler:**
  - Ses dosyası transkripsiyonu
  - Metin analizi ve karşılaştırma
  - WER/WPM hesaplama
  - Uzun duraksama tespiti

### 4. **MongoDB (Veritabanı)**
- **Port:** 27017
- **Teknoloji:** MongoDB, Beanie ODM
- **Koleksiyonlar:**
  - `texts` - Hedef metinler
  - `audio_files` - Yüklenen ses dosyaları
  - `analyses` - Analiz sonuçları
  - `word_events` - Kelime seviyesi olaylar
  - `pause_events` - Duraksama olayları

### 5. **Redis (Queue + Cache)**
- **Port:** 6379
- **Teknoloji:** Redis, RQ
- **Görevler:**
  - Analiz job queue yönetimi
  - Worker koordinasyonu

### 6. **Google Cloud Storage (GCS)**
- **Teknoloji:** Google Cloud Storage
- **Bucket:** `doky_ai_audio_storage`
- **Görevler:**
  - Ses dosyalarını saklama
  - CDN benzeri dosya erişimi

## 🔄 Sistem Akışı - Ses Dosyası Yükleme

### Adım 1: Frontend → Backend API
```
POST /v1/upload/
Content-Type: multipart/form-data
- file: [ses_dosyası.mp3]
- text_id: [hedef_metin_id]
```

### Adım 2: Backend API İşlemleri
1. **Dosya Validasyonu**
   - Dosya tipi kontrolü (audio/mpeg, audio/wav, vb.)
   - Dosya boyutu kontrolü

2. **Text ID Validasyonu**
   - MongoDB'den text_id ile metin bulma
   - Text varlığını doğrulama

3. **GCS Upload**
   - Ses dosyasını Google Cloud Storage'a yükleme
   - Unique dosya adı oluşturma
   - GCS URL'i alma

4. **Database Kayıtları**
   - `AudioFileDoc` oluşturma (MongoDB)
   - `AnalysisDoc` oluşturma (status: "queued")

5. **Queue Job**
   - Redis queue'ya analiz job'u ekleme
   - Worker'a iş gönderme

### Adım 3: Worker İşlemleri
1. **Job Alımı**
   - Redis queue'dan job çekme
   - Analysis status'u "running" yapma

2. **Ses Dosyası İndirme**
   - GCS'den ses dosyasını indirme
   - Geçici dosya oluşturma

3. **ElevenLabs Transkripsiyon**
   - ElevenLabs API'ye ses dosyası gönderme
   - Word-level timestamps alma
   - Language detection

4. **Word Processing**
   - ElevenLabs response'unu işleme
   - Word combination logic (split words birleştirme)
   - Processed words oluşturma

5. **Text Alignment**
   - Reference text tokenization
   - Hypothesis text tokenization
   - Levenshtein alignment

6. **Metrics Calculation**
   - WER (Word Error Rate) hesaplama
   - WPM (Words Per Minute) hesaplama
   - Accuracy hesaplama

7. **Pause Detection**
   - ElevenLabs spacing data kullanma
   - 500ms+ uzun duraksamaları tespit etme
   - Pause events oluşturma

8. **Database Kayıtları**
   - Word events kaydetme
   - Pause events kaydetme
   - Analysis sonuçlarını güncelleme
   - Status'u "done" yapma

### Adım 4: Frontend Güncelleme
1. **Real-time Updates**
   - WebSocket veya polling ile status güncelleme
   - Progress bar gösterimi

2. **Sonuç Görüntüleme**
   - Analiz detaylarını gösterme
   - Word-level hataları gösterme
   - Pause events gösterme
   - Metrics gösterimi

## 🔗 Bileşenler Arası İletişim

### Frontend ↔ Backend API
- **HTTP REST API**
- **Endpoints:**
  - `GET /v1/texts/` - Metin listesi
  - `POST /v1/texts/` - Yeni metin ekleme
  - `POST /v1/texts/copy/` - Dışardan metin kopyalama
  - `GET /v1/analyses/` - Analiz listesi
  - `GET /v1/analyses/{id}` - Analiz detayı
  - `POST /v1/upload/` - Ses dosyası yükleme

### Backend API ↔ MongoDB
- **Beanie ODM**
- **Collections:**
  - TextDoc, AudioFileDoc, AnalysisDoc
  - WordEventDoc, PauseEventDoc

### Backend API ↔ Redis
- **RQ (Redis Queue)**
- **Queue:** "analysis"
- **Job:** "jobs.analyze_audio"

### Worker ↔ Redis
- **RQ Worker**
- **Queue monitoring**
- **Job processing**

### Worker ↔ MongoDB
- **Beanie ODM**
- **Document updates**
- **Bulk operations**

### Worker ↔ GCS
- **Google Cloud Storage Client**
- **File download/upload**
- **Service account authentication**

### Worker ↔ ElevenLabs API
- **HTTP REST API**
- **Speech-to-Text service**
- **Word-level timestamps**

## 📊 Veri Modelleri

### TextDoc
```python
{
  "_id": ObjectId,
  "title": str,
  "body": str,
  "grade": int,
  "comment": str,
  "created_at": datetime
}
```

### AudioFileDoc
```python
{
  "_id": ObjectId,
  "filename": str,
  "path": str,  # GCS URL
  "size": int,
  "content_type": str,
  "uploaded_at": datetime
}
```

### AnalysisDoc
```python
{
  "_id": ObjectId,
  "text_id": str,  # TextDoc._id
  "audio_id": str,  # AudioFileDoc._id
  "status": str,  # "queued", "running", "done", "failed"
  "created_at": datetime,
  "started_at": datetime,
  "finished_at": datetime,
  "summary": dict  # WER, WPM, accuracy, etc.
}
```

### WordEventDoc
```python
{
  "_id": ObjectId,
  "analysis_id": str,
  "idx": int,
  "ref_token": str,
  "hyp_token": str,
  "start_ms": float,
  "end_ms": float,
  "type": str,  # "correct", "missing", "extra", "diff"
  "subtype": str,
  "details": dict
}
```

### PauseEventDoc
```python
{
  "_id": ObjectId,
  "analysis_id": str,
  "after_word_idx": int,
  "start_ms": float,
  "end_ms": float,
  "duration_ms": float,
  "pause_type": str,
  "severity": str
}
```

## 🚀 Deployment (Docker)

### Docker Compose Servisleri
```yaml
services:
  mongodb:     # MongoDB database
  redis:       # Redis queue + cache
  api:         # FastAPI backend
  worker:      # RQ worker
  frontend:    # Next.js frontend
```

### Environment Variables
```bash
# ElevenLabs
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_MODEL=scribe_v1
ELEVENLABS_LANGUAGE=tr

# GCS
GCS_BUCKET=doky_ai_audio_storage
GCS_CREDENTIALS_PATH=./gcs-service-account.json

# Database
MONGODB_URL=mongodb://mongodb:27017/okuma_analizi
REDIS_URL=redis://redis:6379/0
```

## 🔧 Önemli Özellikler

### 1. Word Combination Logic
- ElevenLabs'den gelen split words'leri birleştirme
- Türkçe kelime pattern'leri tanıma
- Konservatif kombinasyon kuralları

### 2. Timezone Handling
- Türkiye saati (+03:00) kullanımı
- Frontend'de doğru saat gösterimi
- Backend'de UTC → TR conversion

### 3. Error Handling
- Comprehensive try-catch blocks
- Detailed logging (Loguru)
- Graceful error recovery

### 4. Pause Detection
- ElevenLabs spacing data kullanma
- 500ms+ uzun duraksamaları tespit
- Severity classification

### 5. Text Management
- Geçici metinler (UI'da gizli)
- Dışardan metin kopyalama
- Grade-based organization

## 📈 Performance Metrics

### WER (Word Error Rate)
- Hata oranı hesaplama
- Substitution, deletion, insertion sayıları

### WPM (Words Per Minute)
- Okuma hızı hesaplama
- İlk ve son kelime zamanları

### Pause Analysis
- Uzun duraksama sayısı
- Severity classification
- Timing analysis

## 🔍 Debugging & Monitoring

### Logging
- **Backend:** Loguru ile structured logging
- **Worker:** Detailed process logging
- **Frontend:** Console logging

### Health Checks
- **API:** `GET /health`
- **Database:** Connection status
- **Redis:** Queue status

### Error Tracking
- Exception handling
- Error categorization
- Recovery mechanisms

## 🎯 Kullanım Senaryoları

### 1. Öğretmen Analizi
- Öğrenci ses dosyası yükleme
- Hedef metin seçimi
- Detaylı analiz raporu

### 2. Self-Assessment
- Öğrenci kendi okumasını analiz etme
- Progress tracking
- Improvement suggestions

### 3. Batch Processing
- Multiple file upload
- Queue-based processing
- Bulk analysis results

Bu dokümantasyon, sistemin tüm bileşenlerini ve aralarındaki etkileşimleri detaylı olarak açıklamaktadır.

