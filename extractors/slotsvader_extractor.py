# extractors/slotsvader_extractor.py
from typing import List, Tuple, Set, Dict, Any, Optional
import logging

from .base_extractor import BaseExtractor
from .min_deposit_extractor import compute_min_deposit


class SlotsVaderExtractor(BaseExtractor):
    """
    Экстрактор для SlotsVader:
    - Авторизация через BaseExtractor (currency/deposit_count подтягиваются из ответа логина).
    - Депозиты тянем с return_raw=True и считаем min_deposit для каждой пары (title, name).
    - Recommended берём ТОЛЬКО из депозита (как в Rolling).
    - ВНИМАНИЕ: запретные GEO игнорируем и ничего не тянем (см. списки ниже).
    """

    DEPOSIT_URL: str  = "/api/v1/model/paysystem/deposit"
    WITHDRAW_URL: str = "/api/v1/model/paysystem/withdraw"

    # --- Запретные GEO (hardcode по задаче) ---
    # Имена, которые пришли от тебя: Australia, Austria, Comoros, France,
    # Germany, Netherlands, Spain, United Kingdom, USA.
    # Маппим их на ISO-коды:
    FORBIDDEN_GEO_CODES = {
        "AU",  # Australia
        "AT",  # Austria
        "KM",  # Comoros
        "FR",  # France
        "DE",  # Germany
        "NL",  # Netherlands
        "ES",  # Spain
        "GB",  # United Kingdom (официальный код GB)
        "UK",  # На всякий случай, если ключ в geo будет UK
        "US",  # USA
        "GR",  # Greece
        "HU"   # Hungary
    } 

    # FATF-blacklist (поддержка флажка; список можно расширять при необходимости)
    # Оставляю наиболее частые ISO-коды (без претензии на актуальность):
    FATF_BLACKLIST_CODES = {
        "KP",  # DPRK (North Korea)
        "IR",  # Iran
        "MM",  # Myanmar
        # при необходимости дополняй
    }

    @staticmethod
    def _norm_geo_code(geo: str) -> str:
        """
        Из строки вида 'DE_prod' -> 'DE'. Из 'uk' -> 'UK'. Из 'United Kingdom' -> 'GB'.
        """
        if not geo:
            return ""
        head = str(geo).split("_", 1)[0].strip()
        # Если это уже код (2 буквы) — нормализуем в верхний регистр
        if len(head) in (2, 3):  # иногда встречаются 'UK'/'GB'/'USA'
            code = head.upper()
            if code == "UK":
                return "GB"  # нормализуем UK -> GB
            if code == "USA":
                return "US"
            return code

        # Если это имя страны прописью — приведём к коду по хардкоду
        name = head.lower()
        mapping = {
            "greece" : "GR",
            "australia": "AU",
            "austria": "AT",
            "comoros": "KM",
            "france": "FR",
            "germany": "DE",
            "netherlands": "NL",
            "spain": "ES",
            "united kingdom": "GB",
            "uk": "GB",
            "great britain": "GB",
            "usa": "US",
            "united states": "US",
            "united states of america": "US",
            "hungary" : "HU"
        }
        return mapping.get(name, head.upper())

    @classmethod
    def is_geo_forbidden_static(cls, current_geo: str) -> bool:
        code = cls._norm_geo_code(current_geo)
        if not code:
            return False
        return (code in cls.FORBIDDEN_GEO_CODES) or (code in cls.FATF_BLACKLIST_CODES)

    # Инстансовый алиас (удобно вызывать из готового объекта)
    def is_geo_forbidden(self, current_geo: str) -> bool:
        return self.is_geo_forbidden_static(current_geo)

    def __init__(self, login, password, user_agent: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(base_url, login, password, user_agent)

    def get_payment_and_withdraw_systems(self, current_geo: str) -> Tuple[
        List[Dict[str, Any]],  # deposit_enriched: [{'title','name','min_deposit','currency','min_source'}, ...]
        List[str],             # withdraw titles
        List[str],             # deposit names (для совместимости)
        List[str],             # withdraw names
        Optional[str],         # currency
        int,                   # deposit_count
        Set[Tuple[str, str]]   # recommended {(title, name), ...}
    ]:
        # --- Главное: если GEO запрещён — тихо пропускаем ---
        if self.is_geo_forbidden(current_geo):
            logging.warning(f"[SlotsVader] GEO '{current_geo}' запрещён — пропускаем без запросов.")
            return ([], [], [], [], self.currency, 0, set())

        country = (current_geo or "").split("_")[0]

        logging.info("[SlotsVader] Fetching DEPOSIT methods")
        dep_titles, dep_names, rec_dep, dep_raw = self.fetch_methods(
            self.DEPOSIT_URL, country, return_raw=True
        )

        logging.info("[SlotsVader] Fetching WITHDRAW methods")
        wd_titles, wd_names, _rec_wd, _ = self.fetch_methods(
            self.WITHDRAW_URL, country, return_raw=True
        )

        # Обогащаем депозиты минимумами
        deposit_enriched: List[Dict[str, Any]] = []
        for item in dep_raw or []:
            try:
                title = (item.get("title") or item.get("alias") or item.get("name") or "").strip()
                pm = item.get("paymethods") or {}
                pm_pay = pm.get("paymethod") or {}

                name = (
                    item.get("name")
                    or pm_pay.get("name")
                    or pm_pay.get("code")
                    or item.get("doc_id")
                    or ""
                ).strip()
                if not title or not name:
                    continue

                min_val, source = compute_min_deposit(item)
                cur = ((pm.get("currency") or {}).get("code")) or self.currency

                deposit_enriched.append({
                    "title": title,
                    "name": name,
                    "min_deposit": float(min_val) if min_val is not None else None,
                    "currency": cur,
                    "min_source": source,
                })
            except Exception:
                # не валимся на единичных кривых записях
                continue

        # Рекомендации — только из депозита
        recommended_methods: Set[Tuple[str, str]] = set(rec_dep)

        return (
            deposit_enriched,
            wd_titles,
            dep_names,
            wd_names,
            self.currency,
            self.deposit_count,
            recommended_methods,
        )
