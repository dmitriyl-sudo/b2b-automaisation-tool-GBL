import json
import requests
import time
import argparse

BASE_URL = "https://rollingslots.com"
LOGIN_URL = f"{BASE_URL}/api/v1/en/account/login"
DEPOSIT_LIST_URL = f"{BASE_URL}/api/v1/en/model/paysystem/deposit?fields=images,name,title,display_type,show_amount,parent_paysystem,run_iframe,version&limit=100"
DEPOSIT_TEST_URL = f"{BASE_URL}/api/v1/en/payment/deposit"
ERROR_LOG_FILE = "error_report.txt"

geo_groups = {
    # "DE": ["0depnoaffdeeurmobi", "0depaffildeeurmobi", "0depaffildeeurdesk", "0depnoaffdeeurdesk", "4depaffildeeurmobi1"],
    # "IT": ["0depnoaffiteurmobi", "0depaffiliteurmobi", "0depaffiliteurdesk", "0depnoaffiteurdesk", "4depaffiliteurmobi1"],
    "AT": ["0depnoaffateurmobi", "0depaffilateurmobi", "0depaffilateurdesk", "0depnoaffateurdesk", "4depaffilateurmobi1"],
    "SE": ["0depnoaffseeurmobi", "0depaffilseeurmobi", "0depaffilseeurdesk", "0depnoaffseeurdesk", "4depaffilseeurmobi1"],
    # "GR": ["0depnoaffgreurmobi", "0depaffilgreurmobi", "0depaffilgreurdesk", "0depnoaffgreurdesk", "4depaffilgreurmobi1"],
    # "IE": ["0depnoaffieeurmobi", "0depaffilieeurmobi", "0depaffilieeurdesk", "0depnoaffieeurdesk", "4depaffilieeurmobi1"],
    # "ES": ["0depnoaffeseurmobi", "0depaffileseurmobi", "0depaffileseurdesk", "0depnoaffeseurdesk", "4depaffileseurmobi1"],
    # "PT": ["0depnoaffpteurmobi", "0depaffilpteurmobi", "0depaffilpteurdesk1", "0depnoaffpteurdesk", "4depaffilpteurmobi1"],
    # "FI": ["0depnoafffieurmobi", "0depaffilfieurmobi", "0depaffilfieurdesk", "0depnoafffieurdesk", "4depaffilfieurmobi1"],
    # "DK_DKK": ["0depnoaffdkdkkmobi", "0depaffildkdkkmobi", "0depaffildkdkkdesk", "0depnoaffdkdkkdesk", "4depaffildkdkkmobi1"],
    # "DK_EUR": ["0depnoaffdkeurmobi", "0depaffildkeurmobi", "0depaffildkeurdesk", "0depnoaffdkeurdesk", "4depaffildkeurmobi1"],
    # "PL_PLN": ["0depnoaffplplnmobi", "0depaffilplplnmobi", "0depaffilplplndesk", "0depnoaffplplndesk", "4depaffilplplnmobi1"],
    # "PL_EUR": ["0depnoaffpleurmobi", "0depaffilpleurmobi", "0depaffilpleurdesk", "0depnoaffpleurdesk", "4depaffilpleurmobi1"],
    # "CH_CHF": ["0depnoaffchchfmobi", "0depaffilchchfmobi", "0depaffilchchfdesk", "0depnoaffchchfdesk", "4depaffilchchfmobi1"],
    # "CH_EUR": ["0depnoaffcheurmobi", "0depaffilcheurmobi", "0depaffilcheurdesk", "0depnoaffcheurdesk", "4depaffilcheurmobi1"],
    # "NO_NOK": ["0depnoaffnonokmobi", "0depaffilnonokmobi", "0depaffilnonokdesk", "0depnoaffnonokdesk", "4depaffilnonokmobi1"],
    # "NO_EUR": ["0depnoaffnoeurmobi", "0depaffilnoeurmobi", "0depaffilnoeurdesk", "0depnoaffnoeurdesk", "4depaffilnoeurmobi1"],
    # "HU_HUF": ["0depnoaffhuhufmobi", "0depaffilhuhufmobi", "0depaffilhuhufdesk", "0depnoaffhuhufdesk", "4depaffilhuhufmobi1"],
    # "HU_EUR": ["0depnoaffhueurmobi", "0depaffilhueurmobi", "0depaffilhueurdesk", "0depnoaffhueurdesk", "4depaffilhueurmobi1"],
    # "AU_AUD": ["0depnoaffauaudmobi1", "0depaffilauaudmobi1", "0depaffilauauddesk1", "0depnoaffauauddesk1", "4depaffilauaudmobi1"],
    # "CA_CAD": ["0depnoaffcacadmobi", "0depaffilcacadmobi", "0depaffilcacaddesk", "0depnoaffcacaddesk", "4depaffilcacadmobi1"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/en/account/dashboard"
}


