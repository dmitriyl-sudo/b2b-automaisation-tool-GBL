# extractors/base_extractor.py
import requests
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Union

class BaseExtractor:
    """
    Базовый экстрактор: сессия, заголовки, авторизация, универсальный fetch_methods().
    Дочерние классы могут переопределить LOGIN_URL/DEPOSIT_URL/WITHDRAW_URL
    или authenticate(), если у проекта иной формат.
    """

    # ✅ ДЕФОЛТЫ БЕЗ /en
    LOGIN_URL: str    = "/api/v1/account/login"
    DEPOSIT_URL: str  = "/api/v1/model/paysystem/deposit"
    WITHDRAW_URL: str = "/api/v1/model/paysystem/withdraw"

    def __init__(self, base_url: str, login: str, password: Union[str, Dict[str, str]], user_agent: Optional[str] = None):
        # Добавляем https:// если протокол отсутствует
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
        self.base_url = base_url.rstrip("/")
        self.login = login
        self.password = password

        self.session = requests.Session()
        self.headers: Dict[str, str] = {"Accept": "application/json"}
        
        # Определяем мобильную эмуляцию по наличию 'mobi' в логине
        if 'mobi' in login.lower():
            self.headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            logging.info(f"[{login}] Using mobile User-Agent for 'mobi' login")
        elif user_agent:
            self.headers["User-Agent"] = user_agent

        self.currency: Optional[str] = None
        self.deposit_count: int = 0

        # Кэш успешно найденных путей, чтобы не перебирать каждый раз
        self._resolved_endpoints: Dict[str, str] = {}   # {"deposit": "/api/..", "withdraw": "/api/.."}

    def _full_url(self, url: str) -> str:
        if not url:
            return self.base_url
        return url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"

    # ---------- Вытаскиваем поля из ответа логина ----------
    def _harvest_from_login_json(self, j: Dict[str, Any]) -> None:
        """
        Пытаемся вытащить currency и deposit_count из распространённых мест
        ответа логина. Ничего не ломаем, если полей нет.
        """
        try:
            candidates = [
                j or {},
                j.get("data", {}) if isinstance(j, dict) else {},
                j.get("user", {}) if isinstance(j, dict) else {},
                j.get("account", {}) if isinstance(j, dict) else {},
                j.get("profile", {}) if isinstance(j, dict) else {},
            ]

            # currency
            for d in candidates:
                cur = (
                    d.get("currency")
                    or d.get("currencyISO")
                    or d.get("currencyIso")
                    or d.get("currency_code")
                    or d.get("currencyCode")
                )
                if isinstance(cur, str) and cur.strip():
                    self.currency = cur.strip().upper()
                    break

            # deposit_count - ищем в разных полях
            for d in candidates:
                dc = (
                    d.get("deposit_count")
                    or d.get("depositCount") 
                    or d.get("deposits")
                    or d.get("balance")
                    or d.get("deposit_balance")
                    or d.get("depositBalance")
                    or d.get("real_balance")
                    or d.get("realBalance")
                    or d.get("money")
                    or d.get("amount")
                )
                if isinstance(dc, (int, float)):
                    self.deposit_count = int(dc)
                    logging.debug(f"[auth] Found deposit_count: {self.deposit_count} from field in {d}")
                    break
                elif isinstance(dc, str) and dc.replace('.', '').replace(',', '').isdigit():
                    self.deposit_count = int(float(dc.replace(',', '.')))
                    logging.debug(f"[auth] Found deposit_count: {self.deposit_count} from string field in {d}")
                    break
        except Exception as e:
            logging.debug(f"[auth] harvest login json issue: {e}")

    def authenticate(self) -> bool:
        """
        Пробуем логиниться без /en, если не вышло — с /en.
        Если пароля нет — не падаем, продолжаем (некоторые сайты отдают методы без логина).
        Дополнительно забираем currency / deposit_count прямо из JSON-ответа логина.
        """
        try:
            pwd = self.password.get(self.login) if isinstance(self.password, dict) else self.password
            if not pwd:
                logging.warning(f"[auth] Пароль не найден для '{self.login}'. Продолжаем без авторизации.")
                logging.info("Авторизация успешна")
                return True

            # кандидаты: без /en (дефолт) → с /en (fallback)
            preferred = self._full_url(getattr(self, "LOGIN_URL", "/api/v1/account/login"))
            alt = self._full_url("/api/v1/en/account/login")
            for url in [preferred, alt] if alt != preferred else [preferred]:
                try:
                    resp = self.session.post(
                        url,
                        json={"login": self.login, "password": pwd},
                        headers=self.headers,
                        timeout=30
                    )
                    if resp.status_code < 400:
                        # Пытаемся вытащить валюту/счётчики из ответа логина
                        try:
                            login_data = resp.json() or {}
                            logging.info(f"[auth] Login response for {self.login}: {login_data}")
                            self._harvest_from_login_json(login_data)
                        except Exception as je:
                            logging.debug(f"[auth] login JSON parse issue: {je}")

                        logging.info("Авторизация успешна")
                        return True
                    logging.error(f"[auth] {resp.status_code} {url} :: {resp.text}")
                except Exception as ie:
                    logging.error(f"[auth] {type(ie).__name__} {url}: {ie}")

            return False
        except Exception as e:
            logging.error(f"[auth] Ошибка авторизации: {e}")
            # Не валим — попробуем работать без сессии
            return True

    # ---------- Универсальный резолвер эндпоинтов для методов ----------
    def _request_methods_json(self, op: str, country: str, preferred_url: Optional[str]) -> Dict[str, Any]:
        """
        Возвращает JSON с методами. Сначала пробуем preferred_url, затем — список известных вариантов.
        op: "deposit"|"withdraw"
        """
        # Список кандидатов: сперва без /en, потом с /en
        known_patterns = [
            "/api/v1/model/paysystem/{op}",
            "/api/v1/paysystem/{op}",
            "/api/v1/model/paysystem",     # operation_type в теле/query
            "/api/v1/paysystem",

            "/api/v1/en/model/paysystem/{op}",
            "/api/v1/en/paysystem/{op}",
            "/api/v1/en/model/paysystem",
            "/api/v1/en/paysystem",
        ]

        candidates: List[str] = []

        # 0) Если ранее уже нашли рабочий путь — пробуем его первым
        if op in self._resolved_endpoints:
            candidates.append(self._resolved_endpoints[op])

        # 1) Явно переданный preferred_url (из DEPOSIT_URL/WITHDRAW_URL)
        if preferred_url:
            candidates.append(preferred_url)

        # 2) Остальные известные варианты
        for p in known_patterns:
            if "{op}" in p:
                candidates.append(p.format(op=op))
            else:
                candidates.append(p)

        # Убираем дубликаты с сохранением порядка
        seen = set()
        uniq = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                uniq.append(c)

        errors = []
        for rel in uniq:
            url = self._full_url(rel)
            try:
                # POST
                payload = {"country": country}
                # если путь без {op}, передаём operation_type в теле
                if "{op}" not in rel and rel.rstrip("/").endswith("paysystem"):
                    payload["operation_type"] = op
                r = self.session.post(url, json=payload, headers=self.headers, timeout=30)
                if r.status_code == 200:
                    self._resolved_endpoints[op] = rel
                    return r.json() or {}

                # GET c query + fields параметр для Rolling и Vegazone
                params = {"country": country, "operation_type": op}

                # Добавляем fields параметр для Rolling, Vegazone и Ludios проектов
                if "rolling" in self.base_url.lower() or "vegazone" in self.base_url.lower() or "ludios" in self.base_url.lower():
                    params["fields"] = "images,name,title,display_type,show_amount,parent_paysystem,run_iframe,version"
                    params["limit"] = 100

                r = self.session.get(url, params=params, headers=self.headers, timeout=30)
                if r.status_code == 200:
                    self._resolved_endpoints[op] = rel
                    return r.json() or {}

                errors.append(f"{r.status_code} {url}")
            except Exception as e:
                errors.append(f"{type(e).__name__} {url}: {e}")

        logging.error(f"[fetch] Не нашли рабочий эндпоинт для '{op}'. Пробовали:\n - " + "\n - ".join(errors))
        return {"success": False, "data": [], "message": f"No working endpoint found for {op}"}


    def fetch_methods(
        self,
        url: str,
        country: str,
        return_raw: bool = False,
    ) -> Tuple[List[str], List[str], Set[tuple], Optional[List[dict]]]:
        """
        Возвращает:
          titles:      List[str]
          names:       List[str]
          recommended: Set[(title, name)]
          raw_list:    List[dict] | None   (если return_raw=True)
        """
        # Определяем операцию по URL, если можем
        url_lower = (url or "").lower()
        op = "withdraw" if "withdraw" in url_lower else "deposit"

        # 1) Получаем JSON с авто-фолбэком путей (без /en → с /en)
        j = self._request_methods_json(op=op, country=country, preferred_url=url)

        data = j.get("data") or j.get("methods") or []
        if not isinstance(data, list):
            logging.warning("fetch_methods: 'data' не список, пришло: %r", type(data))
            data = []

        # Если API отдаёт смесь, отфильтруем по operation_type
        filtered: List[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            pm = item.get("paymethods") or {}
            it_op = None
            if isinstance(pm, dict):
                it_op = pm.get("operation_type") or pm.get("operationType")
            it_op = it_op or item.get("operation_type") or item.get("operationType")
            if it_op and str(it_op).lower() not in ("deposit", "withdraw"):
                continue
            if it_op and str(it_op).lower() != op:
                continue
            filtered.append(item)

        titles: List[str] = []
        names:  List[str] = []
        recommended: Set[tuple] = set()
        raw_list: List[dict] = []

        # 🔧 ДЕДУПЛИКАЦИЯ: отслеживаем уникальные (title, name) пары
        seen_methods = set()

        country_up = (country or "").upper()

        for item in filtered:
            raw_list.append(item)

            title = (item.get("title") or item.get("alias") or item.get("name") or "").strip()
            pm: Dict[str, Any] = item.get("paymethods") or {}
            pm_pay: Dict[str, Any] = pm.get("paymethod") or {}

            name = (
                item.get("name")
                or pm_pay.get("name")
                or pm_pay.get("code")
                or item.get("doc_id")
                or ""
            ).strip()

            if not title or not name:
                continue

            # 🔧 ДЕДУПЛИКАЦИЯ: проверяем уникальность по (title, name)
            dedup_key = (title, name)
            if dedup_key in seen_methods:
                logging.debug(f"[BaseExtractor] Пропускаем дубликат {op}: {title} -> {name}")
                continue
            seen_methods.add(dedup_key)

            titles.append(title)
            names.append(name)

            # Валюта: если ещё не установлена из логина — попробуем взять отсюда
            if not getattr(self, "currency", None):
                try:
                    cur = ((pm.get("currency") or {}).get("code"))
                    if cur:
                        self.currency = str(cur).upper()
                except Exception:
                    pass

            # --- корректный recommended ---
            rec_obj = (
                item.get("recomended")
                or pm.get("recomended")
                or item.get("recommended")   # на случай правильного написания
                or pm.get("recommended")
                or {}
            )

            is_rec = False
            if isinstance(rec_obj, dict) and rec_obj.get("status") is True:
                countries = rec_obj.get("countries") or []
                if not countries:
                    is_rec = True
                else:
                    try:
                        is_rec = country_up in {str(c).upper() for c in countries}
                    except Exception:
                        is_rec = False

            # правило для Crypto: только если прошёл проверку по странам
            # (если хочешь «никогда не рекомендовать», просто занули здесь is_rec)
            if title.strip().lower() == "crypto" and not is_rec:
                is_rec = False

            if is_rec:
                recommended.add((title, name))

        # Для совместимости — считаем кол-во депозитных методов в последнем вызове
        try:
            if op == "deposit":
                self.deposit_count = len(titles)
        except Exception:
            pass

        # 🧪 ДЕБАГ: Выводим все методы которые вернул API
        if op == "deposit" and filtered:
            logging.info(f"[DEBUG] 📋 МЕТОДЫ ИЗ API ({self.base_url}) - ПОЛНЫЙ СПИСОК:")
            logging.info(f"[DEBUG] Всего методов в сыром API: {len(filtered)}")
            logging.info(f"[DEBUG] Логин: {self.login}")

            for i, item in enumerate(filtered, 1):
                title = (item.get("title") or item.get("alias") or item.get("name") or "").strip()
                name = (
                    item.get("name")
                    or (item.get("paymethods") or {}).get("paymethod", {}).get("name")
                    or (item.get("paymethods") or {}).get("paymethod", {}).get("code")
                    or item.get("doc_id")
                    or ""
                ).strip()
                display_type = item.get("display_type", "")
                parent = item.get("parent_paysystem", "")
                recommended_info = item.get("recomended") or item.get("recommended") or {}
                rec_status = recommended_info.get("status", False)
                rec_countries = recommended_info.get("countries", [])

                logging.info(f"  {i:2d}. {title} ({name}) | {display_type} | parent: {parent}")
                if rec_status:
                    logging.info(f"       ⭐ Рекомендован для стран: {rec_countries}")

            logging.info(f"[DEBUG] {'='*60}")

        if return_raw:
            return titles, names, recommended, raw_list
        return titles, names, recommended, None
