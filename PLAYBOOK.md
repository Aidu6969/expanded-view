# Expanded View — production playbook (for scheduled runs)

You are producing ONE new Expanded View short and scheduling it. Expanded View is a faceless
YouTube Shorts + TikTok channel (@expandedview) of animated "how things actually work" explainers.
Episode 1 (`episodes/vtec`) is the reference: match its quality, accuracy, pacing and look.

Owner: Ahadu. He reviews posts during a 3-hour cancel window. Never post anything you would not
defend as accurate.

---------------------------------------------------------------------------------------------------
## 0. Fixed brand — NEVER change per episode
- **Voice:** `ev/voice.py` (Kokoro `am_michael`, speed 1.0). Never speed it up; never swap voices.
- **Look:** dark navy blueprint grid, 3/4 orthographic 3D mechanisms (`ev/gfx.py`), Poppins/Inter type,
  palette in `ev/gfx.py`. Colour meaning: CYAN = normal/baseline state, RED = the key/high/aggressive
  state, AMBER = fluids, pressure, heat, electric signals, YEL = annotations and highlights,
  GREEN = checks. White/steel = metal parts.
- **Brand layer is automatic** (`ev/brand.py`, drawn by `ev/build.py`): background, hook title
  "HOW <TOPIC> ACTUALLY WORKS" (or a variant), word-by-word captions, and THE ENDING.
- **The ending (fixed formula):** the last narration line ends with a short punchline sentence and then
  "That's <TOPIC>." The end card shows the punchline (2 lines, second in red), then the big red
  <TOPIC> title with a 1–2 line subtitle. Set `PUNCH`, `TOPIC`, `SUBTITLE`, `END_WORD`, `TOPIC_WORD`.
- **Length:** 61–75 s (TikTok Creator Rewards only pays for videos over 1 minute; Shorts ≤ 3 min).
  At this voice that is ~165–190 words of narration.
- **Sound:** narration + synthesized music bed + SFX (`ev/audio.py`); -14 LUFS. No licensed music.

---------------------------------------------------------------------------------------------------
## 1. Setup (fresh workspace every run)
1. Attach the repo: `mcp__claude-code-remote__add_repo` with owner `Aidu6969`, repo `expanded-view`,
   access `push`; run the clone command it returns; `cd` into it.
2. `bash setup.sh` (Python deps, voice model; brand fonts are bundled in `ev/fonts`).
3. Read `ev/brand.py`, the function list of `ev/gfx.py`, and `episodes/vtec/scene.py` before writing
   a new scene.
4. Load the Metricool tools: ToolSearch `metricool` (they are `mcp__Metricool_Social_Media_Management__*`).
   Call `getBrandSettings`. Brand id is **7744824** (timezone America/New_York). `networksData` shows
   which networks are connected; post only to connected ones (YouTube is; TikTok once the owner links it).

## 2. Pick the topic
Open `topics.yaml`. If an entry has `status: ready` (already built and checked), skip to step 8 and post
it: rebuild it with `python -m ev.build episodes/<slug>` first (the `out/` folder is not in the repo).
Otherwise take the first entry with `status: queued` (it is in priority order). Skip any
topic already in `published.yaml`. Set its status to `in_progress` in your working copy.
**Backfill first:** if TikTok is connected and an entry in `topics.yaml` has a `note` saying it still
needs posting to TikTok (VTEC), schedule that existing video to TikTok too (step 8, TikTok only, using
the `media/` file in `main`), then clear the note.

## 3. Research (accuracy is the product)
- 3–8 web searches. Prefer manufacturer/engineering sources, textbooks, SAE, Wikipedia for basics.
- Write `episodes/<slug>/research.md`: the 6–12 facts the video states, each with a source URL,
  plus anything you were unsure of and how you resolved it. Do not state numbers you cannot source;
  say "around" or leave them out. Note common misconceptions to avoid.

## 4. Script (`episode.py` → `LINES`)
- 8–10 lines (beats). Each line = one visual beat. Natural spoken sentences, contractions OK.
  No lists of fragments, no parentheses, no symbols, no abbreviations the voice can't say.
  Spell numbers as spoken ("seven thousand RPM").
