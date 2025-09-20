# 🚀 Okuma Analizi - Hızlı Başlangıç

Bu rehber, Okuma Analizi sistemini hızlıca başlatmanız için gerekli adımları içerir.

## 📋 Gereksinimler

- Docker ve Docker Compose
- Git
- Terminal/Command Line

## 🚀 Hızlı Başlatma

### 1. Sistemi Başlatın
```bash
./start.sh
```

Bu script:
- Docker servislerini build eder
- Tüm servisleri başlatır
- Sistem testlerini çalıştırır
- Erişim URL'lerini gösterir

### 2. Manuel Başlatma (İsteğe bağlı)
```bash
# Servisleri başlat
docker-compose up -d --build

# Test et
./test-system.sh
```

## 🌐 Erişim URL'leri

| Servis | URL | Açıklama |
|--------|-----|----------|
| **Frontend** | http://localhost:3000 | Ana uygulama |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | Sistem durumu |

## 🔧 Kullanışlı Komutlar

### Docker Yönetimi
```bash
# Servisleri başlat
docker-compose up -d

# Servisleri durdur
docker-compose down

# Servisleri yeniden başlat
docker-compose restart

# Logları görüntüle
docker-compose logs -f

# Belirli bir servisin loglarını görüntüle
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Sistem Testi
```bash
# Tüm testleri çalıştır
./test-system.sh

# Manuel test
curl http://localhost:8000/health
curl http://localhost:8000/v1/sessions/
```

### Veritabanı Yönetimi
```bash
# MongoDB'ye bağlan
docker-compose exec mongodb mongosh okuma_analizi

# Veritabanını temizle
docker-compose exec mongodb mongosh --eval "db.dropDatabase()" okuma_analizi
```

## 📁 Proje Yapısı

```
okuma-analizi/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── worker/           # RQ worker
├── scripts/          # Utility scripts
├── tests/            # Test suite
├── docker-compose.yml
├── start.sh          # Hızlı başlatma
├── test-system.sh    # Sistem testi
└── env.example       # Environment örneği
```

## 🔑 Environment Konfigürasyonu

### 1. Environment Dosyası Oluşturun
```bash
# Ana dizinde
cp env.example .env

# Backend için
cp backend/env.example backend/.env

# Frontend için
cp frontend/env.example frontend/.env.local

# Worker için
cp worker/env.example worker/.env
```

### 2. Gerekli Değişkenleri Ayarlayın
```bash
# .env dosyasını düzenleyin
nano .env
```

**Önemli değişkenler:**
- `ELEVENLABS_API_KEY`: STT için gerekli
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket
- `SECRET_KEY`: Güvenlik için

## 🧪 Test Etme

### Otomatik Test
```bash
./test-system.sh
```

### Manuel Test
```bash
# API Health Check
curl http://localhost:8000/health

# Sessions API
curl http://localhost:8000/v1/sessions/

# Frontend
curl http://localhost:3000
```

## 🐛 Sorun Giderme

### Servisler Başlamıyor
```bash
# Logları kontrol et
docker-compose logs

# Servisleri yeniden başlat
docker-compose down
docker-compose up -d --build
```

### Database Bağlantı Hatası
```bash
# MongoDB'yi yeniden başlat
docker-compose restart mongodb

# Database'i temizle
docker-compose exec mongodb mongosh --eval "db.dropDatabase()" okuma_analizi
```

### Port Çakışması
```bash
# Kullanılan portları kontrol et
lsof -i :3000
lsof -i :8000
lsof -i :27017
lsof -i :6379
```

## 📊 Sistem Durumu

Sistem çalışırken durumu kontrol etmek için:

```bash
# Docker servisleri
docker-compose ps

# Sistem testi
./test-system.sh

# API health
curl http://localhost:8000/health
```

## 🎯 Sonraki Adımlar

1. **Environment dosyalarını yapılandırın**
2. **ElevenLabs API key'i ekleyin** (STT için)
3. **Google Cloud Storage ayarlarını yapın**
4. **Test verisi yükleyin**
5. **Sistem testlerini çalıştırın**

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin: `docker-compose logs`
2. Sistem testini çalıştırın: `./test-system.sh`
3. Servisleri yeniden başlatın: `docker-compose restart`

---
*Son güncelleme: 17 Eylül 2025*

