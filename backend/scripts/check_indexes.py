import sys
sys.path.append(".")

from app.db_init_guard import normalize_all_documents
normalize_all_documents()

from beanie import Document
import inspect, pkgutil, importlib

def list_indexes():
    pkgs = []
    for name in ("app.models", "src.okuma_analizi.models", "app", "src.okuma_analizi"):
        try:
            pkgs.append(importlib.import_module(name))
        except Exception:
            pass
    for pkg in pkgs:
        for _, modname, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            m = importlib.import_module(modname)
            for _, obj in inspect.getmembers(m, inspect.isclass):
                try:
                    if issubclass(obj, Document) and obj is not Document:
                        Settings = getattr(obj, "Settings", None)
                        idx = getattr(Settings, "indexes", None)
                        kinds = [type(v).__name__ for v in (idx or [])]
                        print(f"{obj.__name__}: indexes={kinds}")
                except Exception:
                    pass

if __name__ == "__main__":
    list_indexes()
