from typing import Any, Iterable, List, Tuple
from loguru import logger

def _to_index_model(entry: Any):
    from pymongo.operations import IndexModel
    from pymongo import ASCENDING
    # Zaten IndexModel ise bırak
    if isinstance(entry, IndexModel):
        return entry
    # Tek tuple: ("field", 1)
    if isinstance(entry, tuple):
        if len(entry) == 2:
            return IndexModel([entry])
    # Liste: [("f1", 1), ("f2", -1)] veya [[("f1",1)]]
    if isinstance(entry, list):
        if len(entry) == 1 and isinstance(entry[0], tuple) and len(entry[0]) == 2:
            return IndexModel([entry[0]])
        if all(isinstance(t, tuple) and len(t) == 2 for t in entry):
            return IndexModel(entry)
    # Dict: {"field": 1}
    if isinstance(entry, dict):
        items = list(entry.items())
        if all(isinstance(t, tuple) and len(t) == 2 for t in items):
            return IndexModel(items)
    # Str kısayol: "field" -> ASC
    if isinstance(entry, str):
        return IndexModel([(entry, ASCENDING)])
    raise TypeError(f"Unsupported index spec: {entry!r} ({type(entry)})")

def normalize_document_indexes(doc_cls):
    try:
        print(f"🔍 DEBUG: Normalizing {doc_cls.__name__}...")
        logger.info(f"Starting index normalization for {doc_cls.__name__}")
        
        try:
            Settings = getattr(doc_cls, "Settings", None)
            if not Settings or not hasattr(Settings, "indexes"):
                print(f"🔍 DEBUG: {doc_cls.__name__} has no Settings or indexes")
                logger.warning(f"{doc_cls.__name__} has no Settings or indexes")
                return
            logger.info(f"Settings found for {doc_cls.__name__}")
        except Exception as e:
            logger.error(f"Failed to get Settings for {doc_cls.__name__}: {e}")
            raise
        
        try:
            raw = getattr(Settings, "indexes")
            if raw is None:
                print(f"🔍 DEBUG: {doc_cls.__name__} has None indexes")
                logger.warning(f"{doc_cls.__name__} has None indexes")
                return
            logger.info(f"Raw indexes found for {doc_cls.__name__}: {raw}")
        except Exception as e:
            logger.error(f"Failed to get indexes from Settings for {doc_cls.__name__}: {e}")
            raise
        
        try:
            if not isinstance(raw, (list, tuple)):
                raw = [raw]
            print(f"🔍 DEBUG: {doc_cls.__name__} raw indexes: {raw}")
            logger.info(f"Normalized raw indexes for {doc_cls.__name__}: {raw}")
        except Exception as e:
            logger.error(f"Failed to normalize raw indexes for {doc_cls.__name__}: {e}")
            raise
        
        try:
            fixed = []
            for i, v in enumerate(raw):
                try:
                    print(f"🔍 DEBUG: Converting {doc_cls.__name__} index {i}: {v} (type: {type(v)})")
                    logger.info(f"Converting {doc_cls.__name__} index {i}: {v} (type: {type(v)})")
                    converted = _to_index_model(v)
                    print(f"🔍 DEBUG: Converted to: {converted} (type: {type(converted)})")
                    logger.info(f"Converted {doc_cls.__name__} index {i} to: {converted} (type: {type(converted)})")
                    fixed.append(converted)
                except Exception as e:
                    logger.error(f"[indexes] {doc_cls.__name__}[{i}] bad spec {v!r}: {e}")
                    logger.error(f"Index conversion failed for {doc_cls.__name__}[{i}]: {e}")
                    raise
            
            Settings.indexes = fixed
            print(f"🔍 DEBUG: {doc_cls.__name__} normalized indexes: {[type(x).__name__ for x in fixed]}")
            logger.info(f"{doc_cls.__name__} normalized indexes: {[type(x).__name__ for x in fixed]}")
            
        except Exception as e:
            logger.error(f"Failed to convert indexes for {doc_cls.__name__}: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Critical error in normalize_document_indexes for {doc_cls.__name__}: {e}")
        raise

