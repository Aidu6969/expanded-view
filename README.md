# Expanded View

Animated "how things actually work" shorts for YouTube Shorts and TikTok (@expandedview).
Every video uses the same voice, look and ending; only the topic changes.

```
ev/            engine: drawing toolkit (gfx), brand layer (brand), narration timing (timeline),
               fixed voice (voice), soundtrack (audio), build + QA (build), fonts (SIL OFL)
episodes/      one folder per video: episode.py (script + metadata), scene.py (visuals + sound plan),
               research.md (facts with sources). episodes/vtec is the reference episode.
topics.yaml    the queue, in priority order
published.yaml what has been posted or scheduled
media/         finished MP4s (served publicly so the scheduler can fetch them)
PLAYBOOK.md    the step-by-step instructions each scheduled run follows
tools/         new_episode.py scaffolds an episode from templates
```

```bash
bash setup.sh
python tools/new_episode.py turbocharger TURBO
python -m ev.build episodes/turbocharger --stills 1,8,20,35,50,62
python -m ev.build episodes/turbocharger
```

Output: `out/<slug>/<slug>.mp4` (1080x1920, 30 fps, -14 LUFS), `qa_sheet.jpg`, `meta.json`.