- Shape: **hook** (surprising claim/question, ≤ 4 s) → **what it is / name** → **the problem it
  solves** → **the parts** → **how it works, step by step** → **the key moment** (the "VTEC kicks in"
  beat) → **the result** → **outro**: undo/recap + punchline + "That's <TOPIC>."
- Check pronunciation of acronyms/part names: `python -c "from ev import voice; print(voice.phonemes('...'))"`.
  If wrong, respell in the text (e.g. "V-tech" style) — the captions show the text, so keep it readable.
- Words you will cue visuals on must appear exactly once in their line (or use `nth`).
- Write `META`: YouTube title (≤ 70 chars + 3 hashtags; curiosity + keyword, e.g.
  "What happens when VTEC kicks in? #honda #jdm #engineering"), description (3 short paragraphs,
  plain facts, ends with a question), tags (8–12), first_comment (a question that names 2–3
  candidate next topics from the queue), tiktok_caption (≤ 150 chars + 4–5 hashtags), sources.
- Optional: if `vidiq_balance` shows ≥ 40 credits, call `vidiq_generate_titles` once (type short)
  and pick the best title that is ACCURATE to the video. Never pick a title that over-promises.

## 5. Scene (`scene.py`)
Scaffold with `python tools/new_episode.py <slug>`, then write the scene. Rules:
- **Time everything off the narration**: `F(line, word)` / `L(line)`; never hard-code seconds.
- **Real geometry and kinematics**: model the mechanism (like `episodes/vtec/mech.py`) and drive motion
  from it — gears mesh at the right ratio, things move only when they physically can, flows go the
  right way. Slow motion is fine; label it with `brand.note(cv, "ANIMATION SLOWED", a)`.
- **One idea per beat**: build the mechanism up piece by piece as the narration names parts; label
  parts with `brand.label` (leader + pill) exactly when spoken; use `brand.stamp` for the key moment;
  `brand.status_pill` + `brand.readout` for a changing state/quantity; a graph (`brand.graph_box`,
  `brand.curve`, `brand.dot`) when a curve explains the idea; `brand.panel`/`brand.bullet` for
  comparisons; `brand.acronym_rows` for acronyms; `brand.gauge`/`brand.lamp` for hooks.
- Second reference: `episodes/turbocharger/scene.py` (flows through pipes, spinning bladed wheels, a
  4-stroke cylinder, x-ray housings). Reusable parts live in `ev/parts.py`: `rev` (shafts, hubs, housings,
  pistons: any round part), `wheel` (fans/compressors/turbines), `pipe` + `flow` (anything that flows:
  air, gas, oil, coolant, current), `spline`, `ring_front`. Add new generic parts there, not in an episode.
- 3D: `Proj(ox, oy, s)` (ortho 3/4 view: X = along the part, Y = down, z = depth/axis), `extrude`
  for prisms (gears, lobes, levers, housings), `vcyl`/`frustum` for vertical round parts,
  `draw_spring`, `zhelix`, `hcircle`. Painter's order: draw far (large z / large -X) first.
- **Layout**: content inside x 60–940, y 150–1400 (captions live at y≈1462; TikTok UI covers the
  bottom and right edge). Hook title occupies y 230–450 until the hook ends.
- Fade/shrink your content as the end card arrives: `current.ending_k(t)`.
- `sound()` returns the audio plan (see `ev/audio.py`): SFX on key moments, optional build/drop
  around the key moment, optional engine note for engine topics.

## 6. Build loop
```bash
python -m ev.build episodes/<slug> --stills 1.0,8,20,35,50,62     # fast: look at key frames
python -m ev.build episodes/<slug>                                 # full render (~2–4 min)
```
LOOK at the stills and `out/<slug>/qa_sheet.jpg` with the Read tool every time. Fix overlaps,
clipped text, wrong motion, empty frames, unreadable labels. At most 4 full builds.

