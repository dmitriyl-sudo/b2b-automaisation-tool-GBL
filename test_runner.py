import requests
import time
from main import geo_groups, site_list

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json"
}

def run_payment_method_tests(project: str, geo: str, login: str, mode: str, env: str = "prod"):
    site = next((s for s in site_list if s["name"] == project), None)
    if not site:
        return [{"geo": geo, "login": login, "method": "-", "status": "FAIL", "code": 400, "message": "Unknown project"}]

    base_url = site["stage_url"] if env == "stage" else site["prod_url"]

    LOGIN_URL = f"{base_url}/api/v1/en/account/login"
    DEPOSIT_LIST_URL = f"{base_url}/api/v1/en/model/paysystem/deposit?fields=images,name,title,display_type,show_amount,parent_paysystem,run_iframe,version&limit=100"
    DEPOSIT_TEST_URL = f"{base_url}/api/v1/en/payment/deposit"
    HEADERS["Origin"] = base_url
    HEADERS["Referer"] = f"{base_url}/en/account/dashboard"

    if mode == "login":
        logins_to_check = [login]
    elif mode == "geo":
        logins_to_check = geo_groups.get(geo, [])
    elif mode == "project":
        logins_to_check = [login for logins in geo_groups.values() for login in logins]
    else:
        return []

    results = []

    for login in logins_to_check:
        session = requests.Session()
        email = None
        try:
            auth = session.post(LOGIN_URL, json={"login": login, "password": "123123123"}, headers=HEADERS)
            if auth.status_code != 200:
                results.append({
                    "geo": geo, "login": login, "method": "-", "status": "FAIL",
                    "code": 401, "message": "Auth failed"
                })
                continue
            email = auth.json().get("email") or auth.json().get("profile", {}).get("email")
        except Exception as e:
            results.append({
                "geo": geo, "login": login, "method": "-", "status": "FAIL",
                "code": 500, "message": f"Auth exception: {str(e)}"
            })
            continue

        try:
            r = session.get(DEPOSIT_LIST_URL, headers=HEADERS)
            r.raise_for_status()
            methods = r.json().get("data", [])
        except Exception as e:
            results.append({
                "geo": geo, "login": login, "method": "-", "status": "FAIL",
                "code": r.status_code if 'r' in locals() and r else 500,
                "message": f"Failed to fetch methods: {str(e)} | Raw: {getattr(r, 'text', 'no response')}"
            })
            continue

        for item in methods:
            name = item.get("name")
            alias = item.get("alias")
            version = item.get("version")
            paymethod_code = item.get("paymethods", {}).get("paymethod", {}).get("name")
            method_currency = item.get("paymethods", {}).get("currency", {}).get("currency", "EUR")
            paysystem_name = item.get("paymethods", {}).get("paysystem", {}).get("name", "").lower()

            if "crypto" in paysystem_name or "coin" in paysystem_name:
                if "binance" not in paysystem_name:
                    continue

            if not alias or not paymethod_code:
                continue

            if "dimoco" in paysystem_name:
                amount_to_use = 45
            elif "siru" in paysystem_name:
                amount_to_use = 15
            elif "cashlib" in paysystem_name.lower():
                amount_to_use = 100
            else:
                amount_to_use = 250

            fields = {"phonemail": email}
            if "ezeewallet" in name.lower():
                fields.update({
                    "email": "dmitriy.l@gbl-factory.com",
                    "password": "!!Vitya1406__"
                })

            payload = {
                "amount": amount_to_use,
                "currency": method_currency,
                "paymethod": paymethod_code,
                "fields": fields,
                "alias": alias,
                "version": version
            }

            try:
                start_time = time.perf_counter()
                r = session.post(DEPOSIT_TEST_URL, json=payload, headers=HEADERS)
                duration = round(time.perf_counter() - start_time, 2)

                result_json = r.json()
                payment_url = result_json.get("url") or result_json.get("redirect_url") or None

                if r.status_code == 200 and payment_url:
                    results.append({
                        "geo": geo,
                        "login": login,
                        "method": name,
                        "status": "OK",
                        "code": 200,
                        "message": "OK",
                        "duration": duration,
                        "url": payment_url
                    })
                else:
                    msg = result_json.get("message", r.text)
                    results.append({
                        "geo": geo,
                        "login": login,
                        "method": name,
                        "status": "FAIL",
                        "code": r.status_code,
                        "message": msg,
                        "duration": duration,
                        "url": payment_url
                    })
            except Exception as e:
                results.append({
                    "geo": geo,
                    "login": login,
                    "method": name,
                    "status": "FAIL",
                    "code": 500,
                    "message": f"Exception during deposit: {str(e)}"
                })

            time.sleep(0.5)

    return results
