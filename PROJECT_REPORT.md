# 📊 DOKY - Okuma Analizi Sistemi Proje Raporu

## 🎯 Proje Genel Bilgiler

**Proje Adı:** DOKY - Okuma Analizi Sistemi  
**Versiyon:** 0.1.0  
**Amaç:** Ses dosyalarından okuma analizi yaparak, hedef metinle karşılaştırma ve hata tespiti  
**Mimari:** Microservices (Backend API + Worker + Frontend)  
**Deployment:** Docker Compose

---

## 📁 Proje Yapısı

```
okuma-analizi/
├── backend/              # FastAPI Backend API
│   ├── app/             # Ana uygulama kodu
│   │   ├── main.py      # FastAPI entry point
│   │   ├── config.py    # Konfigürasyon ayarları
│   │   ├── db.py        # MongoDB ve Redis bağlantıları
│   │   ├── models/      # Beanie ODM modelleri
│   │   ├── routers/     # API endpoint'leri
│   │   ├── services/    # İş mantığı servisleri
│   │   └── storage/     # Google Cloud Storage entegrasyonu
│   ├── scripts/         # Yardımcı scriptler
│   ├── Dockerfile       # Backend container tanımı
│   └── requirements.txt # Python bağımlılıkları
│
├── worker/              # Background Job Worker (RQ)
│   ├── main.py          # Worker entry point
│   ├── jobs.py          # Job tanımları
│   ├── services/        # Alignment ve STT servisleri
│   ├── Dockerfile       # Worker container tanımı
│   └── requirements.txt # Worker bağımlılıkları
│
├── frontend/            # Next.js Frontend
│   ├── app/            # Next.js App Router sayfaları
│   │   ├── page.tsx    # Ana sayfa (upload)
│   │   ├── layout.tsx  # Root layout
│   │   ├── login/      # Login sayfası
│   │   ├── students/   # Öğrenci yönetimi
│   │   ├── texts/      # Metin yönetimi
│   │   ├── analyses/   # Analiz görüntüleme
│   │   ├── settings/   # Kullanıcı ve rol yönetimi
│   │   └── profile/    # Kullanıcı profili
│   ├── components/     # React bileşenleri
│   ├── lib/           # Utility fonksiyonlar ve API client
│   ├── middleware.ts  # Next.js middleware (auth check)
│   ├── Dockerfile     # Frontend container tanımı
│   └── package.json   # NPM bağımlılıkları
│
├── docker-compose.yml  # Servis orkestrasyon
├── Makefile           # Hızlı komutlar
├── start-mobile.sh    # Mobil erişim script
└── logs/              # Uygulama logları
```

---

## 🛠️ Teknoloji Stack'i

### Backend (FastAPI)

| Bileşen | Teknoloji | Versiyon |
|---------|-----------|----------|
| Framework | FastAPI | 0.104.1 |
| ASGI Server | Uvicorn | 0.24.0 |
| Database ODM | Beanie (MongoDB) | 1.25.0 |
| Veritabanı | MongoDB | 7.0 |
| Kuyruk Sistemi | Redis + RQ | 5.0.1 + 1.15.1 |
| Authentication | JWT (python-jose) | 3.3.0 |
| Password Hashing | Passlib (bcrypt) | 1.7.4 |
| Cloud Storage | Google Cloud Storage | 3.3.1 |
| Rate Limiting | SlowAPI | 0.1.9 |
| Logging | Loguru | 0.7.2 |
| Audio Processing | Pydub, Soundfile | 0.25.1, 0.12.1 |
| Python Versiyon | Python | 3.11 |

### Worker (Background Jobs)

| Bileşen | Teknoloji | Versiyon |
|---------|-----------|----------|
| Job Queue | RQ (Redis Queue) | 1.15.1 |
| Database | Motor (Async MongoDB) | 3.3.2 |
| STT Service | ElevenLabs Scribe | API v1 |
| Alignment | Custom Algorithm | - |

### Frontend (Next.js)

