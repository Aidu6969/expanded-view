"""Episode 4 — How a four-stroke engine actually works (intake, compression, power, exhaust)."""
from ev.gfx import INK, RED

SLUG = "four-stroke"
TOPIC = "FOUR STROKES"
SUBTITLE = ["Intake, compression, power, exhaust:", "two crank turns per cycle"]
PUNCH = ("SUCK, SQUEEZE,", "BANG, BLOW.")
HOOK_TITLE = [[("HOW A ", INK), ("4-STROKE ENGINE", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "suck")
TOPIC_WORD = ("outro", "four")

LINES = [
    ("hook",     "At three thousand RPM, each cylinder fires twenty five times a second."),
    ("what",     "Slowed way down, this is how a four stroke engine works. Four strokes of the piston, "
                 "two turns of the crank."),
    ("parts",    "The piston slides in the cylinder. A connecting rod links it to the crankshaft, turning up and down "
                 "into rotation. Up top, two valves and a spark plug."),
    ("intake",   "Stroke one, intake. The intake valve opens, the piston drops, and it pulls in air and fuel."),
    ("compress", "Stroke two, compression. Both valves close, and the piston squeezes that mixture into a space "
                 "about ten times smaller."),
    ("key",      "Stroke three, power. Just before the top, the spark plug fires. The burning gas expands and shoves "
                 "the piston down. It's the only stroke that makes power."),
    ("exhaust",  "Stroke four, exhaust. The exhaust valve opens, and the piston pushes the burnt gas out."),
    ("cam",      "A heavy flywheel carries the crank through the other three. And the camshaft turns at half "
                 "speed, so each valve opens once every two turns."),
    ("outro",    "Nikolaus Otto built the first practical one in eighteen seventy six. Suck, squeeze, bang, blow. "
                 "That's four strokes."),
]
GAPS = {"what": 0.25, "parts": 0.25, "intake": 0.3, "compress": 0.25, "key": 0.3, "exhaust": 0.3, "cam": 0.3,
        "outro": 0.3}

META = {
    "title": "How a 4-stroke engine works, slowed way down #engine #cars #engineering",
    "description": (
        "A four-stroke engine needs four strokes of the piston, and two full turns of the crankshaft, for every "
        "power pulse. Intake: the intake valve opens and the falling piston pulls in air and fuel. Compression: both "
        "valves shut and the piston squeezes the mixture. Power: the spark plug fires just before the top, and the "
        "expanding gas drives the piston down. Exhaust: the exhaust valve opens and the piston pushes the burnt gas "
        "out.\n\n"
        "The camshaft turns at half crank speed, so each valve opens once per cycle, and the flywheel carries the "
        "crank through the three strokes that don't make power. Single cylinder shown; animation slowed and "
        "simplified (real valve timing overlaps a little).\n\n"
        "Which stroke did you not know about? 👇\n#FourStroke #HowItWorks #CarTech"
    ),
    "tags": ["four stroke engine", "how a 4 stroke engine works", "4 stroke engine", "how an engine works",
             "otto cycle", "intake compression power exhaust", "suck squeeze bang blow", "piston engine",
             "camshaft", "engine animation", "how cars work"],
    "first_comment": "Next up: the clutch, the differential, or how a diesel pile hammer drives steel into the ground? Vote below 👇",
    "tiktok_caption": "How a 4-stroke engine works: suck, squeeze, bang, blow, slowed way down 🔥 #engine #cartok #howitworks #engineering #mechanic",
    "sources": [
        "https://en.wikipedia.org/wiki/Four-stroke_engine",
        "https://www.britannica.com/technology/four-stroke-cycle",
        "https://en.wikipedia.org/wiki/Ignition_timing",
        "https://en.wikipedia.org/wiki/Camshaft",
        "https://en.wikipedia.org/wiki/Compression_ratio",
        "https://en.wikipedia.org/wiki/Otto_engine",
    ],
}
