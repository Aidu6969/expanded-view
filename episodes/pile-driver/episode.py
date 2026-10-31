"""Episode 5 — How a diesel pile hammer drives a steel pile into the ground (single-acting / open-top)."""
from ev.gfx import INK, RED

SLUG = "pile-driver"
TOPIC = "DIESEL HAMMER"
SUBTITLE = ["A free-piston two-stroke diesel", "that hammers a pile into the ground"]
PUNCH = ("FALL, SQUEEZE,", "BANG, BOUNCE.")
HOOK_TITLE = [[("HOW A ", INK), ("PILE DRIVER", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "fall,")
TOPIC_WORD = ("outro", "diesel")

LINES = [
    ("hook",    "How do you pound a steel pile into the ground? Turn the hammer into an engine."),
    ("what",    "This is how a diesel pile driver works. It's a giant two stroke diesel engine, "
                "and its piston is a heavy ram that flies free."),
    ("problem", "Lifting a huge weight with a crane for every blow would be painfully slow. "
                "So this hammer lifts itself."),
    ("parts",   "The ram sits in a tall cylinder. At the bottom, an impact block rests on the pile. "
                "On the side, a fuel pump, and exhaust ports in the wall."),
    ("start",   "To start it, the crane lifts the ram, and a trip lets it go."),
    ("fall",    "As it falls, the ram presses the fuel pump lever, and diesel squirts onto the impact block. "
                "Then the ram covers the ports, trapping the air below it."),
    ("key",     "That air gets squeezed until it's hot. The ram slams the block, splashing the fuel into a mist, "
                "and it ignites. Bang."),
    ("result",  "The blast pushes both ways. It drives the pile down, and throws the ram back up the cylinder."),
    ("rise",    "The ram passes the ports, exhaust escapes, fresh air rushes in, and gravity brings it back down. "
                "No crankshaft, no spark plug. It runs as long as it gets fuel."),
    ("outro",   "Fall, squeeze, bang, bounce. That's a diesel hammer."),
]
GAPS = {"what": 0.2, "problem": 0.2, "parts": 0.2, "start": 0.2, "fall": 0.2, "key": 0.3, "result": 0.2,
        "rise": 0.2, "outro": 0.3}

META = {
    "title": "How a pile driver works: the hammer is an engine #construction #engineering #diesel",
    "description": (
        "A diesel pile hammer is a giant two-stroke diesel engine whose piston is a free, heavy steel ram. To start "
        "it, the crane lifts the ram and a trip releases it. As the ram falls it works the fuel pump, which puts a "
        "measured shot of diesel onto the impact block, then it covers the exhaust ports and traps the air beneath it. "
        "The trapped air is compressed and heats up; the ram strikes the block, the fuel is atomised and ignites.\n\n"
        "The blast pushes both ways: it forces the impact block and the pile down and throws the ram back up. As the "
        "ram rises past the ports the exhaust escapes and fresh air is drawn in, then gravity brings it down for the "
        "next blow. It runs as long as it gets fuel. Single-acting (open-top) hammer shown; animation simplified and "
        "slowed down.\n\n"
        "What should we take apart next? 👇\n#PileDriver #HowItWorks #Construction"
    ),
    "tags": ["pile driver", "how a pile driver works", "diesel pile hammer", "diesel hammer", "pile driving",
             "how a diesel hammer works", "construction machines", "foundation piling", "two stroke diesel",
             "engineering animation", "how it works"],
    "first_comment": "Next up: where your gas goes after you fill up, how a sewing machine ties its knot, or the oil "
                     "field pumpjack? Vote below 👇",
    "tiktok_caption": "How a pile driver works: the hammer is a giant diesel engine 💥 #piledriver #construction "
                      "#howitworks #engineering #diesel",
    "sources": [
        "https://en.wikipedia.org/wiki/Pile_driver",
        "https://www.fhwa.dot.gov/publications/research/infrastructure/geotechnical/05159/chapter3.cfm",
        "https://www.sigmaplantfinder.com/blog/piling/diesel-hammer-work",
    ],
}
