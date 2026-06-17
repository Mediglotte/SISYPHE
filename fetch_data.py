#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISYPHE — recuperation de la couche "veille" (situation / epidemies).

Ce script NE TOUCHE PAS au contenu clinique (posologies, protocoles, traductions),
cure a la main. Il alimente une couche volatile d'alertes par pays, a partir de
sources ouvertes :

  1. ReliefWeb API (https://api.reliefweb.int) — ouverte, sans cle, parametre `appname`.
  2. ReliefWeb filtre source = IOM -> alertes de deplacement (DTM / IOM).
  3. OMS Disease Outbreak News (https://www.who.int/api/news/diseaseoutbreaknews) — JSON public.

  L'Institut Pasteur n'expose pas d'API d'alertes par pays : il figure comme
  source de reference (lien dans l'outil), pas comme flux automatise.

SISYPHE restant un fichier HTML simple (pas de site / Pages), le script :
  - ecrit data/overlay.json (trace + format), et
  - INJECTE les donnees directement dans le(s) HTML du depot (balise
    window.SISYPHE_OVERLAY), pour que le fichier unique embarque la veille.

La validation hebdomadaire = fusionner la Pull Request ouverte par l'Action.

Usage :
    python scripts/fetch_data.py            # execution normale (reseau requis)
    python scripts/fetch_data.py --selftest # test logique hors-ligne
"""

import json
import re
import sys
import datetime as dt
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# --------------------------------------------------------------------------- CONFIG
APPNAME = "sisyphe-clinical-tool"
LOOKBACK_DAYS = 120
MAX_PER_SOURCE = 6
MAX_IOM = 3
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "overlay.json"

RELIEFWEB_URL = "https://api.reliefweb.int/v2/reports"
WHO_DON_URL = "https://www.who.int/api/news/diseaseoutbreaknews"
WHO_ITEM_BASE = "https://www.who.int/emergencies/disease-outbreak-news/item/"

SOURCES_LABEL = ["ReliefWeb API", "OMS Disease Outbreak News", "DTM / IOM", "Institut Pasteur"]

QUERY_TERMS = ("cholera OR measles OR diphtheria OR dengue OR malaria OR polio OR "
               "typhoid OR hepatitis OR leishmaniasis OR meningitis OR outbreak OR "
               "epidemic OR vaccination OR malnutrition OR displacement")

COUNTRIES = {
    "soudan":      {"iso3": "SDN", "who": ["Sudan"]},
    "palestine":   {"iso3": "PSE", "who": ["occupied Palestinian territory", "Palestine", "Gaza"]},
    "ukraine":     {"iso3": "UKR", "who": ["Ukraine"]},
    "afghanistan": {"iso3": "AFG", "who": ["Afghanistan"]},
    "yemen":       {"iso3": "YEM", "who": ["Yemen"]},
    "rdc":         {"iso3": "COD", "who": ["Democratic Republic of the Congo"]},
    "syrie":       {"iso3": "SYR", "who": ["Syrian Arab Republic", "Syria"]},
    "mali":        {"iso3": "MLI", "who": ["Mali"]},
    "niger":       {"iso3": "NER", "who": ["Niger"]},
    "tchad":       {"iso3": "TCD", "who": ["Chad"]},
    "burkina":     {"iso3": "BFA", "who": ["Burkina Faso"]},
    "mauritanie":  {"iso3": "MRT", "who": ["Mauritania"]},
}

TIMEOUT = 30


# --------------------------------------------------------------------------- UTILS
def _date_only(value):
    return str(value)[:10] if value else ""


def _from_date():
    return (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()


# --------------------------------------------------------------------------- RELIEFWEB
def reliefweb_payload(iso3, source=None, use_query=True, limit=MAX_PER_SOURCE):
    conds = [
        {"field": "primary_country.iso3", "value": iso3},
        {"field": "date.created", "value": {"from": _from_date() + "T00:00:00+00:00"}},
    ]
    if source:
        conds.append({"field": "source.shortname", "value": source})
    payload = {
        "filter": {"operator": "AND", "conditions": conds},
        "fields": {"include": ["title", "url_alias", "url", "source.shortname", "date.created"]},
        "sort": ["date.created:desc"],
        "limit": limit,
    }
    if use_query:
        payload["query"] = {"value": QUERY_TERMS, "operator": "OR"}
    return payload


def parse_reliefweb(data, force_source=None):
    alerts = []
    for item in (data or {}).get("data", []):
        f = item.get("fields", {})
        title = (f.get("title") or "").strip()
        if not title:
            continue
        if force_source:
            src_name = force_source
        else:
            src = f.get("source", [])
            if isinstance(src, list):
                names = ", ".join(s.get("shortname", "") for s in src if s.get("shortname"))
            else:
                names = src.get("shortname", "") if isinstance(src, dict) else ""
            src_name = "ReliefWeb" + (" / " + names if names else "")
        alerts.append({
            "title": title,
            "source": src_name,
            "date": _date_only(f.get("date", {}).get("created")),
            "url": f.get("url_alias") or f.get("url") or "",
            "kind": "reliefweb",
        })
    return alerts


def fetch_reliefweb(iso3):
    r = requests.post(RELIEFWEB_URL, params={"appname": APPNAME},
                      json=reliefweb_payload(iso3), timeout=TIMEOUT)
    r.raise_for_status()
    return parse_reliefweb(r.json())[:MAX_PER_SOURCE]


def fetch_dtm_iom(iso3):
    r = requests.post(RELIEFWEB_URL, params={"appname": APPNAME},
                      json=reliefweb_payload(iso3, source="IOM", use_query=False, limit=MAX_IOM),
                      timeout=TIMEOUT)
    r.raise_for_status()
    out = parse_reliefweb(r.json(), force_source="DTM / IOM")
    for a in out:
        a["kind"] = "dtm"
    return out[:MAX_IOM]


# --------------------------------------------------------------------------- OMS
def _who_items(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("value", "Items", "items", "data", "results"):
            if isinstance(raw.get(key), list):
                return raw[key]
    return []


def _who_field(item, *keys):
    for k in keys:
        if k in item and item[k]:
            return item[k]
    return ""


def parse_who(raw, who_names, since_date):
    out = []
    names = [n.lower() for n in who_names]
    for it in _who_items(raw):
        if not isinstance(it, dict):
            continue
        title = str(_who_field(it, "Title", "title", "Headline", "Message", "Name")).strip()
        if not title or not any(n in title.lower() for n in names):
            continue
        date = _date_only(_who_field(it, "PublicationDate", "DateCreated", "Date", "date"))
        if since_date and date and date < since_date:
            continue
        url_name = str(_who_field(it, "ItemDefaultUrl", "UrlName", "urlName", "Url", "url"))
        if url_name.startswith("http"):
            url = url_name
        elif url_name:
            url = WHO_ITEM_BASE + url_name.lstrip("/")
        else:
            url = "https://www.who.int/emergencies/disease-outbreak-news"
        out.append({"title": title, "source": "OMS — Disease Outbreak News",
                    "date": date, "url": url, "kind": "who"})
    return out[:MAX_PER_SOURCE]


def fetch_who_raw():
    r = requests.get(WHO_DON_URL, timeout=TIMEOUT, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


# --------------------------------------------------------------------------- BUILD
def build_overlay():
    out = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "appname": APPNAME,
        "sources": SOURCES_LABEL,
        "note": "Couche de veille automatisee. A valider par un clinicien. Ne remplace pas les protocoles.",
        "countries": {},
    }
    try:
        who_raw = fetch_who_raw()
    except Exception as e:  # noqa: BLE001
        print("[WHO] flux indisponible, on continue : %s" % e, file=sys.stderr)
        who_raw = None

    since, today = _from_date(), dt.date.today().isoformat()

    for key, cfg in COUNTRIES.items():
        alerts = []
        for label, fn in (("ReliefWeb", fetch_reliefweb), ("DTM/IOM", fetch_dtm_iom)):
            try:
                alerts += fn(cfg["iso3"])
            except Exception as e:  # noqa: BLE001
                print("[%s] %s (%s) : %s" % (label, key, cfg["iso3"], e), file=sys.stderr)
        if who_raw is not None:
            try:
                alerts += parse_who(who_raw, cfg["who"], since)
            except Exception as e:  # noqa: BLE001
                print("[WHO] %s : %s" % (key, e), file=sys.stderr)

        seen, dedup = set(), []
        for a in sorted(alerts, key=lambda x: x.get("date", ""), reverse=True):
            t = a["title"].lower()
            if t in seen:
                continue
            seen.add(t)
            dedup.append(a)
        out["countries"][key] = {"updated": today, "alerts": dedup[:8]}
    return out


def write_overlay(overlay):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(overlay, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    total = sum(len(c["alerts"]) for c in overlay["countries"].values())
    print("OK : %s (%d alertes, %d pays)." % (OUT_PATH, total, len(overlay["countries"])))


OVERLAY_RE = re.compile(r"(window\.SISYPHE_OVERLAY\s*=\s*).*?(;\s*</script>)", re.S)


def inject_into_html(overlay):
    payload = json.dumps(overlay, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    n = 0
    for f in sorted(REPO_ROOT.glob("*.html")):
        txt = f.read_text(encoding="utf-8")
        if "window.SISYPHE_OVERLAY" not in txt:
            continue
        new, c = OVERLAY_RE.subn(lambda m: m.group(1) + payload + m.group(2), txt, count=1)
        if c:
            f.write_text(new, encoding="utf-8")
            n += 1
            print("Injecte dans %s" % f.name)
    if n == 0:
        print("Aucun HTML avec la balise SISYPHE_OVERLAY (injection ignoree).", file=sys.stderr)
    return n


# --------------------------------------------------------------------------- SELFTEST
def selftest():
    rw = parse_reliefweb({"data": [
        {"fields": {"title": "Sudan: Cholera outbreak", "url_alias": "https://reliefweb.int/x",
                    "source": [{"shortname": "OCHA"}], "date": {"created": "2026-06-10T08:00:00+00:00"}}},
        {"fields": {"title": "", "date": {"created": "2026-06-09T00:00:00+00:00"}}},
    ]})
    assert len(rw) == 1 and rw[0]["date"] == "2026-06-10", rw

    iom = parse_reliefweb({"data": [{"fields": {"title": "Yemen displacement update",
                                                "date": {"created": "2026-06-01T00:00:00+00:00"}}}]},
                          force_source="DTM / IOM")
    assert iom[0]["source"] == "DTM / IOM", iom

    who = parse_who({"value": [
        {"Title": "Cholera - Sudan", "PublicationDate": "2026-05-30T00:00:00Z", "ItemDefaultUrl": "cholera-sudan"},
        {"Title": "Measles - Morocco", "PublicationDate": "2026-05-13T00:00:00Z"},
    ]}, ["Sudan"], "2026-01-01")
    assert len(who) == 1 and who[0]["url"].startswith("https://www.who.int/"), who

    sample = '<html><script id="sisyphe-overlay">window.SISYPHE_OVERLAY = null;</script></html>'
    payload = json.dumps({"countries": {"x": {"alerts": []}}}, separators=(",", ":")).replace("</", "<\\/")
    new, c = OVERLAY_RE.subn(lambda m: m.group(1) + payload + m.group(2), sample, count=1)
    assert c == 1 and '"countries"' in new and new.endswith(";</script></html>"), new
    print("selftest: OK  (ReliefWeb, DTM/IOM, OMS, injection HTML)")


# --------------------------------------------------------------------------- MAIN
if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    if requests is None:
        print("Le module 'requests' est requis (pip install requests).", file=sys.stderr)
        sys.exit(1)
    ov = build_overlay()
    write_overlay(ov)
    inject_into_html(ov)
