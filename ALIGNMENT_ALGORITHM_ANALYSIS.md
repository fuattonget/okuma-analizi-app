# Alignment Algoritması Detaylı Analiz Raporu

## 📋 Özet

Bu rapor, Okuma Analizi sistemindeki **Alignment Algoritması** (`backend/app/services/alignment.py`) üzerinde yapılan detaylı teknik analizi içermektedir. Algoritma, Türkçe metinlerde konuşma tanıma sonuçları ile hedef metinler arasında kelime seviyesinde hizalama yapmak ve okuma hatalarını tespit etmek için kullanılmaktadır.

## 🎯 Algoritma Amacı

Alignment algoritması şu temel görevleri yerine getirir:

1. **Reference Text** (hedef metin) ile **Hypothesis Text** (konuşma tanıma sonucu) arasında kelime seviyesinde hizalama
2. **Okuma hatalarının tespiti**: eksik, fazla, değiştirilmiş, tekrarlanan kelimeler
3. **Türkçe dil özelliklerine uygun** hata sınıflandırması
4. **Timing bilgilerinin** korunması ve event'lerin oluşturulması

## 🏗️ Algoritma Mimarisi

### 1. Ana Fonksiyonlar

```python
# Ana alignment fonksiyonu
def levenshtein_align(ref_tokens: List[str], hyp_tokens: List[str], 
                     word_times: List[Dict[str, Any]] = None) -> List[Tuple[str, str, str, int, int]]

# Event oluşturma fonksiyonu  
def build_word_events(alignment: List[Tuple[str, str, str, int, int]], word_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]

# Türkçe tokenization
def tokenize_tr(text: str) -> List[str]
```

### 2. Yardımcı Fonksiyonlar

```python
# Token normalizasyonu
def _norm_token(tok: str) -> str

# Operation cost hesaplama
def _get_operation_cost(ref_token: str, hyp_token: str, operation: str, 
                       repeated_fillers: Dict[int, bool] = None, hyp_idx: int = -1) -> float

# Filler word tracking
def _track_filler_repetitions(hyp_tokens: List[str], word_times: List[Dict[str, Any]]) -> Dict[int, bool]

# Post-repair logic
def _post_repair_filler_substitutions(alignment: List[Tuple[str, str, str, int, int]]) -> List[Tuple[str, str, str, int, int]]
```

## 🔧 Algoritma Bileşenleri Detaylı Analizi

### 1. **Token Normalizasyonu** (`_norm_token`)

#### Amaç
Türkçe karakterleri normalize ederek karşılaştırma yapmak.

#### İşleyiş
```python
def _norm_token(tok: str) -> str:
    # 1. Küçük harfe çevir
    t = tok.lower()
    
    # 2. Türkçe karakter normalizasyonu
    t = t.replace('ı', 'i')
    t = t.replace('ğ', 'g') 
    t = t.replace('ç', 'c')
    t = t.replace('ö', 'o')
    t = t.replace('ü', 'u')
    t = t.replace('ş', 's')
    
    # 3. Unicode normalizasyonu
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = unicodedata.normalize('NFC', t)
    
    # 4. Noktalama temizleme
    t = re.sub(r'[.,!?;:"""]+$', '', t)
    t = re.sub(r'^[.,!?;:"""]+', '', t)
    
    return t
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: Normalizasyon çok agresif, anlam kaybına neden olabilir
- **Örnek**: `ışık` → `isik`, `göz` → `goz` 
- **Sonuç**: Farklı anlamlı kelimeler aynı olarak algılanabilir

### 2. **Dynamic Programming Tablosu**

#### Amaç
Levenshtein distance algoritması ile optimal alignment bulma.

#### İşleyiş
```python
# DP tablosu oluşturma
dp = [[0.0] * (n + 1) for _ in range(m + 1)]

