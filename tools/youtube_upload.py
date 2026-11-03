"""Upload a video straight to the Expanded View YouTube channel (no Metricool), scheduled or public.

    python tools/youtube_upload.py --check
    python tools/youtube_upload.py out/<slug>/<slug>.mp4 --meta episodes/<slug>/episode.py \
        --publish-at 2026-11-04T10:00:00-05:00 [--short | --long] [--thumbnail out/<slug>/thumb.jpg]

Scheduling = upload as PRIVATE with status.publishAt; YouTube makes it public at that time. To cancel, delete or
keep it private in YouTube Studio before then (that is the owner's cancel window for direct uploads).
After upload it posts META["first_comment"] as a comment (needs the youtube.force-ssl scope).

Credentials (owner, one-time, see docs/SETUP_ACCOUNTS.md), as environment variables of the task environment:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
Allowed domains needed: oauth2.googleapis.com, www.googleapis.com, youtube.googleapis.com
Never print or commit these values.
"""
import argparse
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
API = "https://www.googleapis.com/youtube/v3"
CATEGORY = {"SCIENCE_TECHNOLOGY": "28", "AUTOS_VEHICLES": "2", "EDUCATION": "27"}


class NotConfigured(RuntimeError):
    pass


def access_token():
    cid, sec, rt = (os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))
    if not (cid and sec and rt):
        raise NotConfigured("YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN are not all set")
    data = urllib.parse.urlencode({"client_id": cid, "client_secret": sec, "refresh_token": rt,
                                   "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=30) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise NotConfigured(f"Google refused the refresh token (HTTP {e.code}): {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        raise NotConfigured(f"cannot reach oauth2.googleapis.com ({e.reason}); add it to the allowed domains")


def _req(method, url, tok, body=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {tok}"}
    h.update(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if body is not None and raw is None:
        h["Content-Type"] = "application/json; charset=UTF-8"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=600)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube API HTTP {e.code} for {url.split('?')[0]}: {e.read().decode()[:500]}")


def channel(tok):
    _, _, b = _req("GET", f"{API}/channels?part=snippet&mine=true", tok)
    items = json.loads(b).get("items", [])
    return items[0]["snippet"]["title"] if items else None


def load_meta(path):
    spec = importlib.util.spec_from_file_location("episode", path)
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    return ep.META


def upload(video, meta, publish_at=None, short=True, thumbnail=None, category="SCIENCE_TECHNOLOGY"):
    tok = access_token()
    title = meta["title"]   # vertical + under 3 min is enough for YouTube to treat an upload as a Short
    status = {"privacyStatus": "private" if publish_at else "public", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": False, "embeddable": True}
    if publish_at:
        status["publishAt"] = publish_at
    body = {"snippet": {"title": title[:100], "description": meta["description"][:5000],
                        "tags": meta.get("tags", [])[:30], "categoryId": CATEGORY.get(category, "28"),
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": status}
    size = os.path.getsize(video)
    _, hdr, _ = _req("POST", UPLOAD_URL, tok, body=body,
                     headers={"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    loc = hdr.get("Location") or hdr.get("location")
    with open(video, "rb") as fh:
        _, _, b = _req("PUT", loc, tok, raw=fh.read(), headers={"Content-Type": "video/mp4"})
    vid = json.loads(b)["id"]
    out = {"videoId": vid, "url": f"https://www.youtube.com/{'shorts/' if short else 'watch?v='}{vid}",
           "studio": f"https://studio.youtube.com/video/{vid}/edit", "publishAt": publish_at}
    if thumbnail and os.path.exists(thumbnail):
        try:
            with open(thumbnail, "rb") as fh:
                _req("POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", tok,
                     raw=fh.read(), headers={"Content-Type": "image/jpeg"})
            out["thumbnail"] = "set"
        except RuntimeError as e:
            out["thumbnail"] = f"failed: {e}"   # needs a phone-verified channel
    fc = meta.get("first_comment")
    if fc:
        try:
            _req("POST", f"{API}/commentThreads?part=snippet", tok,
                 body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": fc}}}})
            out["first_comment"] = "posted"
        except RuntimeError as e:
            out["first_comment"] = f"failed (post it after publish): {e}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?")
    ap.add_argument("--meta")
    ap.add_argument("--publish-at")
    ap.add_argument("--long", action="store_true")
    ap.add_argument("--short", action="store_true")
    ap.add_argument("--thumbnail")
    ap.add_argument("--category", default="SCIENCE_TECHNOLOGY")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    try:
        if a.check:
            print(json.dumps({"ok": True, "channel": channel(access_token())}))
            return
        meta = load_meta(a.meta)
        print(json.dumps(upload(a.video, meta, a.publish_at, short=not a.long, thumbnail=a.thumbnail,
                                category=a.category), indent=2))
    except NotConfigured as e:
        print(json.dumps({"ok": False, "not_configured": str(e)}))
        sys.exit(3)


if __name__ == "__main__":
    main()
