# Okuma Analizi Test Suite

Bu dizin, Okuma Analizi projesi için kapsamlı test suite'ini içerir.

## Test Dosyaları

### 1. `test_models_indexes.py`
- **Amaç:** Tüm koleksiyonlarda indekslerin varlığını doğrular
- **Testler:**
  - TextDoc, AudioFileDoc, AnalysisDoc indeksleri
  - ReadingSessionDoc, WordEventDoc, PauseEventDoc, SttResultDoc indeksleri
  - Composite indeksler (analysis_id + position)
  - Unique indeksler (slug)
  - Nested field indeksleri (owner.reader_id)
  - Index performance testleri

### 2. `test_migration_v2.py`
- **Amaç:** Migration v2 script'ini test eder
- **Testler:**
  - TextDoc migration (tokenized_words → canonical.tokens, slug generation)
  - AudioFileDoc migration (gcs_url removal, privacy settings)
  - ReadingSessionDoc creation (text_id + audio_id → session_id)
  - WordEventDoc + PauseEventDoc creation (flattening from summary)
  - AnalysisDoc error_types normalization (Turkish → English)
  - Dry-run vs actual migration
  - Batch processing
  - Error handling

### 3. `test_analysis_pipeline_events.py`
- **Amaç:** Analiz pipeline'ının event üretimini test eder
- **Testler:**
  - analyze_audio fonksiyonu event creation
  - SttResultDoc creation (STT sonrası)
  - WordEventDoc creation (alignment sonrası)
  - PauseEventDoc creation (pause detection sonrası)
  - AnalysisDoc summary aggregation
  - ReadingSessionDoc status update
  - Error handling ve partial failures
  - Individual service functions (build_word_events, detect_pauses, recompute_counts)

### 4. `test_api_sessions.py`
- **Amaç:** Yeni API endpoint'lerini test eder
- **Testler:**
  - GET /v1/sessions (list, filtering, pagination)
  - GET /v1/sessions/{id} (detail with text + audio info)
  - GET /v1/sessions/{id}/analyses (session analyses)
  - PUT /v1/sessions/{id}/status (status update)
  - GET /v1/analyses/{id}/word-events (word events)
  - GET /v1/analyses/{id}/pause-events (pause events)
  - GET /v1/analyses/{id}/metrics (aggregated metrics)
  - 200/404/400 status code validation
  - Error handling

## Test Yapısı

### Fixtures (`conftest.py`)
- `test_db`: Test database connection
- `clean_db`: Database cleanup before each test
- `sample_text_data`: Test text data
- `sample_audio_data`: Test audio data
- `sample_analysis_data`: Test analysis data

### Test Environment
- **Database:** MongoDB test instance
- **Database Name:** `okuma_analizi_test`
- **Isolation:** Her test öncesi database temizlenir
- **Async Support:** pytest-asyncio ile async test desteği

## Çalıştırma

### Gereksinimler
```bash
pip install -r tests/requirements.txt
```

### Tüm Testleri Çalıştır
```bash
python tests/run_tests.py
```

### Belirli Test Dosyası
```bash
pytest tests/test_models_indexes.py -v
```

### Belirli Test Fonksiyonu
```bash
pytest tests/test_api_sessions.py::TestAPISessions::test_get_sessions_success -v
```

### Verbose Output
```bash
pytest tests/ -v --tb=short
```

## Test Kapsamı

### Model Tests
- ✅ Index creation ve validation
- ✅ Unique constraints
- ✅ Composite indexes
- ✅ Performance testing

### Migration Tests
- ✅ Dry-run functionality
- ✅ Data transformation
- ✅ Error handling
- ✅ Batch processing
- ✅ Rollback safety

### Pipeline Tests
- ✅ End-to-end analysis flow
- ✅ Event creation
- ✅ Data aggregation
- ✅ Error scenarios
- ✅ Service integration

### API Tests
- ✅ HTTP status codes
- ✅ Response formats
- ✅ Error handling
- ✅ Authentication (if applicable)
- ✅ Data validation

## Test Data

### Sample Text
```json
{
  "title": "Test Metin",
  "grade": 3,
  "body": "Bu bir test metnidir. Okuma analizi için kullanılacak.",
  "canonical": {
    "tokens": ["Bu", "bir", "test", "metnidir", ".", "Okuma", "analizi", "için", "kullanılacak", "."]
  }
}
```

### Sample Audio
```json
{
  "original_name": "test_audio.wav",
  "storage_name": "test_storage.wav",
  "gcs_uri": "gs://test-bucket/test_audio.wav",
  "content_type": "audio/wav",
  "size_bytes": 1024000,
  "duration_sec": 10.5
}
```

### Sample Analysis
```json
{
  "status": "done",
  "summary": {
    "wer": 0.15,
    "accuracy": 85.0,
    "wpm": 120.5,
    "counts": {
      "correct": 8,
      "missing": 1,
      "extra": 1,
      "diff": 1,
      "total_words": 10
    }
  }
}
```

## Continuous Integration

Test suite CI/CD pipeline'da çalıştırılabilir:

```yaml
test:
  stage: test
  script:
    - pip install -r tests/requirements.txt
    - python tests/run_tests.py
  services:
    - mongodb:latest
    - redis:latest
```

## Debugging

### Test Logs
```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

### Database Inspection
```python
# Test içinde database'i inspect et
print(await test_db.list_collection_names())
```

### Mock Debugging
```python
# Mock calls'i inspect et
print(mock_stt.call_args_list)
```

## Best Practices

1. **Isolation:** Her test bağımsız çalışmalı
2. **Cleanup:** Test sonrası database temizlenmeli
3. **Mocking:** External services mock'lanmalı
4. **Assertions:** Specific ve meaningful assertions
5. **Error Testing:** Error scenarios test edilmeli
6. **Performance:** Critical paths performance test edilmeli