## 7. QA gate — all must pass before scheduling
1. Every factual claim in the narration is in `research.md` with a source.
2. The animation shows the mechanism correctly (parts in the right places, motion physically right).
3. `ev.build` prints `"ok": true` (duration 61–80 s, aim for 61–75 s; loudness -14 LUFS).
4. No text overlaps or leaves the safe area; captions never collide with graphics.
5. Ending = punchline + "That's <TOPIC>." with the end card.
If it cannot pass after 4 builds: do NOT post. Commit the work with `status: needs_review` and
notify the owner with the reason.

## 8. Publish
1. Commit the episode folder (`episode.py`, `scene.py`, `research.md`, any model file) and the updated
   `topics.yaml` to `main`; push.
2. Host the video: `bash tools/publish_media.sh out/<slug>/<slug>.mp4 <YYYY-MM-DD>-<slug>.mp4`.
   It force-pushes the `media` branch (last 4 days of videos only) and prints the public URL
   `https://raw.githubusercontent.com/Aidu6969/expanded-view/media/<file>.mp4`, checking it returns 200.
3. Time: `python tools/slot.py` → next 10:00 / 16:00 New York slot at least 3 h away (the owner's
   cancel window). Never schedule sooner than now + 3 h.
4. Schedule with `createScheduledPost` (blogId `7744824`, `date` = the slot's `iso`). Make **two
   separate posts** (YouTube and TikTok need different text). `info` is a JSON string:
   - YouTube Short:
     ```json
     {"autoPublish": true, "draft": false, "descendants": [], "hasNotReadNotes": false, "shortener": false,
      "smartLinkData": {"ids": []}, "mediaAltText": [],
      "providers": [{"network": "youtube"}], "media": ["<raw URL>"],
      "publicationDate": {"dateTime": "<slot dateTime>", "timezone": "America/New_York"},
      "text": "<META.description>", "firstCommentText": "<META.first_comment>",
      "youtubeData": {"title": "<META.title>", "type": "short", "privacy": "public", "tags": [<META.tags>],
                      "category": "SCIENCE_TECHNOLOGY", "madeForKids": false, "isAiGeneratedContent": true}}
     ```
   - TikTok (only if connected):
     ```json
     {"autoPublish": true, "draft": false, "descendants": [], "hasNotReadNotes": false, "shortener": false,
      "smartLinkData": {"ids": []}, "mediaAltText": [], "firstCommentText": "",
      "providers": [{"network": "tiktok"}], "media": ["<raw URL>"],
      "publicationDate": {"dateTime": "<slot dateTime>", "timezone": "America/New_York"},
      "text": "<META.tiktok_caption>",
      "tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE", "disableComment": false, "disableDuet": false,
                     "disableStitch": false, "commercialContentThirdParty": false,
                     "commercialContentOwnBrand": false, "autoAddMusic": false, "isAigc": true}}
     ```
   AI labels are ON because the narration voice is synthetic: honest, and both platforms ask for it.
   Do not send `videoThumbnailUrl`/`videoCoverMilliseconds` (rejected on this channel).
   If a call errors, read the error, fix the field it names, retry once; never change the wording of
   the text to get around an error.
5. Verify with `getScheduledPosts` (that day, America/New_York) that both posts are there with
   autoPublish on. Keep each post's `plannerUrl`.
6. Append to `published.yaml` one entry per post: slug, date, platform, `scheduled` (slot dateTime),
   title, media URL, Metricool id/uuid, plannerUrl. Set the topic's status to `scheduled`. Commit + push.

## 9. Notify the owner
Send the finished video with SendUserFile (status: proactive, display: render) and a short
SendUserMessage: the title, when it goes live (e.g. "Fri 10:00 AM"), the platforms, the Metricool
planner link(s), the topic queued next, and "To cancel, open the link and delete the post before
<time>." If anything failed, say exactly what and what is needed from him. Nothing else.

## 10. Don'ts
- No real people's likenesses, no brand logos, no copyrighted footage/music.
- No medical/financial/legal claims; stick to how mechanisms work.
- Don't repeat a topic; vary hooks. Two videos a day must still be distinct, substantive topics.
