import logging
from typing import List, Tuple, Set, Dict, Any, Optional

from .base_extractor import BaseExtractor
from .min_deposit_extractor import compute_min_deposit


class RollingExtractor(BaseExtractor):
    """
    Экстрактор для Rolling:
    - тянем сырые депозиты с return_raw=True
    - считаем min_deposit для каждой депозитной пары
    - ⭐ recommended берём ТОЛЬКО из депозита (как раньше)
    """


    def __init__(self, login, password, user_agent=None, base_url=None):
        super().__init__(base_url, login, password, user_agent)

    def get_payment_and_withdraw_systems(self, current_geo: str):
        current_country = current_geo.split("_")[0]

        logging.info("Получение данных о депозитах")
        dep_titles, dep_names, rec_dep, dep_raw = self.fetch_methods(
            self.DEPOSIT_URL, current_country, return_raw=True
        )

        logging.info("Получение данных о выводах")
        wd_titles, wd_names, rec_wd, _ = self.fetch_methods(
            self.WITHDRAW_URL, current_country, return_raw=True
        )

        # ── обогащаем депозиты min_deposit
        deposit_enriched: List[Dict[str, Any]] = []
        for item in dep_raw or []:
            try:
                title = (item.get("title") or item.get("alias") or item.get("name") or "").strip()
                pm = item.get("paymethods") or {}
                pm_pay = pm.get("paymethod") or {}
                name = (item.get("name") or pm_pay.get("name") or pm_pay.get("code") or "").strip()
                if not title or not name:
                    continue

                min_val, source = compute_min_deposit(item)
                currency = ((pm.get("currency") or {}).get("code")) or self.currency

                deposit_enriched.append({
                    "title": title,
                    "name": name,
                    "min_deposit": float(min_val) if min_val is not None else None,
                    "currency": currency,
                    "min_source": source,
                })
            except Exception:
                # не падаем на отдельной записи
                continue

        # ⭐ только депозитные рекомендации (никакого union)
        recommended_methods: Set[Tuple[str, str]] = set(rec_dep)

        # возвращаем в прежнем контракте
        return (
            deposit_enriched,      # вместо списка титулов — обогащённый список dict'ов
            wd_titles,             # withdraw titles (как раньше)
            dep_names,             # не используется фронтом, но оставляем для совместимости
            wd_names,
            self.currency,
            self.deposit_count,
            recommended_methods
        )
