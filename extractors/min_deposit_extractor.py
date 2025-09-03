# extractors/min_deposit_extractor.py
from typing import Tuple, Optional, Any

def _to_float_safe(v: Any) -> Optional[float]:
    """Пытается привести v к float. Возвращает None, если не получилось."""
    if v is None:
        return None
    try:
        s = str(v).strip()
        if not s:
            return None
        return float(s.replace(",", "."))
    except Exception:
        return None

def compute_min_deposit(item: dict) -> Tuple[Optional[float], str]:
    """
    Возвращает:
      (min_value, source)
    Политика: используем min из разных возможных мест.
    
    Приоритет:
      1. item["min"]
      2. item["paymethods"]["min"]
      3. item["paymethod"]["min"]
      4. item["min_dep_flow"]
      5. item["default"] (если это тоже минимальная сумма)
    """
    if not isinstance(item, dict):
        return None, "none"

    # Список потенциальных мест, где может лежать минимальный депозит
    candidates = [
        ("min", item.get("min")),
        ("paymethods.min", item.get("paymethods", {}).get("min") if isinstance(item.get("paymethods"), dict) else None),
        ("paymethod.min", item.get("paymethod", {}).get("min") if isinstance(item.get("paymethod"), dict) else None),
        ("min_dep_flow", item.get("min_dep_flow")),
        ("default", item.get("default")),
    ]

    for source, raw_val in candidates:
        min_val = _to_float_safe(raw_val)
        if min_val is not None and min_val >= 0:
            return min_val, source

    return None, "none"
