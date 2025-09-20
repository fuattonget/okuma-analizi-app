# STT/Alignment Word Merging Fix Report

## 🎯 **HEDEF**
ElevenLabs ham JSON'undaki `words` dizisini doğrudan kullanarak, kelime birleştirme sorununu tamamen çözmek.

## 🔍 **SORUN ANALİZİ**
- **Önceki Durum**: ElevenLabs'den gelen kelimeler `process_words()` fonksiyonu ile işleniyordu
- **Sorun**: Kelimeler birleştiriliyordu ("Atatürk" + "bir" → "Atatürkbir")
- **Etki**: Word events'lerde yanlış `hyp_token` değerleri, yanlış alignment

## ✅ **DÜZELTİLEN DOSYALAR**

### 1. `worker/services/elevenlabs_stt.py`
**Değişiklikler:**
- `process_words()` → `extract_raw_words()` olarak yeniden adlandırıldı
- Kelime birleştirme mantığı tamamen kaldırıldı
- Sadece `type="word"` olan tokenlar alınıyor, `type="spacing"` olanlar ignore ediliyor
- Direct passthrough: `{"word": w["text"], "start": float(w["start"]), "end": float(w["end"]), "confidence": float(w.get("logprob", 0.0))}`

**Kaldırılan Fonksiyonlar:**
- `_should_combine_words()`
- `_is_turkish_word_pattern()`
- `_is_common_turkish_word()`
- Tüm kelime birleştirme mantığı

### 2. `worker/jobs.py`
**Değişiklikler:**
- `stt_client.process_words()` → `stt_client.extract_raw_words()` kullanımı
- Raw words logging eklendi
- STT result kaydında ham words kullanılıyor

### 3. `worker/services/alignment.py`
**Durum:** ✅ Temiz, değişiklik gerekmedi
- Sadece alignment yapıyor, kelime birleştirme yapmıyor

## 🗂️ **YENİ DOSYALAR**

### 1. `scripts/recompute_analysis.py`
**Amaç:** Mevcut analizleri yeniden hesaplamak
**Kullanım:**
```bash
# Belirli analizi yeniden hesapla
python scripts/recompute_analysis.py --analysis-id <analysis_id>

# Belirli session'ı yeniden hesapla  
python scripts/recompute_analysis.py --session-id <session_id>

# Tüm done analizleri yeniden hesapla
python scripts/recompute_analysis.py --all-done
```

### 2. `tests/test_stt_passthrough.py`
**Amaç:** STT word passthrough'u test etmek
**Test Senaryoları:**
- Raw words passthrough
- Punctuation preservation
- Empty words ignored
- Spacing completely ignored
- No word merging

### 3. `tests/test_alignment_no_merge.py`
**Amaç:** Alignment'da kelime birleştirme olmadığını test etmek
**Test Senaryoları:**
- Alignment preserves individual words
- Alignment with missing words
- Alignment with extra words
- Word events no merging
- No combined words in events

## 🗄️ **ARŞİVLENEN DOSYALAR**

### `scripts/_archive/fix_word_events.py`
**Sebep:** Eski yaklaşım, yeni `recompute_analysis.py` ile değiştirildi
**Durum:** Arşivlendi, silinmedi

## 🧪 **TEST SONUÇLARI**

### Unit Tests
```bash
# STT Passthrough Test
python -m pytest tests/test_stt_passthrough.py -v

# Alignment No Merge Test  
python -m pytest tests/test_alignment_no_merge.py -v
```

### Integration Test
```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v
```

## 📊 **BEKLENEN SONUÇLAR**

### Önceki Durum (Yanlış):
```json
{
  "ref_token": "bu",
  "hyp_token": "bugüzelbir",
  "type": "substitution"
}
```

### Yeni Durum (Doğru):
```json
{
  "ref_token": "bu",
  "hyp_token": "bu", 
  "type": "correct",
  "timing": { "start_ms": 1480, "end_ms": 1600 }
},
{
  "ref_token": "güzel",
  "hyp_token": "güzel",
  "type": "correct", 
  "timing": { "start_ms": 1679, "end_ms": 2079 }
},
{
  "ref_token": "bir",
  "hyp_token": "bir",
  "type": "correct",
  "timing": { "start_ms": 2100, "end_ms": 2300 }
}
```

## 🚀 **CANLI DÜZELTME**

### Mevcut Analizleri Düzelt:
```bash
# Tüm yanlış word_events'leri düzelt
python scripts/recompute_analysis.py --all-done

# Belirli session için düzelt
python scripts/recompute_analysis.py --session-id 68cd3eb7880ccd3f605fd202
```

### Yeni Analiz Test:
```bash
# Worker'ı restart et
docker-compose restart worker

# Logları kontrol et
docker-compose logs -f worker | grep "Raw words"
```

## 🔧 **TEKNİK DETAYLAR**

### ElevenLabs Response Schema:
```json
{
  "text": "Bu güzel bir metin",
  "words": [
    {"text": "Bu", "start": 1.0, "end": 1.1, "type": "word", "logprob": -0.1},
    {"text": " ", "start": 1.1, "end": 1.2, "type": "spacing", "logprob": -0.05},
    {"text": "güzel", "start": 1.2, "end": 1.5, "type": "word", "logprob": -0.2},
    {"text": " ", "start": 1.5, "end": 1.6, "type": "spacing", "logprob": -0.05},
    {"text": "bir", "start": 1.6, "end": 1.7, "type": "word", "logprob": -0.3},
    {"text": " ", "start": 1.7, "end": 1.8, "type": "spacing", "logprob": -0.05},
    {"text": "metin", "start": 1.8, "end": 2.0, "type": "word", "logprob": -0.15}
  ]
}
```

### Raw Words Output:
```json
[
  {"word": "Bu", "start": 1.0, "end": 1.1, "confidence": -0.1},
  {"word": "güzel", "start": 1.2, "end": 1.5, "confidence": -0.2},
  {"word": "bir", "start": 1.6, "end": 1.7, "confidence": -0.3},
  {"word": "metin", "start": 1.8, "end": 2.0, "confidence": -0.15}
]
```

## ✅ **DOĞRULAMA**

### Veritabanı Kontrol:
```bash
# STT results kontrol
docker-compose exec mongodb mongosh okuma_analizi --eval "
db.stt_results.find({}, {words: 1}).limit(1).pretty()
"

# Word events kontrol
docker-compose exec mongodb mongosh okuma_analizi --eval "
db.word_events.find({}, {hyp_token: 1, ref_token: 1}).limit(10).pretty()
"
```

### Beklenen Sonuçlar:
- ✅ `stt_results.words` array'inde ayrı kelimeler
- ✅ `word_events.hyp_token` ayrı kelimeler (artık "bugüzelbir" yok)
- ✅ Analysis summary doğru metrikleri üretiyor
- ✅ Timing bilgileri doğru

## 🎉 **SONUÇ**

Kelime birleştirme sorunu **tamamen çözüldü**:
- ElevenLabs ham words doğrudan kullanılıyor
- Spacing tokenlar ignore ediliyor
- Kelime birleştirme mantığı kaldırıldı
- Test coverage eklendi
- Mevcut analizler düzeltilebilir

**Pipeline artık tamamen ham words üzerinden çalışıyor!**
