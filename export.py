import sqlite3
import json
import sys
import time
from datetime import datetime

DB = "monitor.db"
OUT = "data.js"


def build():
    c = sqlite3.connect(DB)
    hosts = []
    names = [r[0] for r in c.execute("SELECT DISTINCT host FROM pings ORDER BY host")]
    for h in names:
        last = c.execute(
            "SELECT ts, up, latency_ms FROM pings WHERE host=? ORDER BY id DESC LIMIT 1",
            (h,),
        ).fetchone()
        total, ups, avg = c.execute(
            "SELECT COUNT(*), SUM(up), AVG(latency_ms) FROM pings WHERE host=?",
            (h,),
        ).fetchone()
        hist = c.execute(
            "SELECT up, latency_ms FROM pings WHERE host=? ORDER BY id DESC LIMIT 60",
            (h,),
        ).fetchall()
        hist.reverse()
        hosts.append({
            "host": h,
            "up": last[1],
            "last_ts": last[0],
            "last_ms": last[2],
            "total": total,
            "availability": round(100.0 * (ups or 0) / total, 1),
            "avg_ms": round(avg, 1) if avg is not None else None,
            "history": [{"up": u, "ms": m} for u, m in hist],
        })
    recent = [
        {"ts": ts, "host": h, "up": u, "ms": m}
        for ts, h, u, m in c.execute(
            "SELECT ts, host, up, latency_ms FROM pings ORDER BY id DESC LIMIT 20"
        )
    ]
    c.close()
    return {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "hosts": hosts,
        "recent": recent,
    }


def write():
    data = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DATA = " + json.dumps(data) + ";\n")
    print("data.js mis a jour", data["generated"])


if __name__ == "__main__":
    write()
    if "--once" not in sys.argv:
        while True:
            time.sleep(30)
            write()