| Bileşen | Teknoloji | Versiyon |
|---------|-----------|----------|
| Framework | Next.js (App Router) | 14.2.32 |
| UI Library | React | 18.0.0 |
| Language | TypeScript | 5.0.0 |
| Styling | Tailwind CSS | 3.3.0 |
| HTTP Client | Axios | 1.6.0 |
| State Management | Zustand | 4.4.0 |
| Utilities | ClassNames | 2.3.0 |
| Node Versiyon | Node.js | 20+ |

### Infrastructure

| Servis | Teknoloji | Port |
|--------|-----------|------|
| API Backend | FastAPI | 8000 |
| Frontend | Next.js | 3000 |
| Database | MongoDB | 27017 |
| Cache/Queue | Redis | 6379 |
| Worker | RQ Worker | - |

---

## 🔧 Ana Dosyalar ve Entry Points

### Backend Entry Point
```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="DOKY - Okuma Analizi API",
    version="1.0.0",
    description="Ses dosyalarından okuma analizi API'si"
)

# Routers
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(students.router, prefix="/v1/students", tags=["students"])
app.include_router(texts.router, prefix="/v1/texts", tags=["texts"])
app.include_router(analyses.router, prefix="/v1/analyses", tags=["analyses"])
app.include_router(upload.router, prefix="/v1/upload", tags=["upload"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(roles.router, prefix="/v1/roles", tags=["roles"])
app.include_router(profile.router, prefix="/v1/profile", tags=["profile"])

# Startup: MongoDB ve Redis bağlantıları
# Rate limiting, CORS, logging middleware
```

### Worker Entry Point
```python
# worker/main.py
from rq import Worker, Queue, Connection
import redis

listen = ['default']
redis_url = 'redis://redis:6379'
conn = redis.from_url(redis_url)

with Connection(conn):
    worker = Worker(list(map(Queue, listen)))
    worker.work()
```

### Frontend Entry Point
```typescript
// frontend/app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  )
}

// frontend/middleware.ts
// JWT token kontrolü
// Public routes: /login
// Protected routes: *, /students, /texts, /analyses, /settings
```

---

## 🌍 Environment Değişkenleri

### Backend (.env / docker-compose.yml)

```bash
# Database
MONGO_URI=mongodb://mongodb:27017
MONGO_DB=okuma_analizi

# Cache & Queue
REDIS_URL=redis://redis:6379

# Google Cloud Storage
GCS_CREDENTIALS_PATH=./gcs-service-account.json
GCS_BUCKET=doky_ai_audio_storage

# ElevenLabs STT
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx
ELEVENLABS_MODEL=scribe_v1_experimental  # veya scribe_v1
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0              # 0.0-2.0 arası
ELEVENLABS_SEED=12456                   # Reproducibility
ELEVENLABS_REMOVE_FILLER_WORDS=false
ELEVENLABS_REMOVE_DISFLUENCIES=false

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=pretty
LOG_FILE=./logs/app.log

# Security (opsiyonel)
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=3
```

### Frontend (.env.local / docker-compose.yml)

```bash
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mobil erişim için (opsiyonel)
# HOST_IP ortam değişkeni ile dinamik olarak ayarlanır
NEXT_PUBLIC_API_URL=http://${HOST_IP}:8000
```

### Worker (.env)

```bash
# Backend ile aynı MongoDB ve Redis ayarları
MONGO_URI=mongodb://mongodb:27017
MONGO_DB=okuma_analizi
REDIS_URL=redis://redis:6379

# ElevenLabs ayarları
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxx
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
```

---

## 🚀 Çalıştırma Komutları

### Docker Compose ile Başlatma (Önerilen)

```bash
# Tüm servisleri başlat
docker-compose up -d

# veya Makefile ile
make start

# Mobil erişim için (IP otomatik algılama)
make start-mobile

# Logları takip et
docker-compose logs -f

# veya
make logs

# Sadece API logları
make logs-api

# Servisleri durdur
docker-compose down

# veya
make stop

# Servisleri yeniden başlat
make restart

# Worker'ı yeniden başlat
make restart-worker
```

### Manuel Başlatma (Development)

#### Backend
```bash
cd backend
pip install -r requirements.txt

# Environment değişkenlerini ayarla
export MONGO_URI=mongodb://localhost:27017
export REDIS_URL=redis://localhost:6379
export ELEVENLABS_API_KEY=sk_xxxxx

# Uvicorn ile başlat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Worker
```bash
cd worker
pip install -r requirements.txt

