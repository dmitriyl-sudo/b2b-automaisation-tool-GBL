# utils/snapshot.py
from datetime import datetime, timezone
from collections import defaultdict
import re

def extract_tag(name: str):
    """Extract condition tags from method name"""
    if not name: 
        return None
    s = name.upper()
    if "MOB" in s: 
        return "MOB"
    if "AFF" in s: 
        return "AFF"
    if (m := re.search(r"(\d)DEP", s)): 
        return f"{m.group(1)}DEP"
    return None

def build_geo_snapshot(logins, fetch_methods_fn, run_login_fn):
    """
    Build snapshot for a single GEO
    logins: list[str]
    fetch_methods_fn(login) -> {deposit_methods, withdraw_methods, recommended_methods}
    run_login_fn(login) -> {currency?}  # если доступна валюта
    """
    title_to_names = defaultdict(set)
    title_to_avail = defaultdict(lambda: {"deposit": False, "withdraw": False})
    title_to_tags = defaultdict(set)
    title_to_recommended = defaultdict(bool)
    title_seen_logins = defaultdict(int)
    currencies = set()

    for login in logins:
        # Get currency from login check
        auth = run_login_fn(login) or {}
        if auth.get("currency"): 
            currencies.add(auth["currency"])

        # Get methods data
        data = fetch_methods_fn(login) or {}
        dep = data.get("deposit_methods") or []
        wdr = data.get("withdraw_methods") or []
        rec = set("|||".join(x) for x in (data.get("recommended_methods") or []))

        def bump(methods, kind):
            titles_in_this_login = set()
            for title, name in methods:
                key = f"{title}|||{name}"
                if key in rec: 
                    title_to_recommended[title] = True
                title_to_names[title].add(name)
                title_to_avail[title][kind] = True
                tag = extract_tag(name)
                if tag: 
                    title_to_tags[title].add(tag)
                titles_in_this_login.add(title)
            # Count unique titles per login
            for t in titles_in_this_login:
                title_seen_logins[t] += 1

        bump(dep, "deposit")
        bump(wdr, "withdraw")

    # Build methods list
    methods = []
    for title in sorted(title_to_names.keys()):
        names = sorted(title_to_names[title])
        tags = sorted(title_to_tags[title]) if title_to_tags[title] else ["ALL"]
        methods.append({
            "title": title,
            "names": names,
            "availability": title_to_avail[title],
            "recommended": bool(title_to_recommended[title]),
            "conditions": tags,
            "seen_in_logins": title_seen_logins[title],
        })

    # Determine currency (if consistent across logins)
    currency = list(currencies)[0] if len(currencies) == 1 else None
    return currency, methods

def build_snapshot(project: str, env: str, geo_to_logins: dict, fetchers):
    """
    Build complete project snapshot
    geo_to_logins: { GEO: [login, ...] }
    fetchers: { 'run_login': lambda geo, login: {...}, 'get_methods': lambda geo, login: {...} }
    """
    geos = []
    total_logins = 0
    unique_titles = set()

    for geo, logins in geo_to_logins.items():
        total_logins += len(logins)
        
        def run_login_fn(login):
            return fetchers["run_login"](geo, login)
        
        def fetch_methods_fn(login):
            return fetchers["get_methods"](geo, login)
        
        currency, methods = build_geo_snapshot(logins, fetch_methods_fn, run_login_fn)
        
        for m in methods:
            unique_titles.add(m["title"])
        
        geos.append({
            "geo": geo,
            "currency": currency,
            "logins_count": len(logins),
            "logins_sample": logins[:3],
            "methods": methods,
        })

    snapshot = {
        "version": 1,
        "project": project,
        "env": env,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "coverage": {
            "total_geos": len(geos),
            "total_logins": total_logins,
            "total_methods_unique": len(unique_titles),
        },
        "geos": geos,
    }
    return snapshot
