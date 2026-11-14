import sqlite3
import subprocess
import platform
import time
from datetime import datetime

DB = "monitor.db"
HOSTS = ["8.8.8.8", "1.1.1.1", "google.com", "192.168.1.1"]

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS pings (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           host TEXT NOT NULL,
           ts TEXT NOT NULL,
           up INTEGER NOT NULL,
           latency_ms REAL)""")
def ping(host):
    flag = "-n" if platform.system() == "Windows" else "-c"
    start = time.perf_counter()
    r = subprocess.run(["ping", flag, "1", host], capture_output=True)
    ms = round((time.perf_counter() - start) * 1000, 1)
    if r.returncode == 0:
        return 1, ms
    return 0, None

def save(host, up, ms):
    with sqlite3.connect(DB) as c:
       c.execute(
         "INSERT INTO pings (host, ts, up, latency_ms) VALUES (?, ?, ?, ?)",
         (host, datetime.now().isoformat(timespec="seconds"), up, ms),
    )

if __name__ == "__main__":
    init_db()
    while True:
        for h in HOSTS:
            up, ms = ping(h)
            save(h, up, ms)
            print(h, "UP" if up else "DOWN", ms)
        time.sleep(30)