def normalize_all_documents():
    try:
        from beanie import Document
        from pymongo import IndexModel, ASCENDING, DESCENDING
        import inspect, pkgutil, importlib
        logger.info("Starting normalization of all documents")
        
        # Muhtemel modellerin kök paketlerini sırayla dene
        try:
            candidates = []
            for name in ("app.models", "src.okuma_analizi.models", "app", "src.okuma_analizi"):
                try:
                    candidates.append(importlib.import_module(name))
                    logger.info(f"Successfully imported module: {name}")
                except Exception as e:
                    logger.warning(f"Failed to import module {name}: {e}")
                    pass
            logger.info(f"Found {len(candidates)} candidate modules")
        except Exception as e:
            logger.error(f"Failed to import candidate modules: {e}")
            raise
        
        try:
            seen = set()
            for pkg in candidates:
                try:
                    logger.info(f"Processing package: {pkg.__name__}")
                    for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                        try:
                            m = importlib.import_module(modname)
                            logger.info(f"Successfully imported submodule: {modname}")
                        except Exception as e:
                            logger.warning(f"Failed to import submodule {modname}: {e}")
                            continue
                        
                        try:
                            for _, obj in inspect.getmembers(m, inspect.isclass):
                                if obj in seen:
                                    continue
                                seen.add(obj)
                                try:
                                    from beanie import Document as _Doc
                                    if issubclass(obj, _Doc) and obj is not _Doc:
                                        logger.info(f"Found Beanie document class: {obj.__name__}")
                                        normalize_document_indexes(obj)
                                except Exception as e:
                                    logger.warning(f"Failed to process class {obj.__name__}: {e}")
                                    continue
                        except Exception as e:
                            logger.error(f"Failed to process members of module {modname}: {e}")
                            continue
                except Exception as e:
                    logger.error(f"Failed to process package {pkg.__name__}: {e}")
                    continue
            
            logger.info(f"Processed {len(seen)} document classes")
        except Exception as e:
            logger.error(f"Failed to process document classes: {e}")
            raise
        
        # Yeni modellerin indekslerini manuel olarak garanti altına al
        try:
            logger.info("Ensuring indexes for new models...")
            ensure_new_model_indexes()
        except Exception as e:
            logger.error(f"Failed to ensure new model indexes: {e}")
            raise
        
        logger.info("✔ Index Settings normalized to IndexModel")
        
    except Exception as e:
        logger.error(f"Critical error in normalize_all_documents: {e}")
        raise


def ensure_new_model_indexes():
    """Manually ensure indexes for new models that might not be auto-discovered"""
    from pymongo import IndexModel, ASCENDING, DESCENDING
    
    # ReadingSessionDoc indexes
    reading_session_indexes = [
        IndexModel([("text_id", ASCENDING)], name="sessions_text_id_asc"),
        IndexModel([("audio_id", ASCENDING)], name="sessions_audio_id_asc"),
        IndexModel([("reader_id", ASCENDING)], name="sessions_reader_id_asc"),
        IndexModel([("status", ASCENDING)], name="sessions_status_asc"),
        IndexModel([("created_at", DESCENDING)], name="sessions_created_at_desc"),
    ]
    
    # WordEventDoc indexes
    word_event_indexes = [
        IndexModel([("analysis_id", ASCENDING)], name="word_events_analysis_id_asc"),
        IndexModel([("position", ASCENDING)], name="word_events_position_asc"),
        IndexModel([("type", ASCENDING)], name="word_events_type_asc"),
        IndexModel([("analysis_id", ASCENDING), ("position", ASCENDING)], name="word_events_analysis_position_asc"),
    ]
    
    # PauseEventDoc indexes
    pause_event_indexes = [
        IndexModel([("analysis_id", ASCENDING)], name="pause_events_analysis_id_asc"),
        IndexModel([("after_position", ASCENDING)], name="pause_events_after_position_asc"),
        IndexModel([("class_", ASCENDING)], name="pause_events_class_asc"),
        IndexModel([("duration_ms", DESCENDING)], name="pause_events_duration_ms_desc"),
    ]
    
    # SttResultDoc indexes
    stt_result_indexes = [
        IndexModel([("session_id", ASCENDING)], name="stt_results_session_id_asc"),
        IndexModel([("provider", ASCENDING)], name="stt_results_provider_asc"),
        IndexModel([("language", ASCENDING)], name="stt_results_language_asc"),
        IndexModel([("created_at", DESCENDING)], name="stt_results_created_at_desc"),
    ]
    
    # TextDoc additional indexes (slug unique)
    text_doc_indexes = [
        IndexModel([("slug", ASCENDING)], name="texts_slug_asc", unique=True),
        IndexModel([("active", ASCENDING)], name="texts_active_asc"),
    ]
    
    # AudioFileDoc additional indexes (owner.reader_id)
    audio_file_indexes = [
        IndexModel([("owner.reader_id", ASCENDING)], name="audios_owner_reader_id_asc"),
    ]
    
    # AnalysisDoc additional indexes (session_id)
    analysis_doc_indexes = [
        IndexModel([("session_id", ASCENDING)], name="analyses_session_id_asc"),
    ]
    
    logger.info("New model indexes defined successfully")
    logger.info(f"ReadingSessionDoc: {len(reading_session_indexes)} indexes")
    logger.info(f"WordEventDoc: {len(word_event_indexes)} indexes")
    logger.info(f"PauseEventDoc: {len(pause_event_indexes)} indexes")
    logger.info(f"SttResultDoc: {len(stt_result_indexes)} indexes")
    logger.info(f"TextDoc additional: {len(text_doc_indexes)} indexes")
    logger.info(f"AudioFileDoc additional: {len(audio_file_indexes)} indexes")
    logger.info(f"AnalysisDoc additional: {len(analysis_doc_indexes)} indexes")
