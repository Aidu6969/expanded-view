#!/usr/bin/env bash
# Put a finished video on the `media` branch and print its public URL.
#   bash tools/publish_media.sh out/<slug>/<slug>.mp4 <YYYY-MM-DD>-<slug>.mp4
# The media branch is a single orphan commit holding only the last 4 days of videos, force-pushed each
# time, so the repo does not grow by ~15 MB per video forever. Metricool fetches the file from the URL.
set -euo pipefail
SRC=$(realpath "$1"); NAME=$2
ROOT=$(cd "$(dirname "$0")/.." && pwd)
REMOTE=$(git -C "$ROOT" remote get-url origin)
SLUG=$(basename "$(dirname "$REMOTE")")/$(basename "$REMOTE" .git)
SLUG=${SLUG#*github.com/}; SLUG=${SLUG#*:}
W=$(mktemp -d)
cd "$W"
git init -q -b media
git remote add origin "$REMOTE"
if git fetch -q --depth 1 origin media 2>/dev/null; then
  git checkout -q FETCH_HEAD -- . 2>/dev/null || true
fi
# keep files dated within the last 4 days
CUT=$(date -d "4 days ago" +%Y-%m-%d)
for f in *.mp4; do
  [ -e "$f" ] || continue
  [[ "${f:0:10}" < "$CUT" ]] && rm -f "$f"
done
cp "$SRC" "$NAME"
git add -A .
git -c user.name="Expanded View bot" -c user.email="noreply@anthropic.com" commit -q -m "media: $NAME"
git push -q -f origin HEAD:media
OWNER_REPO=$(echo "$SLUG" | sed -E 's#^.*/([^/]+/[^/]+)$#\1#')
URL="https://raw.githubusercontent.com/${OWNER_REPO}/media/${NAME}"
for i in 1 2 3 4 5 6; do
  code=$(curl -s -o /dev/null -I -w "%{http_code}" "$URL")
  [ "$code" = "200" ] && break
  sleep 10
done
echo "$URL  (HTTP $code)"
[ "$code" = "200" ]