# RQ worker başlat
rq worker -u redis://localhost:6379
```

#### Frontend
```bash
cd frontend
npm install

# Development server
npm run dev

# Production build
npm run build
npm start
```

### Model ve Temperature Ayarları

```bash
# STT Model değiştir
make model-stable           # scribe_v1 (stabil)
make model-experimental     # scribe_v1_experimental (daha iyi)
make model-show            # Mevcut model

# Temperature ayarla
make temp-0.0              # En düşük yaratıcılık
make temp-0.5              # Orta seviye
make temp-1.0              # Yüksek yaratıcılık
make temp-custom VALUE=0.8 # Özel değer
make temp-show             # Mevcut temperature
```

---

## 📦 Bağımlılıklar

### Backend (requirements.txt)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic-settings==2.0.3
motor==3.3.2
pymongo==4.6.0
redis==5.0.1
rq==1.15.1
requests==2.32.5
numpy==1.24.3
soundfile==0.12.1
pydub==0.25.1
loguru==0.7.2
python-dotenv==1.0.0
orjson==3.9.10
slowapi==0.1.9
fastapi-cors==0.0.6
google-cloud-storage==3.3.1
beanie==1.25.0
pytz==2023.3
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
email-validator==2.1.0
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "classnames": "^2.3.0",
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@types/node": "^20.19.15",
    "@types/react": "^18.3.24",
    "@types/react-dom": "^18.3.7",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.0.0"
  }
}
```

---

## 🔌 Portlar

| Servis | Port | Açıklama |
|--------|------|----------|
| Frontend | 3000 | Next.js web arayüzü |
| Backend API | 8000 | FastAPI REST API |
| MongoDB | 27017 | NoSQL veritabanı |
| Redis | 6379 | Cache ve job queue |

### Erişim URL'leri

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **API Redoc:** http://localhost:8000/redoc

---

## 🐳 Docker Yapısı

### Servisler

#### 1. MongoDB (mongodb)
```yaml
image: mongo:7.0
ports: 27017:27017
environment:
  MONGO_INITDB_DATABASE: okuma_analizi
volumes:
  - mongodb_data:/data/db
```

#### 2. Redis (redis)
```yaml
image: redis:7.2-alpine
ports: 6379:6379
volumes:
  - redis_data:/data
```

#### 3. Backend API (api)
```yaml
build: backend/Dockerfile
ports: 8000:8000
depends_on: [mongodb, redis]
volumes:
  - ./backend:/app
  - ./logs:/app/logs
  - ./gcs-service-account.json:/app/gcs-service-account.json
```

#### 4. Worker (worker)
```yaml
build: worker/Dockerfile
depends_on: [mongodb, redis, api]
volumes:
  - ./worker:/app
  - ./logs:/app/logs
  - ./gcs-service-account.json:/app/gcs-service-account.json
```

#### 5. Frontend (frontend)
```yaml
build: frontend/Dockerfile
ports: 3000:3000
depends_on: [api]
volumes:
  - ./frontend:/app
environment:
  NEXT_PUBLIC_API_URL: http://localhost:8000
```

### Docker Compose Komutları

```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Execute command in container
docker-compose exec [service_name] [command]

# Clean volumes (dikkatli kullanın!)
docker-compose down -v
```

---

## 📊 API Endpoint'leri

### Authentication
- `POST /v1/auth/login` - Kullanıcı girişi
- `POST /v1/auth/logout` - Çıkış

### Students
- `GET /v1/students` - Öğrenci listesi
- `POST /v1/students` - Yeni öğrenci
- `GET /v1/students/{id}` - Öğrenci detay
- `PUT /v1/students/{id}` - Öğrenci güncelle
- `DELETE /v1/students/{id}` - Öğrenci sil/pasifleştir

### Texts
- `GET /v1/texts` - Metin listesi
- `POST /v1/texts` - Yeni metin
- `GET /v1/texts/{id}` - Metin detay
- `PUT /v1/texts/{id}` - Metin güncelle
- `DELETE /v1/texts/{id}` - Metin sil

