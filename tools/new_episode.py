"""Scaffold a new episode:  python tools/new_episode.py <slug> "<TOPIC>"

Creates episodes/<slug>/{episode.py, scene.py, research.md} from templates that already follow the house
rules (fixed voice, brand layer, ending formula). Fill in the TODOs, then build with
    python -m ev.build episodes/<slug> --stills 1,8,20,35,50,62
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EPISODE = '''"""{topic} — episode for Expanded View. See PLAYBOOK.md section 4 for the script rules."""
from ev.gfx import INK, RED

SLUG = "{slug}"
TOPIC = "{topic}"                         # big red word on the end card ("That's {topic}.")
SUBTITLE = ["TODO one-line definition"]   # 1-2 short lines under the end-card title
PUNCH = ("TODO SHORT", "PUNCHLINE.")      # end-card punchline: line 1 white, line 2 red (spoken in the outro)
HOOK_TITLE = [[("HOW ", INK), ("{topic}", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "TODO")      # first word of the spoken punchline sentence in the outro line
TOPIC_WORD = ("outro", "TODO")    # the topic word in the final "That's {topic}." sentence

# Narration, one entry per beat (8-10 beats, ~165-190 words -> 61-75 s at the fixed voice).
# hook -> name/what -> problem -> parts -> how (steps) -> key moment -> result -> outro (undo + punchline + "That's X.")
LINES = [
    ("hook",  "TODO surprising claim or question, under four seconds."),
    ("what",  "TODO what it is, in one sentence."),
    ("problem", "TODO the problem it solves."),
    ("parts", "TODO the parts, named in the order they appear on screen."),
    ("how",   "TODO step one, step two."),
    ("key",   "TODO the key moment, the 'kicks in' beat."),
    ("result", "TODO what that gets you."),
    ("outro", "TODO how it undoes or recaps. TODO punchline sentence. That's {topic}."),
]
GAPS = {{}}   # optional extra pause before a line, e.g. {{"key": 0.4}}

META = {{
    "title": "TODO curiosity + keyword, <= 70 chars #tag1 #tag2 #tag3",
    "description": "TODO paragraph 1: the answer in plain facts.\\n\\nTODO paragraph 2: one nuance or caveat.\\n\\n"
                   "What should we take apart next? 👇\\n#HowItWorks #Engineering",
    "tags": ["TODO", "how it works", "engineering", "animation"],
    "first_comment": "TODO name 2-3 queued topics as a question",
    "tiktok_caption": "TODO <= 150 chars #howitworks #engineering #tag #tag",
    "sources": ["TODO url"],
}}
'''

SCENE = '''"""{topic} visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Structure (same as episodes/vtec/scene.py — read it first):
  1. cue times from the timeline (F/L) — never hard-code seconds
  2. deterministic per-frame state from a real model of the mechanism -> state(t)
  3. scene blocks, each visible in its own time window
  4. draw(cv, t) calls the blocks; sound() returns the audio plan
The brand layer (background, hook title, captions, end card) is drawn by ev.build — don't draw it here.
Safe area: x 60-940, y 150-1400. Hook title occupies y 230-450 until current.hook_out.
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic

# ================================================================== cue times
T_KEY = L("key")["start"]   # TODO tie to the exact word, e.g. F("key", "locks")


# ================================================================== mechanism model
def state(t):
    """TODO: positions/angles/flows at time t from real geometry (gear ratios, linkages, pressures)."""
    return {{}}


# ================================================================== scene blocks
PJ = Proj(540, 760, 1.0)   # ortho 3/4 view; X along the part, Y down, z depth/axis


def draw_hook(cv, t):
    a = 1 - ease(lin(t, current.hook_out, L("what")["start"] + 0.2))
    if a <= 0:
        return
    # TODO an arresting image under the hook title (gauge, lamp, the finished object, a close-up)


def draw_mechanism(cv, t, st):
    k = 1 - current.ending_k(t)          # fade out as the end card arrives
    a = ease(lin(t, L("parts")["start"] - 0.2, L("parts")["start"] + 0.4)) * k
    if a <= 0:
        return
    # TODO extrude()/vcyl()/frustum()/draw_spring() parts, far to near; reveal each when it is named


def draw_labels(cv, t):
    pass  # TODO brand.label(cv, t, "PART", anchor, label_pos, CYAN, F("parts", "part"), T_END)


def draw(cv, t):
    st = state(t)
    draw_hook(cv, t)
    draw_mechanism(cv, t, st)
    draw_labels(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_KEY
MUSIC_START = L("what")["start"]


def sound():
    sfx = [(current.hook_out - 0.1, "whoosh_big", 0.6),
           (L("parts")["start"] - 0.41, "whoosh_up", 0.45),
           (T_KEY, "impact", 0.5)]
    return {{"build": (L("how")["start"], T_KEY), "drop": (T_KEY, L("outro")["start"]), "sfx": sfx}}
'''

RESEARCH = '''# {topic} — research notes

Every fact the narration states, with a source. Unsure items and how they were resolved.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | TODO | TODO url |

## Misconceptions to avoid
- TODO

## Simplifications made on screen
- TODO (e.g. animation slowed, parts not to scale)
'''


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    slug, topic = sys.argv[1], sys.argv[2].upper()
    d = os.path.join(ROOT, "episodes", slug)
    if os.path.exists(d):
        sys.exit(f"{d} already exists")
    os.makedirs(d)
    for name, tpl in (("episode.py", EPISODE), ("scene.py", SCENE), ("research.md", RESEARCH)):
        with open(os.path.join(d, name), "w") as fh:
            fh.write(tpl.format(slug=slug, topic=topic))
    print(f"created {d}/episode.py, scene.py, research.md")


if __name__ == "__main__":
    main()
