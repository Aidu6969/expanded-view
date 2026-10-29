"""Episode 1 — How VTEC actually works. Reference episode: copy its structure for new episodes."""
from ev.gfx import INK, RED

SLUG = "vtec"
TOPIC = "VTEC"                                            # big red word on the end card ("That's VTEC.")
SUBTITLE = ["Variable Valve Timing & Lift", "Electronic Control"]   # under the end-card title (1-2 short lines)
PUNCH = ("TWO CAMS", "IN ONE.")                           # end-card punchline: line 1 white, line 2 red
HOOK_TITLE = [[("HOW ", INK), ("VTEC", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "two")       # word where the punchline card starts ("Two cams in one.")
TOPIC_WORD = ("outro", "vtec")    # word where the big topic title appears ("That's VTEC.")

# Narration, one entry per beat. Natural spoken sentences; ~170-185 words -> 62-70 s.
LINES = [
    ("hook",   "Everyone says VTEC kicked in. But what's actually kicking in?"),
    ("name",   "VTEC stands for Variable Valve Timing and Lift Electronic Control, and it fixes a classic tradeoff."),
    ("trade",  "A mild cam idles smooth and saves fuel. An aggressive cam opens the valves wider and longer for big power up top, but it idles rough. One cam can't do both."),
    ("lobes",  "So Honda gave each pair of valves three cam lobes. Two mild ones outside, and a tall one in the middle, each with its own rocker arm."),
    ("free",   "Only the outer rockers push the valves. The middle one just swings freely."),
    ("low",    "At low RPM, the valves follow the mild lobes."),
    ("switch", "But high in the rev range, with the engine warm and under load, the computer opens a solenoid. Oil pressure pushes pins through all three rockers, locking them together."),
    ("high",   "Now they all follow the big middle lobe. That means more lift, longer duration, and more power."),
    ("outro",  "When revs drop, a spring pushes the pins back, and you're on the mild cam again. Two cams in one. That's VTEC."),
]
GAPS = {"name": 0.22, "trade": 0.20, "lobes": 0.25, "free": 0.18, "low": 0.18, "switch": 0.45, "high": 0.22, "outro": 0.22}

META = {
    "title": "What happens when VTEC kicks in? #honda #jdm #engineering",
    "description": (
        "Everyone says \"VTEC kicked in,\" but what actually kicks in? Honda gives each pair of valves three cam "
        "lobes. At high RPM, oil pressure pushes pins through all three rocker arms and locks them to the tall lobe, "
        "giving the valves more lift and longer duration.\n\n"
        "VTEC = Variable Valve Timing and Lift Electronic Control. The animation is slowed down to show the "
        "mechanism; the switch point varies by engine and load.\n\n"
        "What should we take apart next? 👇\n#VTEC #HowItWorks #CarTech"
    ),
    "tags": ["vtec", "honda vtec", "how vtec works", "vtec explained", "variable valve timing", "camshaft",
             "rocker arm", "engine animation", "how engines work", "jdm"],
    "first_comment": "Turbo, manual gearbox, or limited-slip diff: what should Expanded View take apart next?",
    "tiktok_caption": "What actually happens when VTEC kicks in 🔧 #vtec #honda #howitworks #cartok #engineering",
    "sources": ["https://en.wikipedia.org/wiki/VTEC"],
}
