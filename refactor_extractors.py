import os
import re

# Папка, где лежат экстракторы
extractors_dir = "extractors"

# Преобразует snake_case или склеенные имена в CamelCase
def snake_to_camel(name):
    # Делит по числам, нижним подчёркиваниям и смене слова (напр. needforspin -> need for spin)
    parts = re.findall(r'[A-Za-z][^A-Z_]*', name)
    return ''.join(part.capitalize() for part in parts)

# Шаблон содержимого экстрактора
template = '''
import logging
from .base_extractor import BaseExtractor

class {class_name}(BaseExtractor):
    def __init__(self, login, password, user_agent=None, base_url=None):
        super().__init__(login, password, user_agent, base_url)

    def get_payment_and_withdraw_systems(self, current_geo: str):
        current_country = current_geo.split("_")[0]

        logging.info("Получение данных о депозитах")
        deposit_methods, deposit_names, recommended_deposit = self.fetch_methods(self.DEPOSIT_URL, current_country)

        logging.info("Получение данных о выводах")
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
'''

# Проходим по каждому экстрактору
for filename in os.listdir(extractors_dir):
    if filename.endswith("_extractor.py") and filename != "base_extractor.py":
        base = filename.replace("_extractor.py", "")
        class_name = snake_to_camel(base) + "Extractor"
        filepath = os.path.join(extractors_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template.format(class_name=class_name))

        print(f"✅ Обновлён: {filename} → class {class_name}")
