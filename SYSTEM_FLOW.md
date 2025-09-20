# Sistem Akış Diyagramı - Ses Dosyası Analizi

## 🔄 Detaylı Sistem Akışı

### 1. KULLANICI ETKİLEŞİMİ
```
[Kullanıcı] → [Frontend UI] → [Ses Dosyası Seçimi] → [Hedef Metin Seçimi] → [Analiz Başlat]
```

### 2. FRONTEND → BACKEND API
```
[Frontend] 
    ↓ POST /v1/upload/
[Backend API]
    ↓ Dosya Validasyonu
    ↓ Text ID Kontrolü
    ↓ GCS Upload
    ↓ MongoDB Kayıt
    ↓ Redis Queue
```

### 3. BACKEND API İŞLEMLERİ
```
[Backend API]
    ├── Dosya Validasyonu
    │   ├── Content-Type kontrolü
    │   └── Dosya boyutu kontrolü
    ├── Text ID Validasyonu
    │   └── MongoDB'den text bulma
    ├── GCS Upload
    │   ├── Unique dosya adı
    │   └── GCS URL alma
    ├── Database Kayıtları
    │   ├── AudioFileDoc oluşturma
    │   └── AnalysisDoc oluşturma
    └── Queue Job
        └── Redis'e job ekleme
```

### 4. WORKER İŞLEMLERİ
```
[Worker]
    ├── Job Alımı (Redis Queue)
    ├── Ses Dosyası İndirme (GCS)
    ├── ElevenLabs Transkripsiyon
    │   ├── API çağrısı
    │   ├── Word-level timestamps
    │   └── Language detection
    ├── Word Processing
    │   ├── Response işleme
    │   ├── Word combination logic
    │   └── Processed words
    ├── Text Alignment
    │   ├── Reference tokenization
    │   ├── Hypothesis tokenization
    │   └── Levenshtein alignment
    ├── Metrics Calculation
    │   ├── WER hesaplama
    │   ├── WPM hesaplama
    │   └── Accuracy hesaplama
    ├── Pause Detection
    │   ├── ElevenLabs spacing data
    │   ├── 500ms+ duraksama tespiti
    │   └── Pause events
    └── Database Kayıtları
        ├── Word events
        ├── Pause events
        └── Analysis güncelleme
```

### 5. VERİ AKIŞI
```
[Ses Dosyası] → [GCS] → [Worker] → [ElevenLabs] → [Transkripsiyon]
                                                      ↓
[Reference Text] → [MongoDB] → [Worker] → [Alignment] → [Metrics]
                                                      ↓
[Spacing Data] → [Worker] → [Pause Detection] → [Pause Events]
                                                      ↓
[Sonuçlar] → [MongoDB] → [Frontend] → [Kullanıcı]
```

## 🔗 Bileşenler Arası Bağlantılar

### Frontend ↔ Backend API
- **HTTP REST API**
- **Port:** 3000 → 8000
- **Protokol:** HTTP/HTTPS

### Backend API ↔ MongoDB
- **Beanie ODM**
- **Port:** 8000 → 27017
- **Protokol:** MongoDB Wire Protocol

### Backend API ↔ Redis
- **RQ (Redis Queue)**
- **Port:** 8000 → 6379
- **Protokol:** Redis Protocol

### Worker ↔ Redis
- **RQ Worker**
- **Port:** Worker → 6379
- **Protokol:** Redis Protocol

### Worker ↔ MongoDB
- **Beanie ODM**
- **Port:** Worker → 27017
- **Protokol:** MongoDB Wire Protocol

### Worker ↔ GCS
- **Google Cloud Storage Client**
- **Port:** Worker → 443
- **Protokol:** HTTPS

### Worker ↔ ElevenLabs
- **HTTP REST API**
- **Port:** Worker → 443
- **Protokol:** HTTPS

## 📊 Veri Akışı Detayları

### 1. Ses Dosyası Yükleme
```
[Kullanıcı] → [Frontend] → [Backend] → [GCS] → [URL]
```

### 2. Analiz Job'u
```
[Backend] → [Redis Queue] → [Worker] → [Processing]
```

### 3. Transkripsiyon
```
[Worker] → [ElevenLabs API] → [Word Data] → [Processing]
```

### 4. Sonuç Kaydetme
```
[Worker] → [MongoDB] → [Frontend] → [Kullanıcı]
```

## 🎯 Kritik Noktalar

### 1. Error Handling
- Her adımda try-catch
- Graceful degradation
- User-friendly error messages

### 2. Performance
- Async processing
- Queue-based architecture
- Bulk database operations

### 3. Scalability
- Horizontal scaling (multiple workers)
- Database indexing
- Caching strategies

### 4. Security
- API key management
- File validation
- Input sanitization

Bu akış diyagramı, sistemin tüm bileşenleri arasındaki etkileşimleri ve veri akışını detaylı olarak göstermektedir.

