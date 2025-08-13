import re

def extract_login_data(login_data: str):
    """
    Извлекает данные из строки логина:
    - dep_id: первые 9 символов
    - geo: символы 10-11
    - currency: символы 12-14
    - device: символы 15-18
    """
    pattern = r"(.{9})(.{2})(.{3})(.{4})"
    match = re.match(pattern, login_data)
    if match:
        dep_id = match.group(1)
        geo = match.group(2)
        currency = match.group(3)
        device = match.group(4)
        return dep_id, geo, currency, device
    else:
        raise ValueError("Не удалось сопоставить строку с шаблоном.")

def normalize_method(method: str) -> str:
    """
    Удаляет лишние пробелы в названии платежного метода.
    """
    return " ".join(method.split())