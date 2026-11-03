"""Licensed real-car photos and clips for long-form videos (owner, 2026-11-03: licensed only).

Sources (nothing else, ever):
  Wikimedia Commons  photos (and some video) under public domain / CC0 / CC BY / CC BY-SA. Credited.
  Pexels             stock video clips under the Pexels license (free use, no attribution required; we credit
                     anyway). Needs PEXELS_API_KEY.
  own                files the owner supplies, placed in long/<slug>/assets/own/ with a line in the manifest.

Never: YouTube/TikTok/TV/review footage, press kits whose terms forbid monetised use, AI images of real cars.

Manifest: long/<slug>/assets/manifest.yaml  (committed; the media files themselves are cached, not committed)
  <asset_id>:
    file: assets/<asset_id>.jpg
    kind: photo | clip
    source: wikimedia | pexels | own
    page: <URL of the file page>         title: <file title>
    author: <name>                       license: <short name, e.g. CC BY-SA 4.0>
    license_url: <URL>                   note: <what it shows, checked by eye>

    python -m ev.long.assets search long/<slug> "Honda NSX 1991" --n 12      # candidates with licenses
    python -m ev.long.assets add long/<slug> nsx_front "File:Honda NSX ....jpg"   # download + manifest entry
    python -m ev.long.assets pexels long/<slug> "sports car night highway" --n 8
    python -m ev.long.assets addclip long/<slug> highway_night <pexels video id>
    python -m ev.long.assets fetch long/<slug>       # re-download every manifest file (fresh workspace)
    python -m ev.long.assets credits long/<slug>     # text block for the YouTube description
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

import yaml

UA = "ExpandedViewBot/1.0 (licensed-asset fetcher for an educational car channel)"
COMMONS = "https://commons.wikimedia.org/w/api.php"
OK_LICENSES = ("public domain", "pd", "cc0", "cc by", "cc-by", "cc by-sa", "cc-by-sa", "attribution")
BAD_LICENSES = ("nc", "nd", "fair use", "non-free", "gfdl only")


def _get(url, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return r.read()


def _strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def license_ok(short):
    s = (short or "").lower()
    return any(k in s for k in OK_LICENSES) and not any(re.search(rf"\b{k}\b", s) for k in BAD_LICENSES)


def commons_search(query, n=12, min_width=1600):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": n * 2, "prop": "imageinfo",
                                "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2560})
    data = json.loads(_get(f"{COMMONS}?{q}"))
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = _strip(md.get("LicenseShortName", {}).get("value"))
        row = {"title": p["title"], "width": ii.get("width"), "height": ii.get("height"), "license": lic,
               "license_ok": license_ok(lic), "author": _strip(md.get("Artist", {}).get("value"))[:120],
               "page": ii.get("descriptionurl"), "url": ii.get("thumburl") or ii.get("url"),
               "license_url": md.get("LicenseUrl", {}).get("value", ""),
               "desc": _strip(md.get("ImageDescription", {}).get("value"))[:160]}
        if (row["width"] or 0) >= min_width:
            out.append(row)
    out.sort(key=lambda r: (not r["license_ok"], -(r["width"] or 0)))
    return out[:n]


def commons_info(title):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                                "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2560})
    data = json.loads(_get(f"{COMMONS}?{q}"))
    p = next(iter(data["query"]["pages"].values()))
    if "imageinfo" not in p:
        raise SystemExit(f"not found on Commons: {title}")
    ii = p["imageinfo"][0]
    md = ii.get("extmetadata", {})
    return {"title": p["title"], "page": ii.get("descriptionurl"), "url": ii.get("thumburl") or ii.get("url"),
            "license": _strip(md.get("LicenseShortName", {}).get("value")),
            "license_url": md.get("LicenseUrl", {}).get("value", ""),
            "author": _strip(md.get("Artist", {}).get("value"))[:160] or "Unknown author"}


def _manifest(ep):
    p = os.path.join(ep, "assets", "manifest.yaml")
    return p, (yaml.safe_load(open(p)) or {}) if os.path.exists(p) else {}


def _save_manifest(ep, m):
    p = os.path.join(ep, "assets", "manifest.yaml")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        yaml.safe_dump(m, fh, sort_keys=True, allow_unicode=True, width=120)


def add_commons(ep, aid, title, note=""):
    info = commons_info(title)
    if not license_ok(info["license"]):
        raise SystemExit(f"refused: license {info['license']!r} is not free for monetised use")
    ext = os.path.splitext(urllib.parse.urlparse(info["url"]).path)[1].lower() or ".jpg"
    rel = f"assets/{aid}{ext}"
    with open(os.path.join(ep, rel), "wb") as fh:
        fh.write(_get(info["url"]))
    _, m = _manifest(ep)
    m[aid] = {"file": rel, "kind": "photo", "source": "wikimedia", "page": info["page"], "title": info["title"],
              "author": info["author"], "license": info["license"], "license_url": info["license_url"],
              "url": info["url"], "note": note}
    _save_manifest(ep, m)
    return m[aid]


def pexels_search(query, n=8, orientation="landscape"):
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key:
        raise SystemExit("PEXELS_API_KEY is not set (docs/SETUP_ACCOUNTS.md step 4)")
    q = urllib.parse.urlencode({"query": query, "per_page": n, "orientation": orientation, "size": "medium"})
    data = json.loads(_get(f"https://api.pexels.com/videos/search?{q}", {"Authorization": key}))
    out = []
    for v in data.get("videos", []):
        files = sorted([f for f in v["video_files"] if (f.get("width") or 0) >= 1920 and f.get("file_type") == "video/mp4"],
                       key=lambda f: f["width"])
        if files:
            out.append({"id": v["id"], "duration": v["duration"], "page": v["url"], "author": v["user"]["name"],
                        "file": files[0]["link"], "width": files[0]["width"]})
    return out


def add_pexels(ep, aid, vid, note=""):
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    v = json.loads(_get(f"https://api.pexels.com/videos/videos/{vid}", {"Authorization": key}))
    files = sorted([f for f in v["video_files"] if (f.get("width") or 0) >= 1920 and f.get("file_type") == "video/mp4"],
                   key=lambda f: f["width"])
    if not files:
        raise SystemExit("no 1080p+ mp4 for that video")
    rel = f"assets/{aid}.mp4"
    with open(os.path.join(ep, rel), "wb") as fh:
        fh.write(_get(files[0]["link"]))
    _, m = _manifest(ep)
    m[aid] = {"file": rel, "kind": "clip", "source": "pexels", "page": v["url"], "title": f"Pexels video {vid}",
              "author": v["user"]["name"], "license": "Pexels License", "license_url": "https://www.pexels.com/license/",
              "url": files[0]["link"], "duration": v["duration"], "note": note}
    _save_manifest(ep, m)
    return m[aid]


def fetch_all(ep):
    _, m = _manifest(ep)
    for aid, a in m.items():
        p = os.path.join(ep, a["file"])
        if os.path.exists(p) or a["source"] == "own":
            continue
        if a["source"] == "pexels":
            key = os.environ.get("PEXELS_API_KEY", "").strip()
            data = _get(a["url"], {"Authorization": key} if key else None)
        else:
            data = _get(a["url"])
        with open(p, "wb") as fh:
            fh.write(data)
        print("fetched", aid)


def credits(ep, used=None):
    _, m = _manifest(ep)
    lines = []
    for aid in sorted(m):
        if used is not None and aid not in used:
            continue
        a = m[aid]
        if a["source"] == "own":
            continue
        lines.append(f"• {a['title'].replace('File:', '')}: {a['author']}, {a['license']} ({a['page']})")
    return "Photo and video credits:\n" + "\n".join(lines) if lines else ""


def main():
    cmd, ep = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(ep, "assets"), exist_ok=True)
    args = sys.argv[3:]
    n = int(args[args.index("--n") + 1]) if "--n" in args else 12
    if cmd == "search":
        for r in commons_search(args[0], n):
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == "add":
        print(json.dumps(add_commons(ep, args[0], args[1], args[2] if len(args) > 2 else ""), ensure_ascii=False))
    elif cmd == "pexels":
        for r in pexels_search(args[0], n):
            print(json.dumps(r))
    elif cmd == "addclip":
        print(json.dumps(add_pexels(ep, args[0], args[1], args[2] if len(args) > 2 else "")))
    elif cmd == "fetch":
        fetch_all(ep)
    elif cmd == "credits":
        print(credits(ep))


if __name__ == "__main__":
    main()