### Analyses
- `GET /v1/analyses` - Analiz listesi
- `POST /v1/analyses/file` - Ses dosyası ile analiz başlat
- `GET /v1/analyses/{id}` - Analiz detay
- `GET /v1/analyses/{id}/export` - Analiz sonucu (JSON)
- `DELETE /v1/analyses/{id}` - Analiz sil

### Upload
- `POST /v1/upload/audio` - Ses dosyası yükle (GCS)
- `GET /v1/upload/audio/{file_id}/url` - Geçici erişim URL'i

### Users & Roles (RBAC)
- `GET /v1/users` - Kullanıcı listesi
- `POST /v1/users` - Yeni kullanıcı
- `PUT /v1/users/{id}` - Kullanıcı güncelle
- `POST /v1/users/{id}/reset-password` - Şifre sıfırla
- `GET /v1/roles` - Rol listesi
- `POST /v1/roles` - Yeni rol
- `PUT /v1/roles/{id}` - Rol güncelle

### Profile
- `GET /v1/profile/me` - Kendi profili görüntüle
- `PUT /v1/profile/me` - Profil güncelle
- `POST /v1/profile/me/change-password` - Şifre değiştir

---

## 🔐 Güvenlik Özellikleri

### Authentication & Authorization
- **JWT Token Authentication** - 3 saat otomatik logout (inactivity based)
- **Role-Based Access Control (RBAC)** - Granüler izin sistemi
- **BCrypt Password Hashing** - Güvenli şifre saklama
- **Permission System:**
  - `read`, `view`, `create`, `update`, `delete` yetkileri
  - Özel yetkiler: `analysis:read_all`, `student_management`, vb.

### API Security
- **Rate Limiting** - SlowAPI ile istek sınırlama
- **CORS Configuration** - Cross-origin politikaları
- **Request ID Tracking** - Her istek için unique ID
- **Input Validation** - Pydantic ile veri doğrulama

### Data Security
- **Google Cloud Storage** - Ses dosyaları için güvenli depolama
- **Signed URLs** - 1 saatlik geçerli güvenli erişim
- **MongoDB** - NoSQL veritabanı güvenliği
- **Redis** - Kuyruk ve cache güvenliği

---

## 📝 Yönetim Komutları

### Admin Kullanıcı Oluşturma

```bash
# Admin oluştur
docker-compose exec api python /app/scripts/create_admin.py \
  admin@doky.com admin admin123

# Parametreler: <email> <username> <password>
```

### Database İşlemleri

```bash
# MongoDB shell
docker-compose exec mongodb mongosh okuma_analizi

# Veritabanı backup
docker-compose exec mongodb mongodump --out /backup

# Redis CLI
docker-compose exec redis redis-cli
```

### Log İşlemleri

```bash
# Tüm loglar
make logs

# API logları
make logs-api

# Worker logları
make logs-worker

# Frontend logları
make logs-frontend

# Log dosyaları
tail -f logs/app.log
```

### Test Komutları

```bash
# Sistem testleri
make test

# Alignment testleri
make test-alignment

# Hızlı test
make test-quick
```

---

## 🎨 Frontend Sayfalar

### Public Pages
- `/login` - Giriş sayfası

### Protected Pages
- `/` - Ana sayfa (ses dosyası upload)
- `/students` - Öğrenci listesi
- `/students/[id]` - Öğrenci detay
- `/students/[id]/analysis/[analysisId]` - Öğrenci analiz detay
- `/texts` - Metin listesi
- `/analyses` - Tüm analizler (admin/manager)
- `/analyses/[id]` - Analiz detay
- `/settings` - Kullanıcı ve rol yönetimi
- `/profile` - Kullanıcı profili

### Responsive Design
Tüm sayfalar responsive tasarıma sahip:
- **Mobile:** < 640px (sm)
- **Tablet:** 640px - 1024px (md)
- **Desktop:** > 1024px (lg)

---

## 🔄 İş Akışı (Workflow)

### Analiz Süreci

