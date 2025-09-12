from typing import Any, List
from pymongo import IndexModel, ASCENDING, DESCENDING


def _to_index_model(v: Any) -> IndexModel:
    """Convert various index specifications to IndexModel."""
    if isinstance(v, IndexModel):
        return v
    if isinstance(v, str):
        return IndexModel([(v, ASCENDING)])
    if isinstance(v, tuple):
        # ör: ("field", -1) ya da ("field", 1)
        fld, order = v
        order = ASCENDING if order in (1, "asc", "ASC", ASCENDING) else DESCENDING
        return IndexModel([(fld, order)])
    if isinstance(v, list) and v and isinstance(v[0], tuple):
        # ör: [("a", 1), ("b", -1)]
        pairs = []
        for fld, order in v:
            pairs.append((fld, ASCENDING if order in (1, "asc", "ASC", ASCENDING) else DESCENDING))
        return IndexModel(pairs)
    if isinstance(v, dict):
        pairs = []
        for fld, order in v.items():
            pairs.append((fld, ASCENDING if order in (1, "asc", "ASC", ASCENDING) else DESCENDING))
        return IndexModel(pairs)
    raise ValueError(f"Unsupported index spec: {v!r}")


def normalize_indexes_for(doc_classes: List[type]):
    """Normalize indexes for Beanie Document classes."""
    for Doc in doc_classes:
        Settings = getattr(Doc, "Settings", None)
        if not Settings or not hasattr(Settings, "indexes"):
            continue
        raw = getattr(Settings, "indexes", None)
        if raw is None:
            continue
        if not isinstance(raw, (list, tuple)):
            raw = [raw]
        normalized = [_to_index_model(v) for v in raw]
        setattr(Settings, "indexes", normalized)
