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
    
    def _is_crypto_method(self, title: str, name: str) -> bool:
        """Определяет является ли метод криптовалютой (НЕ включая Jeton и Binance Pay)"""
        # Jeton и Binance Pay НЕ должны группироваться с криптовалютами!
        title_lower = (title or "").strip().lower()
        if title_lower in ["jeton", "binance pay"]:
            return False
            
        # Проверяем по названию (name) - исключаем Jeton и Binance
        import re
        # Исключаем Binance из проверки на Crypto
        if "binance" in (name or "").lower():
            return False
            
        crypto_pattern = r"Coinspaid|Crypto|Tether|Bitcoin|Ethereum|Litecoin|Ripple|Tron|USDC|USDT|DOGE|Cardano|Solana|Toncoin"
        if re.search(crypto_pattern, name or "", re.IGNORECASE):
            return True
            
        # Проверяем по title
        if title_lower == "crypto":
            return True
            
        # Дополнительные префиксы криптовалют (НЕ включая jeton и binance)
        crypto_prefixes = ["btc", "eth", "ltc", "xrp", "trx", "usdt", "usdc", "sol", "ada", "bch", "ton", "doge"]
        if any(title_lower.startswith(prefix) for prefix in crypto_prefixes):
            return True
            
        return False

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

        # ── Обрабатываем методы СОХРАНЯЯ API ПОРЯДОК
        all_processed_methods: List[Dict[str, Any]] = []
        crypto_methods = []
        
        # Сначала обрабатываем ВСЕ методы сохраняя порядок
        for item in dep_raw or []:
            try:
                title = (item.get("title") or item.get("alias") or item.get("name") or "").strip()
                pm = item.get("paymethods") or {}
                pm_pay = pm.get("paymethod") or {}
                name = (item.get("name") or pm_pay.get("name") or pm_pay.get("code") or "").strip()
                display_type = item.get("display_type", "")
                parent_paysystem = item.get("parent_paysystem", "")
                
                if not title or not name:
                    continue

                min_val, source = compute_min_deposit(item)
                currency = ((pm.get("currency") or {}).get("code")) or self.currency

                method_data = {
                    "title": title,
                    "name": name,
                    "min_deposit": float(min_val) if min_val is not None else None,
                    "currency": currency,
                    "min_source": source,
                    "display_type": display_type,
                    "parent_paysystem": parent_paysystem,
                    "api_position": len(all_processed_methods)  # Сохраняем API позицию!
                }

                # Определяем тип метода
                is_crypto_by_name = self._is_crypto_method(title, name)
                is_special_method = title in ["Jeton", "Binance Pay"]
                
                if parent_paysystem == "Crypto" or is_crypto_by_name:
                    method_data["method_type"] = "crypto"
                    crypto_methods.append(method_data)
                elif display_type == "in" and title != "Crypto" and not is_special_method:
                    method_data["method_type"] = "hidden"
                    crypto_methods.append(method_data)
                else:
                    method_data["method_type"] = "visible"
                
                all_processed_methods.append(method_data)
                    
            except Exception as e:
                logging.warning(f"Ошибка обработки метода: {e}")
                continue
        
        # Теперь формируем финальный список СОХРАНЯЯ ПОРЯДОК
        deposit_enriched: List[Dict[str, Any]] = []
        for method in all_processed_methods:
            if method["method_type"] == "visible":
                deposit_enriched.append(method)

        # Если есть криптовалюты, добавляем их как один "Crypto" метод
        if crypto_methods:
            # Ищем основной Crypto метод
            crypto_main = None
            for method in deposit_enriched:
                if method["title"] == "Crypto":
                    crypto_main = method
                    break
            
            if not crypto_main:
                # Создаем основной Crypto метод если его нет
                crypto_main = {
                    "title": "Crypto",
                    "name": "Crypto",
                    "min_deposit": 50.0,  # Стандартный минимум для крипто
                    "currency": self.currency,
                    "min_source": "default",
                    "display_type": "in",
                    "parent_paysystem": "",
                }
                deposit_enriched.append(crypto_main)

        logging.info(f"Обработано методов: {len(deposit_enriched)} (было {len(dep_raw or [])})")
        logging.info(f"Криптовалют сгруппировано: {len(crypto_methods)}")

        # ⭐ только депозитные рекомендации (никакого union)
        recommended_methods: Set[Tuple[str, str]] = set(rec_dep)

        # возвращаем в прежнем контракте
        return (
            deposit_enriched,      # обогащённый и отфильтрованный список
            wd_titles,             # withdraw titles (как раньше)
            dep_names,             # не используется фронтом, но оставляем для совместимости
            wd_names,
            self.currency,
            len(deposit_enriched), # обновленный счетчик
            recommended_methods
        )
