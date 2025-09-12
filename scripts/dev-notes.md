# Geliştirme Kurulumu

## Hızlı Başlangıç

1. **Ortam Değişkenlerini Ayarla**
   ```bash
   cp .env.example .env
   ```

2. **Servisleri Başlat**
   ```bash
   is yükl
   ```

3. **Örnek Verileri Yükle**
   ```bash
   docker compose exec api python -m scripts.seed_texts
   ```

4. **Uygulamalara Eriş**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Dokümantasyonu: http://localhost:8000/docs

## Geliştirme Komutları

- `make up` - Tüm servisleri başlat
- `make down` - Tüm servisleri durdur
- `make logs` - Tüm servislerin loglarını görüntüle
- `make api` - API container shell'ine eriş
- `make fe` - Frontend container shell'ine eriş
- `make wk` - Worker container shell'ine eriş

## Servisler

- **API** (Port 8000): MongoDB ile FastAPI backend
- **Worker**: Redis kuyruğu ile ses analizi işleme
- **Frontend** (Port 3000): Next.js React uygulaması
- **MongoDB** (Port 27017): Veritabanı
- **Redis** (Port 6379): Mesaj kuyruğu

## Dosya Yapısı

```
okuma-analizi/
├── backend/          # FastAPI backend
├── worker/           # Ses analizi worker'ı
├── frontend/         # Next.js frontend
├── infra/           # Altyapı konfigürasyonları
├── scripts/         # Geliştirme scriptleri
├── media/           # Yüklenen ses dosyaları
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Türkçe Dil Desteği

Sistem Türkçe dilinde çalışacak şekilde optimize edilmiştir:

- **Whisper Modeli**: Türkçe konuşma tanıma için yapılandırılmış
- **Tokenizasyon**: Türkçe karakterler (ç, ğ, ı, ö, ş, ü) desteklenir
- **Hata Analizi**: Türkçe okuma hatalarının detaylı sınıflandırması
- **Hece Analizi**: Türkçe hece yapısına uygun hata türleri
