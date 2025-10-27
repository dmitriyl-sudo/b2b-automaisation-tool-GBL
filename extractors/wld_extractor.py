# extractors/wld_extractor.py
from typing import List, Tuple, Set, Dict, Any, Optional
import logging

from .base_extractor import BaseExtractor
from .min_deposit_extractor import compute_min_deposit


class WildTokyoExtractor(BaseExtractor):
    """
    Экстрактор для WildTokyo:
    - авторизация через BaseExtractor (currency/deposit_count подтягиваются из ответа логина);
    - депозиты берём с return_raw=True и считаем min_deposit на каждую пару (title, name);
    - recommended берём ТОЛЬКО из депозита;
    - базовые пути без /en; при 404/вариациях BaseExtractor сам подберёт рабочий endpoint.
    - 🎯 ОБЯЗАТЕЛЬНО добавляем Binance Pay если его нет в API
    """

    DEPOSIT_URL: str  = "/api/v1/model/paysystem/deposit"
    WITHDRAW_URL: str = "/api/v1/model/paysystem/withdraw"

    def __init__(self, login, password, user_agent: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(base_url, login, password, user_agent)

    def _add_binance_pay_if_missing(self, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Добавляет Binance Pay если его нет в методах"""
        # Проверяем есть ли уже Binance Pay
        has_binance = any(
            method.get("title", "").lower() == "binance pay" or 
            "binance" in method.get("name", "").lower()
            for method in methods
        )
        
        if not has_binance:
            logging.info("🎯 [WildTokyo] Добавляем Binance Pay - отсутствует в API")
            binance_method = {
                "title": "Binance Pay",
                "name": "Binancepay_Binancepay_Crypto",
                "min_deposit": 50.0,
                "currency": self.currency or "CHF",
                "min_source": "default_binance",
            }
            methods.append(binance_method)
            logging.info(f"✅ [WildTokyo] Binance Pay добавлен на позицию {len(methods)}")
        else:
            logging.info("✅ [WildTokyo] Binance Pay уже присутствует в методах")
        
        return methods

    def get_payment_and_withdraw_systems(self, current_geo: str) -> Tuple[
        List[Dict[str, Any]],  # deposit_enriched: [{'title','name','min_deposit','currency','min_source'}, ...]
        List[str],             # withdraw titles
        List[str],             # deposit names (для совместимости)
        List[str],             # withdraw names
        Optional[str],         # currency
        int,                   # deposit_count
        Set[Tuple[str, str]]   # recommended {(title, name), ...}
    ]:
        country = (current_geo or "").split("_")[0]

        logging.info("[WildTokyo] Fetching DEPOSIT methods")
        dep_titles, dep_names, rec_dep, dep_raw = self.fetch_methods(
            self.DEPOSIT_URL, country, return_raw=True
        )

        logging.info("[WildTokyo] Fetching WITHDRAW methods")
        wd_titles, wd_names, _rec_wd, _ = self.fetch_methods(
            self.WITHDRAW_URL, country, return_raw=True
        )

        # Обогащаем депозиты минимумом
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

        # 🎯 ОБЯЗАТЕЛЬНО добавляем Binance Pay если его нет
        deposit_enriched = self._add_binance_pay_if_missing(deposit_enriched)

        # Рекомендации — только из депозита
        recommended_methods: Set[Tuple[str, str]] = set(rec_dep)

        # Проверяем что Binance Pay точно есть
        binance_count = sum(1 for method in deposit_enriched 
                          if method.get("title", "").lower() == "binance pay" or 
                             "binance" in method.get("name", "").lower())
        logging.info(f"[WildTokyo] Binance Pay методов найдено: {binance_count}")

        return (
            deposit_enriched,
            wd_titles,
            dep_names,
            wd_names,
            self.currency,
            len(deposit_enriched),  # Обновленный счетчик с Binance Pay
            recommended_methods,
        )