def authenticate(session, login, password):
    payload = {
        "login": login,
        "password": password,
        "google_token": "",
        "facebook_token": ""
    }
    res = session.post(LOGIN_URL, json=payload, headers=HEADERS)
    if res.status_code != 200:
        print("❌ Auth failed")
        return None, None
    print("✅ Auth successful")

    try:
        email = res.json().get("email") or res.json().get("profile", {}).get("email")
        return session, email
    except Exception as e:
        print("⚠️ Failed to extract email:", e)
        return session, None


def get_deposit_methods(session):
    res = session.get(DEPOSIT_LIST_URL, headers=HEADERS)
    if res.status_code != 200:
        print("❌ Failed to fetch deposit methods")
        return []
    return res.json().get("data", [])


def test_payment_methods(session, methods, currency, email, login, error_log_file):
    success_count = 0
    total_tested = 0

    for item in methods:
        title = item.get("title")
        name = item.get("name")
        alias = item.get("alias")
        version = item.get("version")
        paymethod_code = item.get("paymethods", {}).get("paymethod", {}).get("name")
        method_currency = item.get("paymethods", {}).get("currency", {}).get("currency", currency)
        paysystem_name = item.get("paymethods", {}).get("paysystem", {}).get("name", "").lower()

        # фильтруем лишние
        if "crypto" in paysystem_name or "coin" in paysystem_name:
            if "binance" not in paysystem_name:
                continue

        if not all([alias, paymethod_code]):
            print(f"⚠️ Пропущен метод {title} | {name} — нет alias или paymethod")
            continue

        total_tested += 1

        # определяем сумму
        if "dimoco" in paysystem_name:
            amount_to_use = 45
        elif "siru" in paysystem_name:
            amount_to_use = 15
        else:
            amount_to_use = 250

        # базовый payload
        payload = {
            "amount": amount_to_use,
            "currency": method_currency,
            "paymethod": paymethod_code,
            "fields": {
                "phonemail": email
            },
            "alias": alias,
            "version": version
        }

        if "ezeewallet" in name.lower():
            payload["fields"] = {
                "email": "dmitriy.l@gbl-factory.com",
                "password": "!!Vitya1406__"
            }

        # лог запроса
        print(f"\n🔍 Testing method: {title} | {name} | paysystem: {paysystem_name}")
        print("📤 Payload:")
        print(json.dumps(payload, indent=2))

        try:
            res = session.post(DEPOSIT_TEST_URL, json=payload, headers=HEADERS)
            print(f"📨 Status: {res.status_code}")

            result = res.json()
            if res.status_code == 200 and result.get("url"):
                print(f"✅ Passed: {result.get('url')[:70]}...\n")
                success_count += 1
            else:
                message = result.get("message", "No message")
                print(f"❌ Failed: {message}")
                with open(error_log_file, "a", encoding="utf-8") as f:
                    f.write(f"{login} | {name} | {res.status_code} | {message}\n")
        except Exception as e:
            print(f"⚠️ Exception occurred: {e}")
            with open(error_log_file, "a", encoding="utf-8") as f:
                f.write(f"{login} | {name} | EXCEPTION | {str(e)}\n")

        time.sleep(0.5)

    print(f"\n🏁 Finished: {success_count}/{total_tested} methods passed (excluding skipped)")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--password", default="123123123")
    parser.add_argument("--currency", default="EUR")
    args = parser.parse_args()

    # Очистим лог перед началом
    with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    for geo, logins in geo_groups.items():
        print(f"🌍 GEO: {geo}")
        for login in logins:
            print(f"🔐 Testing login: {login}")
            session = requests.Session()
            session, user_email = authenticate(session, login, args.password)
            if session and user_email:
                methods = get_deposit_methods(session)
                test_payment_methods(session, methods, args.currency, user_email, login, ERROR_LOG_FILE)
            else:
                with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{login} | AUTH ERROR | Unable to authenticate or extract email\n")
