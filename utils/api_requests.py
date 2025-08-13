import requests
import logging
from .helpers import extract_login_data  # Импорт из helpers.py

def get_payment_and_withdraw_systems(self):
    deposit_methods = []
    withdraw_methods = []
    deposit_names = []
    withdraw_names = []

    headers = {
        "User-Agent": self.user_agent,
        "Authorization": f"Bearer {self.auth_token}",
        "Accept": "application/json, text/plain, */*"
    }

    logging.info("Получение данных о депозитах")
    deposit_response = self.session.get(self.DEPOSIT_URL, headers=headers)

    if deposit_response.status_code == 200:
        deposit_data = deposit_response.json().get('data', [])
        for item in deposit_data:
            method_title = item.get("title")
            method_name = item.get("name")
            
            # Проверяем, есть ли поле recommended в paymethods
            recommended_status = item.get("paymethods", {}).get("recomended", {}).get("status", False)

            logging.info(f"Метод: {method_title}, Рекомендованный: {recommended_status}")

            if method_title:
                deposit_methods.append(method_title)
            if method_name:
                deposit_names.append(method_name)

    else:
        logging.error(f"Ошибка получения данных о депозитах: {deposit_response.status_code}")

    logging.info("Получение данных о выводах")
    withdraw_response = self.session.get(self.WITHDRAW_URL, headers=headers)

    if withdraw_response.status_code == 200:
        withdraw_data = withdraw_response.json().get('data', [])
        for item in withdraw_data:
            method_title = item.get("title")
            method_name = item.get("name")
            
            # Проверяем, есть ли поле recommended в paymethods
            recommended_status = item.get("paymethods", {}).get("recomended", {}).get("status", False)

            logging.info(f"Метод: {method_title}, Рекомендованный: {recommended_status}")

            if method_title:
                withdraw_methods.append(method_title)
            if method_name:
                withdraw_names.append(method_name)

    else:
        logging.error(f"Ошибка получения данных о выводах: {withdraw_response.status_code}")

    return deposit_methods, withdraw_methods, deposit_names, withdraw_names

