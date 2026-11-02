"""Episode 9 — Why the Lexus LFA V10 sounds like that (1LR-GUE). See research.md for every fact."""
from ev.gfx import INK, RED

SLUG = "lfa-v10"
TOPIC = "LFA V10"
SUBTITLE = ["72-degree V10, even firing,", "intake tuned by Yamaha's sound engineers"]
PUNCH = ("NOT JUST LOUD.", "TUNED.")
HOOK_TITLE = [[("WHY THE ", INK), ("LFA", RED)], [("SOUNDS LIKE THAT", INK)]]
END_WORD = ("outro", "it's")
TOPIC_WORD = ("outro", "lfa")

LINES = [
    ("hook",   "Legend says a needle tachometer couldn't keep up with this engine."),
    ("what",   "It's the four point eight litre V10 from the Lexus LFA. Here's why the LFA sounds like that."),
    ("light",  "To rev that fast, the moving parts are light. The valves are titanium, and every cylinder gets its "
               "own throttle, right at the intake."),
    ("angle",  "Now look at the angle between the two banks. Seventy two degrees. That's not random."),
    ("math",   "A four stroke engine needs two full turns, seven hundred twenty degrees, to fire every cylinder once. "
               "Divide by ten cylinders, and you get seventy two."),
    ("even",   "So a cylinder fires every seventy two degrees, evenly. No lumpy gaps, just one smooth, rising scream."),
    ("yamaha", "Then Yamaha's sound engineers tuned the intake. The surge tank is shaped to resonate like an "
               "instrument, and ducts carry that sound into the cabin."),
    ("key",    "Floor it, and it goes from idle to nine thousand RPM in about six tenths of a second. That's seven "
               "hundred fifty firings every second. Lexus gave it a digital tach."),
    ("outro",  "It's not just loud. It's tuned. That's the LFA V10."),
]
GAPS = {"what": 0.25, "light": 0.3, "angle": 0.3, "math": 0.25, "even": 0.25, "yamaha": 0.3, "key": 0.35,
        "outro": 0.3}

META = {
    "title": "Why the Lexus LFA sounds like that: the 72° V10 explained #lfa #lexus #v10",
    "description": (
        "The Lexus LFA's 1LR-GUE is a 4.8 litre V10 with its banks 72 degrees apart. A four-stroke engine fires "
        "every cylinder once per 720 degrees of crank rotation, so with ten cylinders and even firing, one fires "
        "every 72 degrees: no uneven gaps, one smooth rising note. Titanium valves and an individual throttle for "
        "each cylinder help it rev from idle to its 9,000 rpm redline in about 0.6 seconds, and the car uses an "
        "LCD tachometer.\n\n"
        "Yamaha's sound engineers did acoustic design for the engine: the intake surge tank was designed to "
        "radiate sound, and ducts carry it into the cabin. Animation simplified and slowed; 750 firings a second "
        "is simply 9,000 rpm x 5 firings per crank turn.\n\n"
        "What's the best-sounding engine ever made? 👇\n#LexusLFA #V10 #HowItWorks"
    ),
    "tags": ["lexus lfa", "lfa v10", "why the lfa sounds like that", "1lr-gue", "lexus lfa sound", "v10 engine",
             "72 degree v10", "even firing", "yamaha", "engine sound explained", "engine animation"],
    "first_comment": "Next legend: the RB26, the rotary, or the flat-plane Ferrari V8? Vote below 👇",
    "tiktok_caption": "Why the Lexus LFA sounds like that: the 72° V10 explained 🔊 #lexuslfa #v10 #cartok #engine #jdm",
    "sources": [
        "https://en.wikipedia.org/wiki/Toyota_LR_engine",
        "https://archive.yamaha.com/en/news_release/2009/20091021.html",
        "https://media.lexus.co.uk/sounds-spectacular/",
        "https://www.jalopnik.com/2070065/lexus-lfa-exhaust-note-physics/",
        "https://en.wikipedia.org/wiki/Four-stroke_engine",
    ],
}
