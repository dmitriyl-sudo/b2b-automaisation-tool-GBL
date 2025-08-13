import logging
from .base_extractor import BaseExtractor
from .min_deposit_extractor import compute_min_deposit  # уже есть импорт

class RollingExtractor(BaseExtractor):
    def __init__(self, login, password, user_agent=None, base_url=None):
        super().__init__(login, password, user_agent, base_url)

    def _inject_min_deposit(self, methods_list):
        """
        Пробегаемся по сырым items (как в твоём payload) и добавляем:
          - min_deposit (число)
          - min_source  ('min_dep_flow' | 'min' | 'range' | 'default' | 'not_deposit' | 'none')
          - currency    (если можно вытащить из paymethods.currency)
        Если структура элемента уже нормализована и нет paymethods — просто пропускаем.
        """
        out = []
        for item in methods_list or []:
            # стараемся не ломать исходный объект
            m = dict(item)

            # если доступны сырые поля paymethods — считаем минималку
            pm = (m.get("paymethods") or {}) if isinstance(m, dict) else {}
            try:
                min_val, src = compute_min_deposit(m)
                if min_val is not None:
                    m["min_deposit"] = min_val
                m["min_source"] = src

                # подтащим валюту (если в элементе нет своего поля currency)
                if "currency" not in m:
                    cur_block = pm.get("currency") or {}
                    cur_code = cur_block.get("code") or cur_block.get("currency")
                    if cur_code:
                        m["currency"] = cur_code
            except Exception as e:
                logging.exception("Ошибка расчёта min_deposit для метода: %s", e)

            out.append(m)
        return out

    def get_payment_and_withdraw_systems(self, current_geo: str):
        current_country = current_geo.split("_")[0]

        logging.info("Получение данных о депозитах")
        deposit_methods, deposit_names, recommended_deposit = self.fetch_methods(self.DEPOSIT_URL, current_country)
        # обогащаем минималкой
        deposit_methods = self._inject_min_deposit(deposit_methods)

        logging.info("Получение данных о выводах")
        withdraw_methods, withdraw_names, recommended_withdraw = self.fetch_methods(self.WITHDRAW_URL, current_country)
        # для withdraw тоже можно посчитать — compute_min_deposit вернёт 'not_deposit' и мы не сломаемся
        withdraw_methods = self._inject_min_deposit(withdraw_methods)

        recommended_methods = recommended_deposit.union(recommended_withdraw)

        return (
            deposit_methods,
            withdraw_methods,
            deposit_names,
            withdraw_names,
            self.currency,
            self.deposit_count,
            recommended_methods
        )
