import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class RollingSlotsExtractor:
    BASE_URL = "https://rollingslots.com"
    LOGIN_URL = f"{BASE_URL}/api/v1/en/account/login"
    DEPOSIT_URL = f"{BASE_URL}/api/v1/en/model/paysystem/deposit"
    WITHDRAW_URL = f"{BASE_URL}/api/v1/en/model/paysystem/withdraw"

    def __init__(self, login: str, password: str, user_agent: str = None):
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.auth_token = None
        self.user_agent = user_agent or "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

    def authenticate(self) -> bool:
        payload = {
            "login": self.login,
            "password": self.password,
            "google_token": "",
            "facebook_token": ""
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{self.BASE_URL}/en/login",
            "Origin": self.BASE_URL,
            "X-Fingerprint": "3e67a7847f33cd293198f77ecab70b1f"
        }

        response = self.session.post(self.LOGIN_URL, json=payload, headers=headers)

        if response.status_code == 200:
            self.auth_token = response.json().get("token")
            logging.info("Авторизация прошла успешно")
            return True
        else:
            logging.error(f"Ошибка авторизации: {response.status_code} - {response.text}")
            return False

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
            deposit_methods = [item.get('title') for item in deposit_data if 'title' in item]
            deposit_names = [item.get('name') for item in deposit_data if 'name' in item]
            logging.info(f"Методы депозита: {deposit_methods}")
        else:
            logging.error(f"Ошибка получения данных о депозитах: {deposit_response.status_code}")

        logging.info("Получение данных о выводах")
        withdraw_response = self.session.get(self.WITHDRAW_URL, headers=headers)

        if withdraw_response.status_code == 200:
            withdraw_data = withdraw_response.json().get('data', [])
            withdraw_methods = [item.get('title') for item in withdraw_data if 'title' in item]
            withdraw_names = [item.get('name') for item in withdraw_data if 'name' in item]
            logging.info(f"Методы вывода: {withdraw_methods}")
        else:
            logging.error(f"Ошибка получения данных о выводах: {withdraw_response.status_code}")

        return deposit_methods, withdraw_methods, deposit_names, withdraw_names

if __name__ == "__main__":
    login = "deeur0dep"
    password = "123123123"

    extractor = RollingSlotsExtractor(login, password)

    if extractor.authenticate():
        deposit_methods, withdraw_methods, deposit_names, withdraw_names = extractor.get_payment_and_withdraw_systems()
        print("Методы депозита:", deposit_methods)
        print("Методы вывода:", withdraw_methods)
        print("Названия методов депозита:", deposit_names)
        print("Названия методов вывода:", withdraw_names)
    else:
        print("Не удалось авторизоваться")