# Base case'ler
for i in range(m + 1):
    dp[i][0] = dp[i-1][0] + _get_operation_cost(ref_tokens[i-1], "", "delete", repeated_fillers, -1)

for j in range(n + 1):
    dp[0][j] = dp[0][j-1] + _get_operation_cost("", hyp_tokens[j-1], "insert", repeated_fillers, j-1)

# DP tablosu doldurma
for i in range(1, m + 1):
    for j in range(1, n + 1):
        ref_token = ref_tokens[i-1]
        hyp_token = hyp_tokens[j-1]
        
        # Normalized equality check
        if _norm_token(ref_token) == _norm_token(hyp_token):
            dp[i][j] = dp[i-1][j-1]
        else:
            # Cost hesaplama
            del_cost = dp[i-1][j] + _get_operation_cost(ref_token, "", "delete", repeated_fillers, -1)
            ins_cost = dp[i][j-1] + _get_operation_cost("", hyp_token, "insert", repeated_fillers, j-1)
            rep_cost = dp[i-1][j-1] + _get_operation_cost(ref_token, hyp_token, "replace", repeated_fillers, j-1)
            
            dp[i][j] = min(del_cost, ins_cost, rep_cost)
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: Normalized equality check çok erken yapılıyor
- **Sonuç**: Context kaybı, yanlış eşleşmeler

### 3. **Operation Cost Hesaplama** (`_get_operation_cost`)

#### Amaç
Farklı operasyonların maliyetini hesaplamak.

#### İşleyiş
```python
def _get_operation_cost(ref_token: str, hyp_token: str, operation: str, 
                       repeated_fillers: Dict[int, bool] = None, hyp_idx: int = -1) -> float:
    if operation == "equal":
        return 0.0
    elif operation in ["insert", "delete"]:
        base_cost = 1.0
        
        # Stopword'ler için düşük cost
        token = ref_token if operation == "delete" else hyp_token
        if _is_stop(token):
            base_cost = 0.4
        
        # Filler word handling
        if operation == "insert" and _is_filler(hyp_token):
            if repeated_fillers and hyp_idx in repeated_fillers and repeated_fillers[hyp_idx]:
                return max(0.1, base_cost - 0.3)  # Repeated filler bonus
            else:
                return base_cost
        
        return base_cost
    elif operation == "replace":
        # Punctuation substitution - forbid
        if _is_punctuation(ref_token) or _is_punctuation(hyp_token):
            return float('inf')
        
        # Filler substitution - forbid
        if _is_filler(hyp_token) and not _is_filler(ref_token):
            return float('inf')
        
        # Stopword substitution - higher cost
        return 1.2 if (_is_stop(ref_token) or _is_stop(hyp_token)) else 1.0
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: `base_cost - 0.3` negatif olabilir
- **Örnek**: `base_cost = 0.4`, sonuç = `0.1` (çok düşük cost)
- **Sonuç**: Yanlış filler classification

### 4. **Filler Word Tracking** (`_track_filler_repetitions`)

#### Amaç
2 saniye içinde tekrarlanan filler word'leri tespit etmek.

#### İşleyiş
```python
def _track_filler_repetitions(hyp_tokens: List[str], word_times: List[Dict[str, Any]]) -> Dict[int, bool]:
    repetition_window_ms = 2000  # 2 seconds
    filler_counts = {}  # filler_word -> list of (timestamp, index)
    repeated_fillers = {}
    
    for i, (token, timing) in enumerate(zip(hyp_tokens, word_times)):
        if _is_filler(token) and timing and 'start' in timing:
            start_ms = timing['start'] * 1000
            filler_word = _norm_token(token)
            
            if filler_word not in filler_counts:
                filler_counts[filler_word] = []
            
            # Add current occurrence
            filler_counts[filler_word].append((start_ms, i))
            
            # Remove old occurrences outside window
            filler_counts[filler_word] = [
                (ts, idx) for ts, idx in filler_counts[filler_word] 
                if start_ms - ts <= repetition_window_ms
            ]
            
            # Mark as repeated if appears 2+ times in window
            if len(filler_counts[filler_word]) >= 2:
                repeated_fillers[i] = True
            else:
                repeated_fillers[i] = False
    
    return repeated_fillers
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: `word_times` yoksa tüm filler'lar normal cost alır
- **Sonuç**: Inconsistent filler handling

