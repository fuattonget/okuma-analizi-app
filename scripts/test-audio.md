# Test Audio Guide

## Test Senaryosu

Bu rehber, okuma analizi sisteminin doğru çalıştığını test etmek için örnek bir kullanım senaryosu sunar.

## Test Metni

**Hedef Metin:** "Bu güzel bir gün. Güneş parlıyor ve kuşlar şarkı söylüyor. Çocuklar parkta oyun oynuyor."

Bu metin sistemde örnek metin olarak mevcuttur (seed_texts.py ile yüklenir).

## Test Adımları

### 1. Sistemi Başlat
```bash
# Servisleri başlat
docker compose up -d --build

# Örnek metinleri yükle
docker compose exec api python -m scripts.seed_texts
```

### 2. Frontend'e Eriş
- http://localhost:3000 adresine git
- Upload formunu gör

### 3. Test Dosyasını Hazırla
Aşağıdaki metni okuyarak ses kaydı yap:

**Okuma Talimatları:**
- Metni doğal hızda oku
- Bazı kelimeleri atla veya yanlış oku (test için)
- Kelimeler arasında 1-2 saniye duraksama yap
- Bazı kelimeleri ekle (metinde olmayan)

**Örnek Okuma Senaryosu:**
```
"Bu güzel bir gün. [duraksama 1.5s] Güneş [duraksama 1s] parlıyor ve kuşlar [duraksama 2s] şarkı söylüyor. [duraksama 1s] Çocuklar parkta oyun oynuyor."
```

### 4. Upload İşlemi
1. **Ses Dosyası:** Kaydettiğin ses dosyasını sürükle/bırak
2. **Metin Seçimi:** "Güzel Bir Gün" örneğini seç
3. **Analiz Et:** Butona tıkla

### 5. Sonuçları İncele

#### Beklenen Analiz Sonuçları

**Ana Metrikler:**
- WER: 0.000-0.500 arası (okuma kalitesine göre)
- Accuracy: %50-100 arası
- WPM: 60-120 arası (normal okuma hızı)
- Duraksama: 2-5 arası (800ms üzeri duraksamalar)

#### Detaylı Analiz

**Kelime Seviyesi Analiz:**
- **Doğru Kelimeler:** Normal görünüm
- **Eksik Kelimeler:** Kırmızı alt çizgi
- **Farklı Kelimeler:** Sarı arka plan
- **Fazla Kelimeler:** Mavi italik `[ek: 'kelime']` formatında

**Duraksama Analizi:**
- Kelimeler arasında ⏸️ işareti
- Hover ile süre bilgisi (örn: "Duraksama 1420 ms")
- 800ms üzeri duraksamalar sayılır

**Alt Kırılımlar:**
- **harf_ek:** Harf ekleme hatası
- **harf_cik:** Harf çıkarma hatası  
- **degistirme:** Harf değiştirme hatası
- **hece_ek:** Hece ekleme hatası
- **hece_cik:** Hece çıkarma hatası

## Test Senaryoları

### Senaryo 1: Mükemmel Okuma
- Metni kelimesi kelimesine oku
- Hızlı ve akıcı oku
- **Beklenen:** WER < 0.1, Accuracy > %90

### Senaryo 2: Hatalı Okuma
- Bazı kelimeleri atla: "güzel" → atla
- Yanlış oku: "parlıyor" → "parluyor"
- Kelime ekle: "çok güzel bir gün"
- **Beklenen:** WER > 0.2, çeşitli hata türleri

### Senaryo 3: Yavaş Okuma
- Her kelime arasında 1-2 saniye duraksama
- Yavaş ve dikkatli oku
- **Beklenen:** Yüksek duraksama sayısı, düşük WPM

### Senaryo 4: Hızlı Okuma
- Çok hızlı oku
- Kelimeleri birleştir
- **Beklenen:** Yüksek WPM, düşük duraksama

## Sorun Giderme

### Analiz Başlamıyor
- Docker servislerinin çalıştığını kontrol et: `docker compose ps`
- Redis bağlantısını kontrol et: `docker compose logs redis`
- Worker loglarını kontrol et: `docker compose logs worker`

### Ses Dosyası Yüklenmiyor
- Dosya formatını kontrol et (MP3, WAV, M4A)
- Dosya boyutunu kontrol et (< 50MB)
- Rate limit kontrolü (5 upload/dakika)

### Analiz Tamamlanmıyor
- Worker loglarını kontrol et: `docker compose logs worker`
- MongoDB bağlantısını kontrol et: `docker compose logs mongo`
- Whisper model yükleme hatalarını kontrol et

## Log İnceleme

### Backend Logları
```bash
docker compose logs api
```

### Worker Logları
```bash
docker compose logs worker
```

### Tüm Servisler
```bash
docker compose logs -f
```

## Başarı Kriterleri

✅ **Sistem Testi Başarılı:**
- Ses dosyası başarıyla yüklenir
- Analiz 2-5 dakika içinde tamamlanır
- Sonuçlar doğru şekilde görüntülenir
- Hata türleri doğru kategorize edilir
- Duraksamalar doğru tespit edilir

✅ **Performans Testi Başarılı:**
- WER hesaplaması mantıklı aralıkta
- Accuracy yüzdesi doğru hesaplanır
- WPM değeri okuma hızını yansıtır
- Duraksama sayısı gerçekçi

Bu test senaryosu ile sistemin tüm özelliklerini kapsamlı bir şekilde test edebilirsiniz.


