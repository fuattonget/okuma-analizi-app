# 📚 Okuma Analizi - Alignment Sistemi Kılavuzu

**Tarih:** 1 Ekim 2025  
**Versiyon:** 2.0  
**Durum:** ✅ Kullanıma Hazır

---

## 🎯 Sistem Ne İş Yapar?

Öğrencinin okuduğu metni analiz ederek:
- ✅ Doğru okunan kelimeler
- ❌ Yanlış okunan kelimeler
- ➕ Fazladan söylenen kelimeler
- ➖ Atlanan kelimeler
- 🔁 Tekrar edilen kelimeler

Bu bilgileri tespit eder ve raporlar.

---

## 🔄 Nasıl Çalışır?

```
1. Ses dosyası yüklenir (MP3/WAV)
2. ElevenLabs metni yazıya çevirir
3. Sistem iki metni karşılaştırır:
   - Hedef metin (ne okunmalıydı)
   - Okunan metin (ne okundu)
4. Her kelime için hata türü belirlenir
5. Sonuçlar gösterilir
```

---

## 📊 Hata Türleri

### 1️⃣ CORRECT (Doğru) ✅

**Ne demek?** Kelime doğru okunmuş.

**Örnekler:**
- "okul" → "okul" ✅
- "ÖĞRETMEN" → "Öğretmen" ✅ (büyük/küçük harf farkı sayılmaz)
- "mı" → "mı?" ✅ (noktalama farkı sayılmaz)
- "okul" → "\"okul" ✅ (tırnak farkı sayılmaz)

**Kural:** Normalizasyon sonrası eşleşme:
- Büyük/küçük harf farketmez
- Noktalama farketmez (`,` `.` `?` `!` `:` `;`)
- Tırnak farketmez (`"` `"` `"`)

---

### 2️⃣ SUBSTITUTION (Değiştirme) 🔄

**Ne demek?** Kelime yanlış okunmuş.

#### 2a. Harf Ekleme (1 harf fazla)
```
"okul" → "okulu"
```

#### 2b. Harf Eksiltme (1 harf eksik)
```
"okulu" → "okul"
```

#### 2c. Harf Değiştirme (1 harf değişik)
```
"önce" → "önde"
```

#### 2d. Hece Ekleme (2+ harf fazla)
```
"eseriniz" → "eserleriniz"
```

#### 2e. Hece Eksiltme (2+ harf eksik)
```
"öğrencilerine" → "öğrencilere"
```

---

### 3️⃣ MISSING (Eksik) ➖

**Ne demek?** Kelime okunmamış, atlanmış.

**Örnek:**
```
Hedef metin: "yalan hiçbir şey"
Okunan:      "yalan şey"
→ "hiçbir" atlandı = MISSING
```

---

### 4️⃣ EXTRA (Fazla) ➕

**Ne demek?** Metinde olmayan kelime söylenmiş.

**Örnek:**
```
Hedef metin: "yalan şey"
Okunan:      "yalan çok şey"
→ "çok" fazladan = EXTRA
```

**Özel Durum:** Eğer extra kelime sonraki kelimeye %50+ benzerse, tekrarlama olarak değerlendirilir.

---

### 5️⃣ REPETITION (Tekrarlama) 🔁

**Ne demek?** Öğrenci kelimeyi tekrar etti veya kekeledi.

#### ElevenLabs Tekrarlama İşaretleri:

**1. "--" İşareti**
```
"okul--" → TEKRARLAMA
"öğretmenlerini--" → TEKRARLAMA
```
→ ElevenLabs kelimeyi kesik olarak algıladığında "--" koyar

**2. Ortada Tire**
```
"u-üzerindeki" → TEKRARLAMA
"öğre-öğretmenleri" → TEKRARLAMA
```
→ Kelime baştan başlatılmış

**3. Benzer Kelimeler**
```
Okunan: "hiç hiçbir"
→ "hiç" TEKRARLAMA (sonraki "hiçbir"e %50+ benzer)
```

**4. Aynı Kelimeler**
```
Okunan: "yeni yeni nesil"
→ İkinci "yeni" TEKRARLAMA
```

---

## ⚙️ ElevenLabs Ayarları

### Model Seçimi

**Stable (Önerilen):**
```bash
make model-stable
```
- Daha stabil
- Üretim için önerilen
- Model: `scribe_v1`

**Experimental (Daha İyi Kalite):**
```bash
make model-experimental
```
- Daha iyi kalite
- Bazen daha iyi sonuç verir
- Model: `scribe_v1_experimental`

### Ayarları Görüntüleme

```bash
make model-show      # Mevcut model
make temp-show       # Mevcut temperature
```

---

## 🎚️ Kalite Ayarları

### Temperature (Yaratıcılık)

| Değer | Ne Yapar | Ne Zaman Kullanılır |
|-------|----------|---------------------|
| 0.0 | En tutarlı | ✅ Önerilen (üretim) |
| 0.5 | Orta | Test için |
| 1.0+ | Değişken | Önerilmez |

**Değiştirmek için:**
```bash
make temp-0.0   # En tutarlı (önerilen)
make temp-0.5   # Orta
```

### Diğer Önemli Ayarlar

