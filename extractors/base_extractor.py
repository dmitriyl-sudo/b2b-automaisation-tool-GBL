# base_extractor.py
import requests
import logging

class BaseExtractor:
    def __init__(self, login, password, user_agent=None, base_url=None):
        if not base_url:
            raise ValueError("base_url должен быть передан в конструктор!")

        self.login = login
        self.password = password
        self.base_url = base_url
        self.user_agent = user_agent or "Mozilla/5.0"
        self.session = requests.Session()
        self.auth_token = None
        self.currency = None
        self.deposit_count = None

        self.LOGIN_URL = f"{self.base_url}/api/v1/en/account/login"
        self.DEPOSIT_URL = f"{self.base_url}/api/v1/en/model/paysystem/deposit"
        self.WITHDRAW_URL = f"{self.base_url}/api/v1/en/model/paysystem/withdraw"

    def authenticate(self):
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
            "Referer": f"{self.base_url}/en/login",
            "Origin": self.base_url,
            "X-Fingerprint": "some_fingerprint_value"
        }

        response = self.session.post(self.LOGIN_URL, json=payload, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                self.auth_token = data.get("token") or response.cookies.get("__token")
                self.currency = data.get("currency")
                self.deposit_count = data.get("profile", {}).get("deposit_count") or data.get("data", {}).get("deposit_count")
                logging.info("Авторизация успешна")
                return True
            except Exception as e:
                logging.error(f"Ошибка разбора ответа: {e}")
                return False
        logging.error(f"Ошибка авторизации: {response.status_code}")
        return False

    def fetch_methods(self, url, current_country):
        methods = []
        names = []
        recommended = set()
        headers = {
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json, text/plain, */*"
        }
        page = 1
        while True:
            response = self.session.get(f"{url}?page={page}", headers=headers)
            if response.status_code != 200:
                break
            data = response.json().get("data", [])
            if not data:
                break
            for item in data:
                title = item.get("title")
                name = item.get("name")
                rec_info = item.get("paymethods", {}).get("recomended", {})
                if rec_info.get("status") and (not rec_info.get("countries") or current_country in rec_info["countries"]):
                    if title and name:
                        recommended.add((title, name))
                if title:
                    methods.append(title)
                if name:
                    names.append(name)
            page += 1
        return methods, names, recommended
