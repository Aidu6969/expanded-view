#!/usr/bin/env bash
# Host a finished video publicly so Metricool can fetch it, and print its URL.
#   bash tools/publish_media.sh out/<slug>/<slug>.mp4 <YYYY-MM-DD>-<slug>.mp4
# The engine repo (expanded-view) is PRIVATE. Videos go to a separate PUBLIC repo,
# Aidu6969/expanded-view-media, which holds only the last 4 days of finished videos (they are public
# on YouTube/TikTok anyway) as one force-pushed commit, so it never grows. Metricool copies the file
# to its own storage when the post is created; the link only has to work at scheduling time.
# FALLBACK (owner-approved 2026-10-31, for autonomy): if the media repo cannot be reached from the run,
# the video goes to the orphan `media` branch of the engine repo (same 4-day, force-pushed rule), served from
# raw.githubusercontent.com/Aidu6969/expanded-view/media/<file>. That only works while the engine repo is
# public. The script prints which host it used.
set -euo pipefail
SRC=$(realpath "$1"); NAME=$2
MEDIA_REPO=${MEDIA_REPO:-Aidu6969/expanded-view-media}
BRANCH=main
if ! git ls-remote "https://github.com/${MEDIA_REPO}" >/dev/null 2>&1; then
  echo "media repo ${MEDIA_REPO} unreachable; falling back to Aidu6969/expanded-view branch media" >&2
  MEDIA_REPO=Aidu6969/expanded-view; BRANCH=media
fi
W=$(mktemp -d)
cd "$W"
git init -q -b "$BRANCH"
git remote add origin "https://github.com/${MEDIA_REPO}"
if git fetch -q --depth 1 origin "$BRANCH" 2>/dev/null; then
  git checkout -q FETCH_HEAD -- . 2>/dev/null || true
fi
CUT=$(date -d "4 days ago" +%Y-%m-%d)
for f in *.mp4; do
  [ -e "$f" ] || continue
  [[ "${f:0:10}" < "$CUT" ]] && rm -f "$f"
done
[ -f README.md ] || printf '# Expanded View videos\n\nFinished videos waiting to be posted. Old files are removed automatically.\n' > README.md
cp "$SRC" "$NAME"
git add -A .
git -c user.name="Expanded View bot" -c user.email="noreply@anthropic.com" commit -q -m "media: $NAME"
git push -q -f origin HEAD:"$BRANCH"
URL="https://raw.githubusercontent.com/${MEDIA_REPO}/${BRANCH}/${NAME}"
code=000
for i in 1 2 3 4 5 6; do
  code=$(curl -s -o /dev/null -I -w "%{http_code}" "$URL")
  [ "$code" = "200" ] && break
  sleep 10
done
echo "$URL  (HTTP $code)"
[ "$code" = "200" ]