```env
ELEVENLABS_REMOVE_FILLER_WORDS=false     # Dolgu kelimeleri TUT
ELEVENLABS_REMOVE_DISFLUENCIES=false     # Tekrarları TUT
ELEVENLABS_SEED=12456                    # Aynı sonuç için
```

**Önemli:** Bu ayarları `false` tutun! Aksi halde tekrarları ve dolgu kelimelerini tespit edemeyiz.

---

## 🔍 Tekrarlama Tespiti Nasıl Çalışır?

### 1. "--" İşareti Kontrolü
```python
Kelime "--" içeriyor mu?
→ EVET: TEKRARLAMA
→ HAYIR: Devam et
```

### 2. Ortada Tire Kontrolü
```python
"u-üzerindeki" gibi ortada tire var mı?
→ EVET: TEKRARLAMA
→ HAYIR: Devam et
```

### 3. Sonraki Kelimeye Benzerlik
```python
Extra kelime sonraki kelimeye %50+ benzer mi?
Örnek: "hiç" → "hiçbir" (%75 benzer)
→ EVET: TEKRARLAMA
→ HAYIR: EXTRA olarak kal
```

### 4. Aynı Kelime Tekrarı
```python
5 kelime içinde aynı kelime var mı?
Örnek: "yeni ... yeni"
→ EVET: TEKRARLAMA
→ HAYIR: Normal işle
```

---

## 📏 Önemli Eşik Değerler

| Ne İçin | Değer | Açıklama |
|---------|-------|----------|
| **Benzer kelime** | %70 | İki kelime %70+ benzer → Tekrar |
| **Extra → Tekrar** | %50 | Extra kelime sonrakine %50+ benzer → Tekrar |
| **Forward match** | %80 | İleriye bakma için %80 benzerlik |
| **Karakter farkı** | 4+ | 4+ karakter farkı olmalı (substring için) |

**Not:** Bu değerler ihtiyaca göre ayarlanabilir.

---

## 🛠️ Hızlı Komutlar

### Sistem Yönetimi
```bash
make start          # Sistemi başlat
make stop           # Sistemi durdur
make restart        # Yeniden başlat
make logs-worker    # Worker logları
```

### Model/Kalite Ayarları
```bash
make model-experimental   # Daha iyi kalite
make model-stable        # Daha stabil
make model-show          # Ayarları göster
```

### Temizlik
```bash
make clean          # Containerları temizle
make clean-all      # Her şeyi temizle
```

---

## 💡 İpuçları

### Daha İyi Transkript İçin:

1. **Ses kalitesi yüksek olsun**
   - Minimum 16 kHz (önerilen 44.1 kHz)
   - Az gürültü
   - Net telaffuz

2. **Doğru ayarları kullanın**
   ```bash
   make model-experimental  # Daha iyi sonuç
   make temp-0.0           # Tutarlı sonuç
   ```

3. **Ses dosyası hazırlığı**
   - Sessiz ortam
   - İyi mikrofon
   - Normal konuşma hızı

---

## 🐛 Sorun Giderme

### "Model değişmedi" hatası
```bash
# Çözüm: Worker'ı yeniden oluştur
make model-experimental  # Otomatik yapıyor
```

### "Tekrarlar yakalanmıyor"
```bash
# Kontrol et:
ELEVENLABS_REMOVE_DISFLUENCIES=false  # Mutlaka false olmalı
```

### "Logları göremiyorum"
```bash
make logs-worker     # Worker logları
make logs-api        # API logları
make logs            # Tüm loglar
```

---

## 📈 Sistem İstatistikleri

### Kod Boyutu
- **Worker alignment:** 1,111 satır
- **Backend alignment:** 1,086 satır
- **Toplam:** 2,197 satır

### Fonksiyon Sayısı
- **Aktif fonksiyon:** 16 adet
- **Yardımcı fonksiyon:** 7 adet
- **Ana fonksiyon:** 9 adet

### Son Güncellemeler (v2.0)
- ✅ 9 önemli iyileştirme yapıldı
- ✅ 3 kullanılmayan fonksiyon silindi
- ✅ 3 kullanılmayan değişken silindi
- ✅ ~95 satır kod azaltıldı
- ✅ Tüm bilinen hatalar düzeltildi

---

## 🎯 Özet

### Sistem Yapabilir:
- ✅ 5 farklı hata türü tespit eder
- ✅ Tekrarlama ve kekemeleri yakalar
- ✅ Noktalama farklarını görmezden gelir
- ✅ ElevenLabs'ın özel işaretlerini anlar
- ✅ Dolgu kelimelerini tespit eder

### Kullanıcı Yapabilir:
- 🎚️ Model değiştirebilir (stable/experimental)
- 🎚️ Temperature ayarlayabilir (0.0-2.0)
- 📊 Detaylı raporlar alabilir
- 🔍 Logları inceleyebilir

### En İyi Ayarlar:
```env
MODEL=scribe_v1_experimental  # Daha iyi kalite
TEMPERATURE=0.0               # En tutarlı
SEED=12456                    # Tekrarlanabilir
REMOVE_FILLERS=false          # Dolgu kelimeleri tut
REMOVE_DISFLUENCIES=false     # Tekrarları tut
```

---

**Hazırlayan:** AI Assistant  
**Destek için:** Dokümantasyonu okuyun veya logları kontrol edin  
**Son Güncelleme:** 1 Ekim 2025