### 5. **Repetition Pattern Detection**

#### Amaç
`öğret-öğretmen` gibi tekrarlama pattern'lerini tespit etmek.

#### İşleyiş
```python
# Special case: "öğret-öğretmen" pattern
is_repetition_pattern = False
if ("-" in hyp_token and not hyp_token.startswith("-") and not hyp_token.endswith("-")):
    parts = hyp_token.split("-", 1)
    if len(parts) > 1:
        norm_hyp_after_dash = _norm_token(parts[1])
        norm_ref = _norm_token(ref_token)
        if norm_hyp_after_dash == norm_ref:
            is_repetition_pattern = True

if is_repetition_pattern:
    # Treat as repetition pattern
    alignment.append(("replace", ref_token, hyp_token, i-1, j-1))
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: Her `-` içeren kelimeyi repetition olarak algılayabilir
- **Örnek**: `türk-amerikan` → yanlış repetition detection
- **Sonuç**: False positive repetition events

### 6. **Backtracking Logic**

#### Amaç
DP tablosundan optimal alignment path'ini çıkarmak.

#### İşleyiş
```python
while i > 0 or j > 0:
    ref_token = ref_tokens[i-1] if i > 0 else ""
    hyp_token = hyp_tokens[j-1] if j > 0 else ""
    
    # Normalized equality check
    if i > 0 and j > 0 and _norm_token(ref_token) == _norm_token(hyp_token):
        alignment.append(("equal", ref_token, hyp_token, i-1, j-1))
        i -= 1
        j -= 1
    elif i > 0 and (j == 0 or dp[i-1][j] < dp[i][j-1]):
        # Delete - skip punctuation
        if _is_punctuation(ref_token):
            i -= 1  # Skip punctuation completely
        else:
            alignment.append(("delete", ref_token, "", i-1, -1))
            i -= 1
    # ... diğer durumlar
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: `i -= 1` ile `continue` eksik olabilir
- **Sonuç**: Infinite loop riski

### 7. **Post-Repair Logic** (`_post_repair_filler_substitutions`)

#### Amaç
Problemli filler substitution'ları MISSING+EXTRA pair'lerine çevirmek.

