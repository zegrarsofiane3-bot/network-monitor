import json
import platform
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

DB = "monitor.db"
CONFIG = "config.json"
HOSTS = ["8.8.8.8", "1.1.1.1", "google.com", "192.168.1.1"]
INTERVAL = 30          # secondes entre deux series de pings
FAIL_THRESHOLD = 2     # echecs de suite avant d'envoyer une alerte
API = "https://api.telegram.org"
OK_ICON = chr(0x2705)
WARN_ICON = chr(0x26A0) + chr(0xFE0F)


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS pings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            ts TEXT NOT NULL,
            up INTEGER NOT NULL,
            latency_ms REAL)""")


def ping(host):
    if platform.system() == "Windows":
        cmd = ["ping", "-n", "1", "-w", "2000", host]
    else:
        cmd = ["ping", "-c", "1", "-W", "2", host]
    start = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True)
    ms = round((time.perf_counter() - start) * 1000, 1)
    out = r.stdout.decode(errors="ignore").lower()
    # Sous Windows, "hote inaccessible" peut renvoyer le code 0 :
    # on exige donc une vraie reponse (presence de "ttl=").
    if r.returncode == 0 and "ttl=" in out:
        return 1, ms
    return 0, None


def save(host, up, ms):
    with sqlite3.connect(DB) as c:
        c.execute(
            "INSERT INTO pings (host, ts, up, latency_ms) VALUES (?, ?, ?, ?)",
            (host, datetime.now().isoformat(timespec="seconds"), up, ms),
        )


def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        return None
    if cfg.get("token") and cfg.get("chat_id"):
        return cfg
    return None


def send_telegram(text, cfg):
    url = API + "/bot" + cfg["token"] + "/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": cfg["chat_id"], "text": text}
    ).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print("Erreur Telegram :", type(e).__name__, e)
        return False


def check_alert(host, up, fails, alerted):
    """Retourne un message si l'etat de la machine vient de changer."""
    now = datetime.now().strftime("%H:%M")
    if up:
        fails[host] = 0
        if alerted[host]:
            alerted[host] = False
            return OK_ICON + " " + host + " est de nouveau en ligne (" + now + ")"
        return None
    fails[host] += 1
    if fails[host] >= FAIL_THRESHOLD and not alerted[host]:
        alerted[host] = True
        return WARN_ICON + " " + host + " est hors ligne (" + now + ")"
    return None


def run():
    init_db()
    cfg = load_config()
    if cfg is None:
        print("Alertes Telegram desactivees (config.json absent ou incomplet)")
    else:
        print("Alertes Telegram activees")
    fails = {h: 0 for h in HOSTS}
    alerted = {h: False for h in HOSTS}
    while True:
        for h in HOSTS:
            up, ms = ping(h)
            save(h, up, ms)
            print(h, "UP" if up else "DOWN", ms)
            msg = check_alert(h, up, fails, alerted)
            if msg and cfg:
                send_telegram(msg, cfg)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    if "--test-alert" in sys.argv:
        cfg = load_config()
        if cfg is None:
            print("config.json absent ou incomplet")
        elif send_telegram(OK_ICON + " Test : les alertes du Network Monitor fonctionnent", cfg):
            print("Message envoye, regarde ton Telegram")
        else:
            print("Echec de l'envoi (verifie le token et le chat_id)")
    else:
        run()