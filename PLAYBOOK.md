# Expanded View — production playbook (for scheduled runs)

You are producing ONE new Expanded View short and scheduling it. Expanded View is a faceless
YouTube Shorts + TikTok channel (@expandedview) of animated "how things actually work" explainers.
Episode 1 (`episodes/vtec`) is the reference: match its quality, accuracy, pacing and look.

Owner: Ahadu. He reviews posts during a 3-hour cancel window. Never post anything you would not
defend as accurate.

---------------------------------------------------------------------------------------------------
## GOAL: get Expanded View into both paid programs. Every decision serves this.
Targets (checked Oct 2026; re-check monthly):
- **YouTube Partner Program (ad revenue):** 1,000 subscribers + 10M public Shorts views in 90 days
  (or 4,000 long-form watch hours in 12 months). **From Feb 1, 2027 new applicants need 20M Shorts
  views in 90 days (or 8,000 hours)**; channels already accepted are grandfathered. So: qualify before
  Feb 1, 2027 if at all possible. After that date Shorts ad revenue also needs 10M Shorts views/90 days.
  Lower YPP tier (fan funding, no ad revenue): 500 subs + 3 uploads in 90 days + 3M Shorts views/90 days.
- **TikTok Creator Rewards:** 10,000 followers + 100,000 views in the last 30 days, personal account,
  18+, original videos over 1 minute. Pay per 1,000 qualified views depends on **originality, play
  duration, search value and audience engagement**: optimise all four.
- **The biggest risk is YouTube's "inauthentic content" policy** (clarified July 2026): channels whose
  videos look template-made "with little to no variation" are refused or demonetised. Our fixed brand
  (voice, look, ending) is fine; the SUBSTANCE must differ every time. The YPP review is done by people
  looking at the whole channel, so every upload must be one you would show a reviewer.

What that means for each run:
1. **Topic:** Expanded View is a VEHICLE channel (owner, 2026-11-01): cars first, plus anything with an engine
   or wheels (trucks, planes, bikes). Never build a household, industrial or other non-vehicle topic, even if
   it is queued or trending; skip it and tell the owner. Within that scope, pick things people already search
   for and watch (topics.yaml is ordered by proven demand).
   **Fan-favourite first (owner, 2026-11-01):** VTEC beat every other video on both platforms. Prefer legendary
   engines and car-culture questions with real fan bases (2JZ, LFA V10, RB26, rotary, boxer rumble, anti-lag...).
   Hook on the myth or argument fans already have ("Everyone says ..."), then show the real mechanism.
   Name engines freely, but no badges/logos and no downloaded recordings of real cars; engine sounds are realistic
   generated clips of a generic engine type (`SFX_PROMPTS`, see section 5).
