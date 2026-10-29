"""Print the publish time for the next post (America/New_York).

Rule: the next 10:00 or 16:00 slot (Metricool's best YouTube hours for this channel) that is at least
3 hours from now (the owner's cancel window) and not already used in published.yaml. If that slot is
more than 6 hours past the 3-hour mark (a late run), use now + 3 h rounded up to 5 minutes instead,
so a late run never pushes the queue into tomorrow.

    python tools/slot.py            ->  {"dateTime": "2026-10-30T10:00:00", "timezone": "America/New_York",
                                         "iso": "2026-10-30T10:00:00-04:00"}
"""
import json
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import yaml

NY = ZoneInfo("America/New_York")
SLOTS = [time(10, 0), time(16, 0)]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def taken():
    try:
        with open(os.path.join(ROOT, "published.yaml")) as fh:
            rows = yaml.safe_load(fh) or []
    except FileNotFoundError:
        return set()
    return {str(r.get("scheduled", ""))[:16] for r in rows if r.get("scheduled")}


def next_slot(now=None, used=None):
    now = now or datetime.now(NY)
    used = taken() if used is None else used
    earliest = now + timedelta(hours=3)
    cands = [datetime.combine((now + timedelta(days=d)).date(), s, tzinfo=NY) for d in range(5) for s in SLOTS]
    first = next(c for c in cands if c >= earliest and c.strftime("%Y-%m-%dT%H:%M") not in used)
    if first - earliest <= timedelta(hours=6):
        return first
    fb = earliest.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=(earliest.minute // 5 + 1) * 5)
    # a late run posts at now+3h, but never in the middle of the night
    return fb if 8 <= fb.hour < 21 else first


def main():
    c = next_slot()
    print(json.dumps({"dateTime": c.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": "America/New_York",
                      "iso": c.isoformat()}))


if __name__ == "__main__":
    main()