#### İşleyiş
```python
def _post_repair_filler_substitutions(alignment: List[Tuple[str, str, str, int, int]]) -> List[Tuple[str, str, str, int, int]]:
    repaired = []
    i = 0
    
    while i < len(alignment):
        op, ref_token, hyp_token, ref_idx, hyp_idx = alignment[i]
        
        if op == "replace" and _is_filler(hyp_token) and not _is_filler(ref_token):
            # Check if next alignment has high similarity
            next_similar = False
            if i + 1 < len(alignment):
                next_op, next_ref, next_hyp, _, _ = alignment[i + 1]
                if next_op in ["equal", "replace"] and next_ref and next_hyp:
                    # Calculate normalized Levenshtein distance
                    lev_dist = char_edit_stats(ref_token, next_hyp)[0]
                    max_len = max(len(ref_token), len(next_hyp))
                    lev_norm = lev_dist / max_len if max_len > 0 else 1.0
                    
                    if lev_norm <= 0.3:  # High similarity threshold
                        next_similar = True
            
            if next_similar:
                # Convert SUB to MISSING + EXTRA
                repaired.append(("delete", ref_token, "", ref_idx, -1))
                repaired.append(("insert", "", hyp_token, -1, hyp_idx))
            else:
                repaired.append((op, ref_token, hyp_token, ref_idx, hyp_idx))
        else:
            repaired.append((op, ref_token, hyp_token, ref_idx, hyp_idx))
        
        i += 1
    
    return repaired
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: Magic number `0.3` threshold sabit
- **Sonuç**: Farklı context'ler için uygun olmayabilir

### 8. **Word Event Building** (`build_word_events`)

#### Amaç
Alignment sonuçlarından WordEventDoc formatında event'ler oluşturmak.

#### İşleyiş
```python
def build_word_events(alignment: List[Tuple[str, str, str, int, int]], word_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    word_events = []
    
    for op, ref_token, hyp_token, ref_idx, hyp_idx in alignment:
        # Skip punctuation tokens
        if _is_punctuation(ref_token) or _is_punctuation(hyp_token):
            if (ref_token and hyp_token and 
                _is_punctuation(ref_token) and _is_punctuation(hyp_token) and 
                ref_token == hyp_token):
                event_type = "correct"
                subtype = None
            else:
                continue  # Skip punctuation
        
        # Check for normalized equality
        elif _norm_token(ref_token) == _norm_token(hyp_token):
            event_type = "correct"
            subtype = "case_punct_only"
        elif op == "equal":
            event_type = "correct"
            subtype = None
        elif op == "delete":
            event_type = "missing"
            subtype = None
        elif op == "insert":
            event_type = "extra"
            subtype = None
        elif op == "replace":
            # Check for repetition pattern
            is_repetition_pattern = False
            if ("-" in hyp_token and not hyp_token.startswith("-") and not hyp_token.endswith("-")):
                parts = hyp_token.split("-", 1)
                if len(parts) > 1:
                    norm_hyp_after_dash = _norm_token(parts[1])
                    norm_ref = _norm_token(ref_token)
                    if norm_hyp_after_dash == norm_ref:
                        is_repetition_pattern = True
            
            if is_repetition_pattern:
                event_type = "repetition"
                subtype = "enhanced_pattern"
            else:
                event_type = "substitution"
                subtype = classify_replace(ref_token, hyp_token)
                subtype = normalize_sub_type(subtype)
        
        # Get timing data
        start_ms = None
        end_ms = None
        if hyp_idx >= 0 and hyp_idx < len(word_times):
            start_ms = word_times[hyp_idx].get("start", 0) * 1000
            end_ms = word_times[hyp_idx].get("end", 0) * 1000
        
        event_data = {
            "ref_token": ref_token if ref_token else None,
            "hyp_token": hyp_token if hyp_token else None,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "type": event_type,
            "sub_type": subtype,
            "ref_idx": ref_idx,
            "hyp_idx": hyp_idx
        }
        
        word_events.append(event_data)
    
    return word_events
```

#### 🚨 **Kritik Hata Noktası**
- **Problem**: Double normalization (hem DP'de hem event building'de)
- **Sonuç**: Inconsistent classification

## 🚨 **Kritik Algoritma Hataları**

### 1. **Normalizasyon Çok Agresif**
- **Problem**: Türkçe karakterler çok agresif normalize ediliyor
- **Etki**: Farklı anlamlı kelimeler aynı olarak algılanıyor
- **Örnek**: `ışık` → `isik`, `göz` → `goz`

### 2. **Filler Tracking Timing-Dependent**
- **Problem**: `word_times` yoksa filler logic çalışmıyor
- **Etki**: Inconsistent filler handling
- **Sonuç**: Bazı durumlarda filler'lar normal cost alıyor

### 3. **Operation Costs Negative Olabilir**
- **Problem**: `base_cost - 0.3` negatif sonuç verebilir
- **Etki**: DP table corruption
- **Sonuç**: Yanlış alignment path'leri

### 4. **Repetition Pattern Over-Matching**
- **Problem**: Her `-` içeren kelimeyi repetition olarak algılıyor
- **Etki**: False positive repetition detection
- **Örnek**: `türk-amerikan` → yanlış repetition

### 5. **Backtracking Complexity**
- **Problem**: Complex backtracking logic
- **Etki**: Index errors ve infinite loop riski
- **Sonuç**: System crash

### 6. **Magic Numbers**
- **Problem**: Sabit threshold'lar (0.3, 2000ms, 0.4)
- **Etki**: Non-adaptive behavior
- **Sonuç**: Farklı context'ler için uygun olmayabilir

### 7. **Double Normalization**
- **Problem**: Hem DP'de hem event building'de normalizasyon
- **Etki**: Inconsistent results
- **Sonuç**: Aynı durum farklı şekilde sınıflandırılabilir

## 📊 **Performans Analizi**

### Time Complexity
- **Levenshtein DP**: O(m×n) where m=ref_tokens, n=hyp_tokens
- **Filler tracking**: O(n) where n=hyp_tokens
- **Post-repair**: O(k) where k=alignment_length
- **Overall**: O(m×n) - optimal for alignment problem

### Space Complexity
- **DP table**: O(m×n)
- **Filler tracking**: O(n)
- **Overall**: O(m×n)

### Memory Usage
- **DP table**: 8 bytes per cell (float64)
- **Example**: 1000×1000 tokens = ~8MB memory

## 🎯 **Önerilen İyileştirmeler**

### 1. **Normalizasyon İyileştirmesi**
```python
def _norm_token_conservative(tok: str) -> str:
    """Daha conservative normalizasyon"""
    # Sadece case normalization
    t = tok.lower()
    
    # Sadece temel noktalama temizleme
    t = re.sub(r'[.,!?;:"""]+$', '', t)
    t = re.sub(r'^[.,!?;:"""]+', '', t)
    
    return t
```

### 2. **Filler Tracking İyileştirmesi**
```python
def _track_filler_repetitions_robust(hyp_tokens: List[str], word_times: List[Dict[str, Any]] = None) -> Dict[int, bool]:
    """Timing-independent filler tracking"""
    if not word_times:
        # Fallback: simple repetition detection
        return _simple_filler_repetition_detection(hyp_tokens)
    else:
        return _timing_based_filler_repetition_detection(hyp_tokens, word_times)
```

### 3. **Operation Cost İyileştirmesi**
```python
def _get_operation_cost_safe(ref_token: str, hyp_token: str, operation: str, 
                           repeated_fillers: Dict[int, bool] = None, hyp_idx: int = -1) -> float:
    """Safe operation cost calculation"""
    if operation == "insert" and _is_filler(hyp_token):
        if repeated_fillers and hyp_idx in repeated_fillers and repeated_fillers[hyp_idx]:
            # Ensure minimum cost
            return max(0.2, base_cost - 0.2)
        else:
            return base_cost
```

### 4. **Repetition Pattern İyileştirmesi**
```python
def _is_valid_repetition_pattern(ref_token: str, hyp_token: str) -> bool:
    """Daha strict repetition pattern detection"""
    if "-" not in hyp_token:
        return False
    
    # Check if it's a valid Turkish repetition pattern
    parts = hyp_token.split("-", 1)
    if len(parts) != 2:
        return False
    
    # Additional validation
    if len(parts[0]) < 3 or len(parts[1]) < 3:  # Minimum length
        return False
    
    # Check if first part is prefix of second part
    if not parts[1].startswith(parts[0]):
        return False
    
    return _norm_token(parts[1]) == _norm_token(ref_token)
```

### 5. **Backtracking İyileştirmesi**
```python
def _safe_backtrack(dp: List[List[float]], ref_tokens: List[str], hyp_tokens: List[str]) -> List[Tuple[str, str, str, int, int]]:
    """Safe backtracking with proper error handling"""
    alignment = []
    i, j = len(ref_tokens), len(hyp_tokens)
    
    while i > 0 or j > 0:
        try:
            # Safe index access
            ref_token = ref_tokens[i-1] if i > 0 else ""
            hyp_token = hyp_tokens[j-1] if j > 0 else ""
            
            # ... backtracking logic with proper bounds checking
            
        except (IndexError, ValueError) as e:
            logger.error(f"Backtracking error at position ({i}, {j}): {e}")
            break
    
    return alignment
```

## 🔍 **Test Senaryoları**

### 1. **Normalizasyon Testi**
```python
def test_normalization():
    test_cases = [
        ("ışık", "isik", True),  # Should be different
        ("göz", "goz", True),    # Should be different  
        ("çok", "cok", False),   # Should be same
        ("öğretmen", "ogretmen", False),  # Should be same
    ]
    
    for ref, hyp, should_differ in test_cases:
        result = _norm_token(ref) == _norm_token(hyp)
        assert result != should_differ, f"Normalization error: {ref} vs {hyp}"
```

### 2. **Filler Tracking Testi**
```python
def test_filler_tracking():
    hyp_tokens = ["çok", "güzel", "çok", "bir", "gün"]
    word_times = [
        {"start": 0.0, "end": 0.5},
        {"start": 0.6, "end": 1.0}, 
        {"start": 1.1, "end": 1.6},  # 0.1s gap - should be repeated
        {"start": 1.7, "end": 2.0},
        {"start": 2.1, "end": 2.5}
    ]
    
    result = _track_filler_repetitions(hyp_tokens, word_times)
    assert result[2] == True, "Second 'çok' should be marked as repeated"
```

### 3. **Repetition Pattern Testi**
```python
def test_repetition_patterns():
    test_cases = [
        ("öğretmen", "öğret-öğretmen", True),   # Valid repetition
        ("türk", "türk-amerikan", False),       # Invalid repetition
        ("kitap", "kitap-kitap", True),         # Valid repetition
        ("okul", "okul-öğretmen", False),       # Invalid repetition
    ]
    
    for ref, hyp, should_be_repetition in test_cases:
        result = _is_valid_repetition_pattern(ref, hyp)
        assert result == should_be_repetition, f"Repetition error: {ref} vs {hyp}"
```

## 📈 **Metrikler ve Değerlendirme**

### 1. **Accuracy Metrics**
- **Alignment Accuracy**: Doğru alignment oranı
- **Error Classification Accuracy**: Hata sınıflandırma doğruluğu
- **False Positive Rate**: Yanlış pozitif oranı
- **False Negative Rate**: Yanlış negatif oranı

### 2. **Performance Metrics**
- **Processing Time**: Alignment işlem süresi
- **Memory Usage**: Bellek kullanımı
- **Throughput**: Dakikada işlenen kelime sayısı

### 3. **Quality Metrics**
- **WER (Word Error Rate)**: Kelime hata oranı
- **CER (Character Error Rate)**: Karakter hata oranı
- **Alignment Quality Score**: Alignment kalite skoru

## 🎯 **Sonuç ve Öneriler**

Alignment algoritması genel olarak iyi tasarlanmış ancak **kritik hata noktaları** bulunmaktadır. En önemli sorunlar:

1. **Normalizasyon çok agresif** → False positive matches
2. **Filler tracking timing-dependent** → Inconsistent behavior
3. **Operation costs negative olabilir** → DP table corruption
4. **Repetition pattern over-matching** → False repetition detection

**Öncelikli iyileştirmeler:**
1. Conservative normalizasyon implementasyonu
2. Robust filler tracking (timing-independent)
3. Safe operation cost calculation
4. Strict repetition pattern validation
5. Comprehensive test suite

Bu iyileştirmeler yapıldığında, algoritmanın accuracy'si ve reliability'si önemli ölçüde artacaktır.

---

**Rapor Tarihi**: 2024-12-19  
**Versiyon**: 1.0  
**Hazırlayan**: AI Code Assistant  
**Dosya**: `backend/app/services/alignment.py`
