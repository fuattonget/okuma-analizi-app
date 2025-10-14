# Okuma Analizi Projesi - Proje Mimarisi

## 1. Proje Bileşenleri ve Kullanılan Teknolojiler

### **Arka Uç (API/BE)**
- **Dil:** Python 3.11
- **Framework:** FastAPI 0.104.1
- **ASGI Server:** Uvicorn 0.24.0
- **ORM/ODM:** Beanie 1.25.0 (MongoDB için)
- **Motor:** Motor 3.3.2 (Async MongoDB driver)
- **Kimlik Doğrulama:** JWT (python-jose), Passlib (bcrypt)
- **Rate Limiting:** SlowAPI
- **Logging:** Loguru
- **CORS:** FastAPI-CORS

### **Ön Uç (FE)**
- **Framework:** Next.js 14.0.0
- **Dil:** TypeScript 5.0.0
- **UI Library:** React 18.0.0
- **Styling:** Tailwind CSS 3.3.0
- **State Management:** Zustand 4.4.0
- **HTTP Client:** Axios 1.6.0
- **Build Tool:** Next.js (Webpack + SWC)
- **Development:** ESLint, PostCSS, Autoprefixer

### **Worker Servisi**
- **Dil:** Python 3.11
- **Framework:** RQ (Redis Queue) 1.15.1
- **Ana Görev:** Redis kuyruğunu dinleyerek ses analizi işlerini asenkron olarak işleme
- **Ses İşleme:** SoundFile, Pydub, NumPy
- **STT API:** ElevenLabs Speech-to-Text
- **Analiz Algoritmaları:** Custom alignment, scoring, pause detection

## 2. Depolama ve Harici Servis Bağlantıları

### **Veritabanı**
- **Tür:** MongoDB 7.0
- **Bağlantı:** Motor (async) + PyMongo (sync)
- **ODM:** Beanie (Pydantic tabanlı)
- **Bağlantı URI:** `mongodb://localhost:27017` (local) / MongoDB Atlas (production)

### **Önbellek/Kuyruk**
- **Tür:** Redis 7.2
- **Kullanım Amaçları:**
  - **Job Queue:** RQ ile asenkron iş işleme
  - **Session Storage:** Oturum yönetimi
  - **Caching:** Geçici veri önbellekleme
- **Bağlantı:** `redis://localhost:6379` (local) / Redis Cloud (production)

### **Harici API'ler**

#### **ElevenLabs Speech-to-Text**
- **API Endpoint:** `https://api.elevenlabs.io/v1/speech-to-text`
- **Model:** `scribe_v1_experimental` (daha iyi kalite için)
- **Dil:** Türkçe (`tr`)
- **Özellikler:**
  - Word-level timestamps
  - Deterministic results (temperature: 0.0)
  - Filler words ve disfluencies korunur (analiz için)
  - Random seed: 12456 (reproducibility)

#### **Google Cloud Storage (GCS)**
- **Bucket:** `doky_ai_audio_storage`
- **Kimlik Doğrulama:** Service Account JSON
- **Kullanım:**
  - Ses dosyalarını yükleme
  - Signed URL'ler ile güvenli erişim
  - Private bucket (public erişim yok)
- **Kütüphane:** `google-cloud-storage==3.3.1`

## 3. Bileşenler Arası İletişim (Veri Akışı)

