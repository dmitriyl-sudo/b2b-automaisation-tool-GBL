from typing import Any, Dict, Optional, Tuple

def _to_float(x: Any) -> Optional[float]:
    try:
        if x is None or (isinstance(x, str) and not x.strip()):
            return None
        return float(x)
    except Exception:
        return None

def _min_from_range(range_str: Any) -> Optional[float]:
    if not isinstance(range_str, str) or not range_str.strip():
        return None
    nums = []
    for part in range_str.split(","):
        v = _to_float(part.strip())
        if v is not None:
            nums.append(v)
    return min(nums) if nums else None

def compute_min_deposit(method: Dict[str, Any]) -> Tuple[Optional[float], str]:
    """
    method — один элемент из массива data[*] (как ты прислал).
    Возвращает (min_value, source), где source указывает из какого поля взяли минималку.
    Алгоритм:
      1) min_dep_flow
      2) min
      3) range (минимум из списка)
      4) default
    Только для operation_type == "deposit".
    """
    pm = (method or {}).get("paymethods") or {}
    if (pm.get("operation_type") or "").lower() != "deposit":
        return (None, "not_deposit")

    v = _to_float(pm.get("min_dep_flow"))
    if v is not None:
        return (v, "min_dep_flow")

    v = _to_float(pm.get("min"))
    if v is not None:
        return (v, "min")

    v = _min_from_range(pm.get("range"))
    if v is not None:
        return (v, "range")

    v = _to_float(pm.get("default"))
    if v is not None:
        return (v, "default")

    return (None, "none")
