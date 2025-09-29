# Alignment Test Suite

Bu dizin, alignment algoritmalarının test edilmesi için kapsamlı test dosyalarını içerir.

## 📁 Test Dosyaları

### 1. **test_alignment_criteria_compliance.py**
Ana kriterlere uygunluk testleri:
- ✅ CORRECT tespiti (normalize eşleşme, noktalama farkı)
- ❌ SUBSTITUTION tespiti (alt türler dahil)
- ➕ EXTRA tespiti
- ➖ MISSING tespiti  
- 🔁 REPETITION tespiti

### 2. **test_normalization_functions.py**
Normalizasyon fonksiyonları testleri:
- `_norm_token()` fonksiyonu
- `classify_replace()` fonksiyonu
- `normalize_sub_type()` fonksiyonu
- `char_edit_stats()` fonksiyonu

### 3. **test_repetition_detection.py**
Repetition tespit algoritmaları testleri:
- "--" pattern tespiti
- Arka arkaya aynı token tespiti
- Forward match tespiti
- Edge case'ler

### 4. **test_ui_integration.py**
UI entegrasyon testleri:
- Gerçek senaryolar
- Performance testleri
- Memory usage testleri
- Kapsamlı test raporları

### 5. **test_alignment_improvements.py**
Mevcut alignment iyileştirmeleri testleri:
- Noktalama işleme
- Apostrophe işleme
- Char diff hesaplama

## 🚀 Test Çalıştırma

### Hızlı Test (UI için)
```bash
# Hızlı test - 5 temel test
make test-quick
# veya
python3 test_alignment_quick.py
```

### Kapsamlı Test
```bash
# Tüm alignment testleri
make test-alignment
# veya
python3 run_alignment_tests.py
```

### Tekil Test Dosyaları
```bash
# Belirli bir test dosyasını çalıştır
python3 -m pytest tests/test_alignment_criteria_compliance.py -v
python3 -m pytest tests/test_normalization_functions.py -v
python3 -m pytest tests/test_repetition_detection.py -v
python3 -m pytest tests/test_ui_integration.py -v
```

## 📊 Test Sonuçları

### Hızlı Test Sonuçları
- **Dosya:** `quick_test_results.json`
- **İçerik:** 5 temel test sonucu
- **Format:** JSON

### Kapsamlı Test Sonuçları
- **Dosya:** `alignment_test_results.json`
- **HTML Rapor:** `alignment_test_report.html`
- **İçerik:** Tüm test dosyaları + UI testleri
- **Format:** JSON + HTML

## 🎯 Test Kriterleri

### 1. CORRECT ✅
- Normalize edilmiş eşleşme
- Noktalama farkı hata değil
- Case-insensitive eşleşme

### 2. SUBSTITUTION ❌
- **harf_ekleme:** 1 harf ekleme
- **harf_eksiltme:** 1 harf eksiltme
- **harf_değiştirme:** 1 harf değiştirme
- **hece_ekleme:** ≥2 harf ekleme
- **hece_eksiltme:** ≥2 harf eksiltme

### 3. EXTRA ➕
- ref_token yok, hyp_token var

### 4. MISSING ➖
- ref_token var, hyp_token yok

### 5. REPETITION 🔁
- "--" pattern + sonraki token benzerliği
- Arka arkaya aynı tokenlar
- Sonradan ref ile eşleşme

## 🔧 Gereksinimler

```bash
# Test bağımlılıklarını yükle
pip install -r tests/requirements.txt
```

**Gerekli Paketler:**
- pytest==7.4.3
- pytest-asyncio==0.21.1
- httpx==0.25.2
- pytest-mock==3.12.0
- pytest-json-report==1.5.0
- psutil==5.9.6

## 📈 Performance Metrikleri

### Hızlı Test
- **Süre:** ~1-2 saniye
- **Test Sayısı:** 5
- **Memory:** Minimal

### Kapsamlı Test
- **Süre:** ~10-30 saniye
- **Test Sayısı:** 50+
- **Memory:** <100MB
- **Large Text:** 300+ token

## 🐛 Debug ve Sorun Giderme

### Test Başarısız Olursa
1. **Hızlı test çalıştır:** `make test-quick`
2. **Sonuçları kontrol et:** `quick_test_results.json`
3. **Detaylı test çalıştır:** `make test-alignment`
4. **HTML raporu incele:** `alignment_test_report.html`

### Yaygın Sorunlar
- **Import hatası:** Python path kontrolü
- **Memory hatası:** Büyük test dosyalarını küçült
- **Timeout:** Test timeout değerlerini artır

## 📝 Test Yazma Rehberi

### Yeni Test Ekleme
1. Mevcut test dosyalarından birini kopyala
2. Test sınıfını genişlet
3. Test metodları ekle
4. Assertion'ları yaz
5. Testi çalıştır ve doğrula

### Test Formatı
```python
def test_example():
    """Test description"""
    # Arrange
    ref_tokens = ["test"]
    hyp_tokens = ["test"]
    
    # Act
    alignment = levenshtein_align(ref_tokens, hyp_tokens)
    events = build_word_events(alignment, [])
    
    # Assert
    assert len(events) == 1
    assert events[0]["type"] == "correct"
```

## 🎉 Başarı Kriterleri

- **Hızlı Test:** 5/5 geçmeli
- **Kapsamlı Test:** %95+ başarı oranı
- **Performance:** <30 saniye
- **Memory:** <100MB

## 📞 Destek

Test sorunları için:
1. Test sonuçlarını kontrol edin
2. Log dosyalarını inceleyin
3. Gerekirse test parametrelerini ayarlayın
4. Yeni test case'leri ekleyin