### **FE → BE**
- **HTTP Client:** Axios
- **Base URL:** `http://localhost:8000` (local) / Vercel URL (production)
- **Authentication:** JWT Bearer Token (localStorage'da saklanır)
- **Request Interceptors:** Token otomatik ekleme
- **Response Interceptors:** 401 hatalarında otomatik logout
- **Timeout:** 30 saniye

### **BE → Worker**
- **Queue System:** RQ (Redis Queue)
- **Queue Name:** `main`
- **Job Type:** `analyze_audio(analysis_id)`
- **İletişim:** Redis üzerinden job enqueue/dequeue
- **Worker Command:** `rq worker -u redis://redis:6379/0 main --with-scheduler`

### **BE/Worker → Depolama**

#### **MongoDB Veri Akışı:**
```
Audio Upload → AudioFileDoc
Session Creation → ReadingSessionDoc
Analysis Job → AnalysisDoc
Word Events → WordEventDoc
Pause Events → PauseEventDoc
STT Results → SttResultDoc
```

#### **GCS Veri Akışı:**
```
Frontend Upload → Backend → GCS Bucket
Analysis → Signed URL Generation → Frontend Audio Playback
```

## 4. Kritik Ortam Değişkenleri

### **Backend/Worker Ortam Değişkenleri**

#### **Veritabanı Bağlantıları**
```bash
MONGO_URI=mongodb://localhost:27017              # MongoDB bağlantı URI
MONGO_DB=okuma_analizi                           # Veritabanı adı
REDIS_URL=redis://localhost:6379                 # Redis bağlantı URL
```

#### **Harici API Anahtarları**
```bash
ELEVENLABS_API_KEY=sk_xxx                        # ElevenLabs API anahtarı
GCS_CREDENTIALS_PATH=./gcs-service-account.json  # GCS service account dosyası
GCS_BUCKET=doky_ai_audio_storage                 # GCS bucket adı
```

#### **ElevenLabs Konfigürasyonu**
```bash
ELEVENLABS_MODEL=scribe_v1_experimental          # STT model
ELEVENLABS_LANGUAGE=tr                           # Dil kodu
ELEVENLABS_TEMPERATURE=0.0                       # Deterministic sonuçlar
ELEVENLABS_SEED=12456                           # Random seed
ELEVENLABS_REMOVE_FILLER_WORDS=false            # Filler words korunur
ELEVENLABS_REMOVE_DISFLUENCIES=false            # Disfluencies korunur
```

#### **JWT Konfigürasyonu**
```bash
JWT_SECRET=your-secret-key                       # JWT imzalama anahtarı
JWT_ALGORITHM=HS256                              # JWT algoritması
JWT_EXPIRATION_MINUTES=43200                     # Token geçerlilik süresi (30 gün)
```

#### **CORS ve API Ayarları**
```bash
CORS_ORIGINS=["*"]                               # CORS izin verilen originler
API_HOST=0.0.0.0                                # API host
API_PORT=8000                                    # API port
```

### **Frontend Ortam Değişkenleri**

#### **API Bağlantısı**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000        # Backend API URL
```

### **Production Ortam Değişkenleri (Vercel/Railway)**

#### **MongoDB Atlas**
```bash
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/okuma_analizi
```

#### **Redis Cloud**
```bash
REDIS_URL=redis://username:password@host:port
REDIS_HOST=your-redis-host
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-password
```

#### **Google Cloud Storage**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_PROJECT_ID=your-gcp-project-id
```

## 5. Proje Dizin Yapısı

```
okuma-analizi/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── models/            # Beanie MongoDB modelleri
│   │   ├── routers/           # API endpoint'leri
│   │   ├── services/          # Business logic
│   │   ├── storage/           # GCS entegrasyonu
│   │   └── utils/             # Yardımcı fonksiyonlar
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   ├── app/                   # App Router (Next.js 13+)
│   ├── components/            # React bileşenleri
│   ├── lib/                   # API client, utilities
│   └── package.json
├── worker/                     # RQ worker servisi
│   ├── services/              # Analiz algoritmaları
│   ├── jobs.py                # RQ job fonksiyonları
│   └── main.py                # Worker entry point
├── docker-compose.yml         # Local development setup
└── scripts/                   # Utility scripts
```

## 6. Deployment Stratejisi

### **Local Development**
- Docker Compose ile tüm servisler
- MongoDB ve Redis container'ları
- Hot reload için volume mount'lar

### **Production Deployment**
- **Frontend:** Vercel (Next.js optimized)
- **Backend:** Railway/Render/Fly.io
- **Database:** MongoDB Atlas
- **Cache/Queue:** Redis Cloud
- **Storage:** Google Cloud Storage

### **Environment Separation**
- Local: `.env` dosyaları
- Production: Platform environment variables
- Secrets: Platform secret management (Vercel Secrets, Railway Variables)

Bu mimari, okuma analizi uygulamasının tüm bileşenlerini kapsamlı bir şekilde açıklamaktadır. Her bileşen kendi sorumluluğunu üstlenirken, modern web development best practice'lerini takip etmektedir.

