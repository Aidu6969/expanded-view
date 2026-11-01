"""Episode 7 — How a sewing machine makes a lockstitch (rotary hook, bobbin, take-up lever, feed dogs)."""
from ev.gfx import INK, RED

SLUG = "sewing-machine"
TOPIC = "LOCKSTITCH"
SUBTITLE = ["Two threads, locked together", "in the middle of the fabric"]
PUNCH = ("DOWN, LOOP,", "HOOK, PULL.")
HOOK_TITLE = [[("HOW A ", INK), ("SEWING MACHINE", RED)], [("ACTUALLY SEWS", INK)]]
END_WORD = ("outro", "down,")
TOPIC_WORD = ("outro", "lockstitch")

LINES = [
    ("hook",    "A sewing machine never pulls its needle through the cloth. So how does it sew?"),
    ("what",    "This is how a sewing machine works. It makes a lockstitch, with two threads. "
                "One comes from the top, and one from a bobbin hidden underneath."),
    ("problem", "By hand, you push the whole needle through and pull it out the other side. "
                "A machine never lets go of its needle, so the eye sits right at the point."),
    ("parts",   "Under the plate, a spinning hook surrounds the bobbin case. "
                "Up top, a take up lever controls the thread."),
    ("down",    "The needle pushes the top thread down through the fabric. "
                "As it starts to rise, the thread puffs out into a small loop."),
    ("key",     "The hook's point snags that loop, and drags it all the way around the bobbin case. "
                "Now the top thread is wrapped around the bottom one."),
    ("tight",   "The take up lever yanks upward and pulls the loop shut, "
                "so the two threads lock together inside the fabric."),
    ("feed",    "Then the feed dogs drag the cloth forward one stitch, and it all happens again. "
                "The hook spins twice for every single stitch."),
    ("outro",   "Down, loop, hook, pull. That's a lockstitch."),
]
GAPS = {"what": 0.2, "problem": 0.25, "parts": 0.25, "down": 0.25, "key": 0.3, "tight": 0.3, "feed": 0.25,
        "outro": 0.35}

META = {
    "title": "How a sewing machine works: the knot you never see #sewing #howitworks #engineering",
    "description": (
        "A sewing machine can't pass its needle all the way through the cloth, so it makes a lockstitch from two "
        "threads instead: the top thread through the needle, whose eye is right at the point, and a lower thread "
        "from a bobbin underneath. The needle carries the top thread down through the fabric; as it starts to rise "
        "the thread forms a small loop. The point of the rotary hook catches that loop and carries it around the "
        "bobbin case, so the top thread ends up wrapped around the bobbin thread.\n\n"
        "The take-up lever then pulls the slack back up, drawing the two threads together so they interlock inside "
        "the fabric, and the feed dogs move the cloth along by one stitch. On a full rotary hook like the one shown, "
        "the hook turns twice for each stitch. Animation simplified and slowed down.\n\n"
        "What should we take apart next? 👇\n#SewingMachine #HowItWorks #Lockstitch"
    ),
    "tags": ["how a sewing machine works", "sewing machine", "lockstitch", "how a lockstitch works", "bobbin",
             "rotary hook", "sewing machine mechanism", "how does a sewing machine work", "sewing",
             "engineering animation", "how it works"],
    "first_comment": "Next up: the oil field pumpjack, what your clutch pedal actually does, or how oil reaches every "
                     "part of your engine? Vote below 👇",
    "tiktok_caption": "How a sewing machine works: it ties a knot you never see 🧵 #sewing #sewingmachine "
                      "#howitworks #engineering #lockstitch",
    "sources": [
        "https://en.wikipedia.org/wiki/Lockstitch",
        "https://www.firgelliauto.com/blogs/mechanisms/sewing-machine-rotary-hook",
        "https://en.wikipedia.org/wiki/Sewing_machine",
    ],
}