2. **Hook (first 2 s):** motion on screen from frame 1 plus a concrete, surprising claim or question
   ("How do you drive a 50-ton steel pile into the ground?"). Never open on a slow fade or a definition.
   **Open-loop rule (owner, 2026-11-03, from YouTube retention data):** the first line must be an open question
   or a myth that the video does NOT answer until the key moment (VTEC: "Everyone says VTEC kicked in. But
   what's actually kicking in?" kept 94% of viewers at the halfway point and 69% at the end). A plain fact as
   the hook followed by a definition (turbo: "Your exhaust can spin this..." then "A turbocharger is two
   wheels on one shaft") lost ~40% of viewers between seconds 6 and 15 and stalled at ~1,500 views.
   So: no definition or "X is ..." sentence before ~10 s; line 2 restates the stakes ("Here's what's really
   happening") instead of explaining; re-hook around 25-35 s with a second question ("So why 72 degrees?");
   the payoff of the opening question lands in the key beat, not earlier.
   **Real-world opening (owner, 2026-11-03):** the first 2–3 s show the thing in its real setting (a semi-truck
   on a downhill grade, a car's headlights on a dark road, a hand with a key fob at a door), drawn in our style,
   THEN cut/x-ray inside to the mechanism. Viewers recognise their own world before the diagram starts.
   Prefer "your car..." hooks for everyday topics ("Your fuel gauge is lying to you, on purpose").
3. **Retention:** a new visual event every 2–3 s; reveal the key moment late enough to hold viewers; no
   dead air; the 61–75 s length is required for TikTok pay, so it must earn every second.
4. **Originality (both platforms):** a custom-modelled animation of THIS mechanism, a script with real
   explanation (the why, not a list of parts), a hook and visual structure that differ from the last
   5 episodes (check `published.yaml` + their episode.py). Never reuse another channel's footage,
   script, title or exact hook.
5. **Search value:** the YouTube title and TikTok caption contain the phrase people actually search
   ("how a manual transmission works"), plus curiosity. Say that phrase early in the narration too.
6. **Engagement:** YouTube first comment asks a real question (pick-the-next-topic works); the
   description ends with a question.
7. **Quality over count:** two a day only while every video passes the QA gate. A skipped day costs
   less than a weak upload sitting on the channel when a reviewer looks.

---------------------------------------------------------------------------------------------------
## 0. Fixed brand — NEVER change per episode
- **NARRATOR PAUSE (owner, 2026-11-05):** ElevenLabs is paused until its API key reaches the task environment.
  `ev/voice.py DEFAULT_BACKEND = "kokoro"`: posted videos use the old Kokoro voice (`am_michael`, the voice of the
  first 8 episodes) and our own synthesized SFX stand-ins (`ev/sfx.py`); the build's QA accepts them. Everything else
  in this playbook is unchanged. When the owner says ElevenLabs works, set `DEFAULT_BACKEND = "elevenlabs"` and the
  rules below (Brian, realistic SFX) apply again.
- **Voice (owner, 2026-11-03):** ElevenLabs "Brian" (voice B), `ev/voice.py`, for EVERY video, Shorts and long-form.
  Never swap voices, never fall back to the old Kokoro voice for anything that gets posted (`EV_VOICE=kokoro` is
  for local previews only and fails QA). Lines are generated with the neighbouring lines as context, and word
  times come from ElevenLabs' alignment, so captions are exact. Pronunciation: captions keep the real spelling;
  `voice.LEXICON` + the episode's `SAY` dict respell what the narrator says (check with
  `python -c "from ev import voice; print(voice.phonemes('...'))"`). Add any new acronym or name to `SAY`.
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
  Brian speaks ~2.5 words/s, so that is roughly 150–180 words; trust the build's duration, not the word count.
- **Sound:** narration + our own synthesized music bed + REALISTIC sound effects (`ev/sfx.py`: house library
  `ev/sfx/*.wav` + episode clips from `SFX_PROMPTS`, all made with the ElevenLabs Sound Effects API and committed
  so they are made once). The old synthesized SFX and engine note are retired. -14 LUFS. No licensed music, no AI music.
- **Loop ending (automatic):** the last 0.45 s cross-fades into frame 0, so a replay looks seamless (rewatches count).
- **Series label:** engine/car-culture episodes set `SERIES = ("LEGENDARY ENGINES", <n>)` (n = count of
  published episodes in the series + 1); it shows above the hook title. Other topics: `SERIES = ("HOW IT WORKS", n)`.
- **Search phrase on screen:** `HOOK_TITLE` must contain the phrase people type (TikTok and YouTube read on-screen
  text): "WHY THE LFA SOUNDS LIKE THAT", "HOW A CLUTCH ACTUALLY WORKS".

---------------------------------------------------------------------------------------------------
## 1. Setup (fresh workspace every run)
1. Attach the repos with `mcp__claude-code-remote__add_repo` (access `push`): first owner `Aidu6969`,
   repo `expanded-view` (PRIVATE engine repo: run the clone command it returns and `cd` into it), then
   repo `expanded-view-media` (PUBLIC, videos only: attach it, no need to clone; `tools/publish_media.sh`
   pushes to it). If `add_repo` is missing or the media repo can't be attached, carry on: the engine repo
   is normally already cloned in the working directory, and `publish_media.sh` falls back automatically
   (step 8.2). A missing media repo is NOT a reason to stop (owner decision, 2026-10-31).
2. `bash setup.sh` (Python deps, voice model; brand fonts are bundled in `ev/fonts`).
   **Narrator check (must pass; with the Kokoro pause it just checks the voice model):** `python -c "from ev import voice; print(voice.check_configured())"`.
   If it raises NarratorNotConfigured: do NOT build or post. Set the next topic to `needs_review` only if you
   started it, and notify the owner with the exact message plus "see docs/SETUP_ACCOUNTS.md step 1". Stop.
   **Sound library:** if `ev/sfx/` has no .wav files, run `python -m ev.sfx --library` once and commit `ev/sfx/`.
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
  around the key moment. Engine/mechanical sounds: declare realistic clips in `SFX_PROMPTS = {name: (prompt, seconds)}`
  (generic engine type, e.g. "high revving naturally aspirated V10, free rev to 9000 rpm, exterior, no music"), use
  them as sfx cues, and commit `episodes/<slug>/sfx/`. The `engine` key (synth note) is ignored.

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
   It force-pushes the video to the public repo `Aidu6969/expanded-view-media` (last 4 days of videos
   only) and prints the public URL `https://raw.githubusercontent.com/Aidu6969/expanded-view-media/main/<file>.mp4`,
   checking it returns 200. Never put anything but finished videos in that repo.
   **Fallback (automatic, owner-approved for autonomy):** if the media repo can't be reached, the script
   pushes to the orphan `media` branch of `Aidu6969/expanded-view` instead and prints that URL
   (`https://raw.githubusercontent.com/Aidu6969/expanded-view/media/<file>.mp4`). Use whatever URL it prints.
   Only stop if the script fails or the printed URL is not HTTP 200.
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
                      "category": "SCIENCE_TECHNOLOGY", "madeForKids": false, "isAiGeneratedContent": false}}
     ```
   - TikTok (only if connected):
     ```json
     {"autoPublish": true, "draft": false, "descendants": [], "hasNotReadNotes": false, "shortener": false,
      "smartLinkData": {"ids": []}, "mediaAltText": [], "firstCommentText": "",
      "providers": [{"network": "tiktok"}], "media": ["<raw URL>"],
      "publicationDate": {"dateTime": "<slot dateTime>", "timezone": "America/New_York"},
      "text": "<META.tiktok_caption>",
      "tiktokData": {"title": "<META.tiktok_caption>", "privacyOption": "PUBLIC_TO_EVERYONE", "disableComment": false, "disableDuet": false,
                     "disableStitch": false, "commercialContentThirdParty": false,
                     "commercialContentOwnBrand": false, "autoAddMusic": false, "isAigc": false}}
     ```
   TikTok rejects the post without `tiktokData.title` (use the caption). Metricool copies the video to its
   own storage when the post is created, so the `media` branch only has to serve it at scheduling time.
   AI labels are OFF (owner's decision). That is within both platforms' rules only because the videos are
   clearly animated and the narrator is a generic voice: YouTube requires disclosure only for realistic
   content (real people saying/doing things they didn't, realistic events, AI music as the focus); TikTok
   for realistic AI people/scenes or a recognisable person's voice. Never use realistic footage of real
   people or events, cloned voices or AI music. If a topic would need any of that, skip it.
   Do not send `videoThumbnailUrl`/`videoCoverMilliseconds` (rejected on this channel).
   If a call errors, read the error, fix the field it names, retry once; never change the wording of
   the text to get around an error. If the error is about the Metricool plan's post limit (the Free plan
   allows 20 posts a month; each platform post counts), do not retry: keep the video, set the topic to
   `ready`, and tell the owner the monthly limit was reached.
5. Verify with `getScheduledPosts` (that day, America/New_York) that both posts are there with
   autoPublish on. Keep each post's `plannerUrl`.
6. Append to `published.yaml` one entry per post: slug, date, platform, `scheduled` (slot dateTime),
   title, media URL, Metricool id/uuid, plannerUrl. Set the topic's status to `scheduled`. Commit + push.

### 8b. YouTube direct upload (when configured) and the YouTube cut
- If `python tools/youtube_upload.py --check` prints `"ok": true`, upload the YouTube Short directly instead of the
  Metricool YouTube post: `python tools/youtube_upload.py <mp4> --meta episodes/<slug>/episode.py --publish-at <slot iso>`.
  It goes up private and YouTube publishes it at the slot; the cancel link for the owner is the `studio` URL it prints.
  Record `platform: youtube, via: direct, videoId, studio` in published.yaml. TikTok always stays on Metricool.
  If the check fails, use Metricool for YouTube as before (and mention the reason once in the owner message).
- **YouTube cut A/B (owner, 2026-11-03):** every second episode (even count in published.yaml) sets
  `YT_DROP = [<1-2 nice-to-have beats>]` in episode.py, runs `python tools/yt_cut.py episodes/<slug>` and posts
  `out/<slug>/<slug>_yt.mp4` (40–50 s) to YouTube; TikTok always gets the full 61–75 s video. Record `yt_cut: true`.
  The weekly review compares average % viewed of cut vs full episodes.

## 9. Notify the owner
Send the finished video with SendUserFile (status: proactive, display: render) and a short
SendUserMessage: the title, when it goes live (e.g. "Fri 10:00 AM"), the platforms, the Metricool
planner link(s), the topic queued next, and "To cancel, open the link and delete the post before
<time>." If anything failed, say exactly what and what is needed from him. Nothing else.

## 10. Don'ts
- No real people's likenesses, no brand logos, no copyrighted footage/music.
- No medical/financial/legal claims; stick to how mechanisms work.
- Don't repeat a topic; vary hooks. Two videos a day must still be distinct, substantive topics.

---------------------------------------------------------------------------------------------------
## 11. Long-form (YouTube only, owner 2026-11-03): one 8–12 min video a week
History of legendary cars, the cars enthusiasts actually buy, and comparisons (e.g. BMW M3 vs Mercedes E63 AMG).
Higher bar than Shorts: real cars on screen, deep research, chapters.
- **Folder:** `long/<slug>/` with `episode.py` (LINES = paragraphs, SHOTS, CHAPTERS, META, SAY, SFX), `research.md`
  (every fact sourced, myths section), `assets/manifest.yaml`. Builder: `python -m ev.long.build long/<slug>`
  (16:9, 1920x1080; `--stills` for a quick look). Reference: `long/honda-nsx`.
- **Footage: licensed only.** Wikimedia Commons photos (PD/CC0/CC BY/CC BY-SA) and Pexels clips, added with
  `python -m ev.long.assets ...` (it refuses NC/ND). Look at every photo before using it: right car, right
  generation, no people's faces as the subject, no watermark. Every photo/clip shows its credit on screen and the
  description lists all credits automatically. Never: clips from YouTube/TV/reviews, press kits that forbid
  monetised use, AI images of real cars. If a needed image doesn't exist under a free license, use a spec/
  timeline/fact card instead.
- **Script:** 1,300–1,700 words, open-loop cold open (a myth or question paid off near the end), 6–8 chapters,
  numbers only from research.md, uncertain claims attributed ("reportedly", "Honda says").
- **QA:** `"ok": true` (8–12 min, -14 LUFS, ElevenLabs voice), every shot's asset licensed, look at qa_sheet.jpg
  and 10+ stills across the video.
- **Publish:** direct YouTube upload (`--long --category AUTOS_VEHICLES`) when configured, otherwise Metricool
  YouTube post with `youtubeData.type: "video"`. Slot: Saturday 10:00 New York (at least 3 h ahead).
  Upload the .srt as captions later if the API allows; record in published.yaml with `format: long`.
