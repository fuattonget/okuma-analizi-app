# Okuma Analizi

Türkçe dilinde okuma analizi yapan uygulama için monorepo. Backend API, worker servisi ve frontend içerir.

## 🚀 Hızlı Başlangıç

### Otomatik Kurulum
```bash
# Sistemi başlat ve test et
./start.sh
```

### Manuel Kurulum
```bash
# 1. Environment dosyalarını ayarla
make setup-env

# 2. Servisleri başlat
make start

# 3. Sistemi test et
make test
```

### Erişim URL'leri
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

4. **Uygulamaya eriş:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Dokümantasyonu: http://localhost:8000/docs

## Servisler

- **API** (`./backend`): Port 8000'de FastAPI backend servisi
- **Worker** (`./worker`): Arka plan görev işleme servisi
- **Frontend** (`./frontend`): Port 3000'de Next.js frontend
- **MongoDB**: Port 27017'de veritabanı servisi
- **Redis**: Port 6379'da cache ve mesaj kuyruğu
- **Google Cloud Storage**: Ses dosyaları için bulut depolama

## Kullanılabilir Komutlar

- `make up` - Tüm servisleri başlat
- `make down` - Tüm servisleri durdur
- `make logs` - Tüm servislerin loglarını görüntüle
- `make api` - API container shell'ine eriş
- `make fe` - Frontend container shell'ine eriş
- `make wk` - Worker container shell'ine eriş

## Özellikler

### Türkçe Dil Desteği
- **ElevenLabs STT**: Yüksek kaliteli Türkçe konuşma tanıma
- **Tokenizasyon**: Türkçe karakter desteği (ç, ğ, ı, ö, ş, ü)
- **Hata Analizi**: Türkçe okuma hatalarının detaylı analizi
- **Hece Analizi**: Türkçe hece yapısına uygun hata sınıflandırması

### Analiz Metrikleri
- **WER (Word Error Rate)**: Kelime hata oranı
- **Accuracy**: Doğruluk yüzdesi
- **WPM (Words Per Minute)**: Dakikada kelime sayısı
- **Duraksama Analizi**: 800ms üzeri duraksamaların tespiti

### Hata Sınıflandırması
- **Eksik Kelimeler**: Kırmızı alt çizgi ile işaretlenir
- **Fazla Kelimeler**: Mavi italik `[ek: 'kelime']` formatında
- **Farklı Kelimeler**: Sarı arka plan ile vurgulanır
- **Alt Kırılımlar**: harf_ek, harf_cik, degistirme, hece_ek, hece_cik

## Geliştirme

Her servisin kendi dizini ve özel kurulum talimatları vardır:

- `backend/` - Python FastAPI uygulaması
- `worker/` - Python worker servisi
- `frontend/` - Next.js React uygulaması
- `infra/` - Altyapı ve deployment konfigürasyonları

## Dosya Yapısı

```
okuma-analizi/
├── backend/          # FastAPI backend
├── worker/           # Ses analizi worker'ı
├── frontend/         # Next.js frontend
├── infra/           # Altyapı konfigürasyonları
├── scripts/         # Geliştirme scriptleri
├── gcs-service-account.json  # GCS kimlik doğrulama
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Test Etme

Detaylı test rehberi için `scripts/test-audio.md` dosyasına bakın.

### Hızlı Test
1. Sistemi başlat
2. Frontend'e git (http://localhost:3000)
3. Örnek metin seç
4. Ses dosyası yükle
5. Analiz sonuçlarını incele

## Teknoloji Stack

- **Backend**: FastAPI, MongoDB, Redis, ElevenLabs STT
- **Worker**: Python, RQ, ElevenLabs API
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Storage**: Google Cloud Storage (GCS)
- **Infrastructure**: Docker, Docker Compose

## GCS Kurulumu

Ses dosyaları Google Cloud Storage'da saklanır. Kurulum için:

1. **GCS Bucket Oluştur:**
   ```bash
   gsutil mb gs://doky_ai_audio_storage
   ```

2. **Service Account Oluştur:**
   - Google Cloud Console'da service account oluştur
   - Storage Admin rolü ver
   - JSON key dosyasını indir ve `gcs-service-account.json` olarak kaydet

3. **Environment Variables:**
   ```bash
   STORAGE_BACKEND=gcs
   GCS_BUCKET=doky_ai_audio_storage
   GCS_CREDENTIALS_PATH=./gcs-service-account.json
   GCS_PUBLIC_BASE=https://storage.googleapis.com
   ```
