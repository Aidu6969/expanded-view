"""Episode: why Subarus rumble. See research.md for every fact.
Open loop: "Everyone says that Subaru rumble is just the boxer engine. It isn't. So what's actually making it?" is
paid off in the key beat (pulses leave evenly, arrive unevenly). Different structure from the last five: a live pulse
timeline driven by real pipe lengths, plus a synthesized rumble that audibly changes when the pipes change."""
from ev.gfx import INK, RED

SLUG = "boxer-rumble"
TOPIC = "BOXER RUMBLE"
SERIES = ("LEGENDARY ENGINES", 6)
SUBTITLE = ["Even bangs, uneven pipes,", "a lumpy beat at the turbo"]
PUNCH = ("THE BANGS ARE EVEN.", "THE PIPES AREN'T.")
HOOK_TITLE = [[("WHY ", INK), ("SUBARUS", RED)], [("RUMBLE", INK)]]
END_WORD = ("outro", "bangs")
TOPIC_WORD = ("outro", "boxer")

LINES = [
    ("hook",   "Everyone says that Subaru rumble is just the boxer engine. It isn't. So what's actually making it?"),
    ("what",   "Here's what's really behind the boxer rumble."),
    ("how",    "Inside, four pistons punch out in opposing pairs, and they fire perfectly evenly, one bang every half "
               "turn of the crank. On paper, it should sound as smooth as any four cylinder."),
    ("rehook", "So if the bangs are even, where's the rumble coming from?"),
    ("parts",  "Follow the exhaust. Each cylinder gets its own pipe, and they all have to meet at the turbo, tucked in "
               "near one side of the engine."),
    ("key",    "One side's pipes snake under the engine, the long way around. The other side is only inches away. "
               "So the pulses leave evenly, but they arrive unevenly. A short gap, then a long gap. "
               "That lumpy beat is the rumble."),
    ("result", "The twenty fifteen WRX switched to equal length pipes to feed a twin scroll turbo. The pulses lined up, "
               "and most of the rumble went away."),
    ("keep",   "The STI kept the old pipes through twenty twenty one. And you can still buy unequal pipes for the new "
               "cars, just to bring it back."),
    ("outro",  "The bangs are even. The pipes aren't. That's boxer rumble."),
]
GAPS = {"what": 0.15, "how": 0.2, "rehook": 0.2, "parts": 0.2, "key": 0.2, "result": 0.55, "keep": 0.25, "outro": 0.3}
SAY = {"WRX": "W R X", "STI": "S T I"}

META = {
    "title": "Why Subarus rumble: the boxer rumble explained #subaru #wrx #boxer",
    "description": (
        "The Subaru rumble isn't just the boxer engine. A flat-four fires evenly, one cylinder every 180 degrees of "
        "crank rotation. The burble comes from the unequal-length exhaust headers: one bank's pipes run under the "
        "engine to reach the turbo while the other bank is only inches away, so pulses that leave evenly reach the "
        "collector unevenly.\n\n"
        "The 2015 WRX moved to equal-length headers to feed a twin-scroll turbo cleanly, which leaves a much smoother "
        "note (not perfectly silent: some rumble remains). The WRX STI kept unequal-length headers through 2021, and "
        "unequal-length headers are sold for the newer cars. Animation simplified and slowed, timing shift exaggerated "
        "so you can see it; all sounds in this video are synthesized.\n\n"
        "Rumble or smooth: which would you pick?"
    ),
    "tags": ["boxer rumble", "why do subarus rumble", "subaru rumble", "unequal length headers", "equal length headers",
             "wrx sound", "wrx sti", "boxer engine", "flat four", "subaru exhaust", "how cars work"],
    "first_comment": "Next up: how ABS stops a skid, how anti-lag spits fire, or flat-plane vs cross-plane V8s? Vote below",
    "tiktok_caption": "Why do Subarus rumble? It's not just the boxer engine. Boxer rumble explained #subaru #wrx #boxerrumble #cartok #howitworks",
    "sources": [
        "https://en.wikipedia.org/wiki/Flat-four_engine",
        "https://jalopnik.com/1933843/subaru-unequal-header-length-exhaust-sound/",
        "https://www.slashgear.com/1970710/subaru-unequal-length-headers-rumble-sound",
        "https://www.motorauthority.com/news/1104225_that-subaru-rumble-heres-why-that-happens",
        "https://thinktuning.com/wrx-unequal-length-headers/",
        "https://carnoise.substack.com/p/dat-sweet-rumble-tho",
    ],
}
