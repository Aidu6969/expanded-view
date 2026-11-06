"""Episode: How a fuel gauge works, and why it reads full for miles. See research.md for every fact.
Open loop: "Your fuel gauge is lying to you, on purpose. So what's it hiding?" is paid off in the key beats: hidden
fuel at BOTH ends of the dial (a deliberate "full reserve" above F, and a real empty point below E that isn't
marked). Different structure from the last five: night gas-station opening, a float + resistor sender cutaway,
a slosh / averaging signal graph, and a needle-vs-fuel calibration curve."""
from ev.gfx import INK, RED

SLUG = "fuel-gauge"
TOPIC = "FUEL GAUGE"
SERIES = ("HOW IT WORKS", 3)
SUBTITLE = ["A float, a resistor and a needle", "tuned to tell you what you asked for"]
PUNCH = ("IT'S TELLING YOU", "WHAT YOU ASKED FOR.")
HOOK_TITLE = [[("YOUR FUEL GAUGE", INK)], [("IS LYING TO YOU", RED)]]
END_WORD = ("outro", "it's")
TOPIC_WORD = ("outro", "fuel")

LINES = [
    ("hook",    "Your fuel gauge is lying to you. On purpose. So what's it hiding?"),
    ("what",    "Something at both ends of the dial. Here's how a fuel gauge actually works."),
    ("sender",  "Inside the tank, a float rides on top of the fuel. It sits on a long arm, and the arm drags a "
                "wiper across a strip of resistors."),
    ("how",     "Fuel goes down, the float sinks, the resistance changes, and the car turns that into the needle "
                "you see."),
    ("slosh",   "But fuel sloshes every time you brake or turn. So the gauge averages the signal, and the needle "
                "moves slowly on purpose."),
    ("rehook",  "So why does it sit on full for miles, then race toward empty?"),
    ("key",     "Part of it is the float. In a full tank it's pinned at the top, so the first gallons don't move "
                "it. The rest is tuning. Drivers told carmakers they like it, so it reads full before the tank "
                "is full, and stays there. Ford aims for around twenty or thirty miles."),
    ("empty",   "And empty isn't empty either. There's no secret reserve tank. The real empty point just isn't "
                "marked on the dial."),
    ("outro",   "So your gauge isn't broken. It's telling you what you asked for. That's the fuel gauge."),
]
GAPS = {"what": 0.2, "sender": 0.3, "how": 0.25, "slosh": 0.3, "rehook": 0.3, "key": 0.35, "empty": 0.3,
        "outro": 0.3}
SAY = {}
YT_DROP = ["how", "slosh"]

META = {
    "title": "Your fuel gauge is lying to you (on purpose): how a fuel gauge works #cars #fuelgauge #howitworks",
    "description": (
        "A fuel gauge reads a float in the tank. The float rides on the fuel at the end of an arm, and the arm "
        "moves a wiper across a resistor, so the resistance changes with the fuel level and the car turns that "
        "into the needle position. Because fuel sloshes when you brake and turn, the reading is averaged over "
        "time, so the needle moves slowly on purpose.\n\n"
        "Why it sits on full: in a full tank the float is already at the top of its travel, and carmakers tune "
        "the gauge to read full slightly before the tank is full and stay there for a while, because drivers "
        "said they like it. A Ford fuel-system engineer told NPR they target roughly 20 to 30 miles. Empty "
        "isn't really empty either: there's no separate reserve tank, the real empty point just isn't marked. "
        "Don't make a habit of running it dry. Animation simplified.\n\n"
        "Does your gauge stay on full for ages, or drop right away?"
    ),
    "tags": ["fuel gauge", "how a fuel gauge works", "why does my gas gauge stay on full", "gas gauge",
             "fuel sending unit", "fuel level sensor", "car facts", "how cars work", "car mysteries",
             "engineering explained"],
    "first_comment": "Next up: matrix headlights that dodge other drivers, the Mazda rotary, or how keyless entry "
                     "knows the key is in your pocket? Vote below",
    "tiktok_caption": "Your fuel gauge is lying to you, on purpose. How a fuel gauge actually works #fuelgauge #cartok #carfacts #howitworks #cars",
    "sources": [
        "https://www.autoblog.com/features/gas-gauge",
        "https://www.npr.org/transcripts/135064825",
        "https://thenewswheel.com/how-your-car-measures-gas-and-why-it-lies-to-you/",
        "https://patents.google.com/patent/US7784342",
        "https://patents.google.com/patent/US5257300",
        "https://patents.google.com/patent/US4838082",
    ],
}
