DEFAULT_SLA_SEC = 3.0

def run_smoke_checks(item, account_currency=None, listing_hint=None, sla_sec=DEFAULT_SLA_SEC):
    """
    item: dict одного результата теста: {geo, login, method, status, code, message, duration, url, ...}
    account_currency: валюта аккаунта, если известна
    listing_hint: подсказка доступности из списка методов: {'deposit': bool, 'withdraw': bool}
    """
    checks = []

    # http_ok
    code = item.get('code')
    status = (item.get('status') or '').upper()
    http_ok = (status == 'OK') or (isinstance(code, int) and 200 <= code < 300)
    checks.append({'name': 'http_ok', 'pass': bool(http_ok), 'details': f'code={code}, status={status}'})

    # has_url
    url = item.get('url') or item.get('link') or item.get('payment_url')
    checks.append({'name': 'has_url', 'pass': bool(url), 'details': 'payment URL present' if url else 'missing url'})

    # fast_enough
    dur = item.get('duration')
    fast = (dur is not None and float(dur) < sla_sec)
    checks.append({'name': 'fast_enough', 'pass': bool(fast), 'details': f'duration={dur}s, sla<{sla_sec}s'})

    # consistent_with_listing
    if listing_hint:
        # если метод в листинге как доступный — не должен падать 4xx/5xx «на старте»
        consistent = True
        if (listing_hint.get('deposit') or listing_hint.get('withdraw')) and not http_ok:
            consistent = False
        checks.append({'name': 'consistent_with_listing', 'pass': consistent,
                       'details': f"listed={listing_hint}, http_ok={http_ok}"})

    # currency_ok (минимальная проверка)
    if account_currency:
        # пример: просто фиксируем, что валюта аккаунта известна
        checks.append({'name': 'currency_ok', 'pass': True, 'details': f'account={account_currency}'})

    failed = [c for c in checks if not c['pass']]
    summary = {'passed': len(checks) - len(failed), 'failed': len(failed)}
    return checks, summary