```
1. Ses Dosyası Upload (Frontend)
   ↓
2. GCS'e Yükleme (Backend API)
   ↓
3. Analysis Job Oluşturma (Backend API)
   ↓
4. Redis Queue'ya Ekleme (Backend API)
   ↓
5. Worker Job'ı Alır (RQ Worker)
   ↓
6. ElevenLabs STT API (Worker)
   ↓
7. Alignment Algoritması (Worker)
   ↓
8. Sonuçları MongoDB'ye Kaydet (Worker)
   ↓
9. Frontend'de Göster (Polling/Real-time)
```

### Authentication Flow

```
1. Login (Email + Password)
   ↓
2. JWT Token Oluşturma (3 saat geçerli)
   ↓
3. localStorage'a Token Kaydet
   ↓
4. Her API İsteğinde Bearer Token
   ↓
5. Token Doğrulama + Permission Check
   ↓
6. İnactivity Tracking (3 saat)
   ↓
7. Auto Logout
```

---

## 📈 Monitoring & Logging

### Log Sistemi
- **Loguru** ile yapılandırılmış logging
- **Dosya Rotasyonu:** 5 MB, 7 gün retention
- **Zip Kompresyon:** Eski loglar otomatik sıkıştırılır
- **Log Seviyeleri:** DEBUG, INFO, WARNING, ERROR, CRITICAL

### Log Formatı
```
2025-10-08 14:30:45.123 | INFO | app.routers.analyses:create:45 | Analysis created: 68e656ad5ba6c3474d99ee2f
```

### Request Tracking
- Unique Request ID
- Request/Response timing
- Client IP tracking
- Slow query detection (>250ms)

---

## 🧪 Testing

### Test Türleri
- Unit Tests
- Integration Tests
- API Tests
- Alignment Algorithm Tests
- UI Integration Tests

### Test Komutları
```bash
# Tüm testler
pytest tests/

# Specific test
pytest tests/test_alignment_improvements.py

# Coverage raporu
pytest --cov=app tests/
```

---

## 📱 Mobil Erişim

### Yerel Ağdan Erişim

```bash
# IP'yi otomatik algılayıp başlat
./start-mobile.sh

# veya
make start-mobile

# Manuel IP ayarla
export HOST_IP=$(ipconfig getifaddr en0)
docker-compose down
docker-compose up -d
```

Mobil cihazdan erişim: `http://<YOUR_IP>:3000`

---

## 🛠️ Geliştirme Notları

### Hot Reload
- **Backend:** Uvicorn `--reload` flag ile otomatik reload
- **Frontend:** Next.js development server otomatik reload
- **Worker:** Manuel restart gerekli

### Database Migrations
Beanie ODM kullanıldığından schema migration'a gerek yok. Model değişiklikleri otomatik yansır.

### Environment Dosyaları
```
backend/env.example     → backend/.env
frontend/env.example    → frontend/.env.local
worker/env.example      → worker/.env
env.example            → .env (root)
```

---

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Port kullanımını kontrol et
lsof -i :3000
lsof -i :8000

# Process'i sonlandır
kill -9 <PID>
```

### MongoDB Connection Error
```bash
# MongoDB durumunu kontrol et
docker-compose ps mongodb

# Logları incele
docker-compose logs mongodb

# Restart
docker-compose restart mongodb
```

### Worker Not Processing Jobs
```bash
# Worker loglarını kontrol et
docker-compose logs worker

# Redis bağlantısını test et
docker-compose exec redis redis-cli ping

# Worker restart
make restart-worker
```

---

## 📞 Önemli Linkler

- **API Documentation:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000
- **MongoDB:** mongodb://localhost:27017
- **Redis:** redis://localhost:6379

---

## 📄 Lisans ve İletişim

**Proje:** DOKY - Okuma Analizi Sistemi  
**Geliştirici:** [Proje Ekibi]  
**Son Güncelleme:** Ekim 2025

---

## 🎯 Sonraki Adımlar

- [ ] Production deployment (Kubernetes/Cloud Run)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Performance monitoring (Prometheus/Grafana)
- [ ] Automated backups
- [ ] Load testing
- [ ] Documentation website
- [ ] API versioning
- [ ] Webhook notifications
- [ ] Multi-language support
- [ ] Mobile app (React Native)

---

**Bu rapor proje yapısını, kullanılan teknolojileri, çalıştırma komutlarını ve geliştirme süreçlerini kapsamlı olarak açıklamaktadır.**

