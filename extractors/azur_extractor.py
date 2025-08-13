import logging
from .base_extractor import BaseExtractor

class AzurSlotExtractor(BaseExtractor):
    def __init__(self, login, password, user_agent=None, base_url=None):
        # Базовый URL может быть задан извне, но если нет — ставим дефолтный
        default_base = "https://azurslot.com/en"
        super().__init__(login, password, user_agent, base_url or default_base)

    def get_payment_and_withdraw_systems(self, current_geo: str):
        current_country = current_geo.split("_")[0]

        logging.info("🔍 Получение данных о депозитах")
        deposit_methods, deposit_names, recommended_deposit = self.fetch_methods(self.DEPOSIT_URL, current_country)

        logging.info("🔍 Получение данных о выводах")
        withdraw_methods, withdraw_names, recommended_withdraw = self.fetch_methods(self.WITHDRAW_URL, current_country)

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
