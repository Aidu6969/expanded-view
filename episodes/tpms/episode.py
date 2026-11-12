"""Episode: How tire pressure sensors (TPMS) work. See research.md for every fact.
Open loop: "Plenty of cars don't have a pressure sensor in the tires at all. So how do they know?" is paid off in the
key beat (a soft tire is a little smaller, so it spins faster than the others) and in the punchline (one system asks
the tire, the other just watches it spin).
Different structure from the last five: a frosty-driveway opening with a dash lamp, a 3D wheel cutaway with the
valve-stem sensor and its battery, radio packets to a receiver, a pressure-vs-time graph with the 25 % line, two
tires rolling side by side with turn counters (rolling radius), a four-wheel turn-count race, and an all-four-low
"nothing to compare" beat."""
from ev.gfx import INK, RED

SLUG = "tpms"
TOPIC = "TPMS"
SERIES = ("HOW IT WORKS", 8)
SUBTITLE = ["Tire pressure monitoring: a sensor", "in the wheel, or a wheel that spins fast"]
PUNCH = ("ONE ASKS THE TIRE.", "ONE WATCHES IT SPIN.")
HOOK_TITLE = [[("HOW ", INK), ("TIRE PRESSURE", RED)], [("SENSORS WORK", INK)]]
END_WORD = ("outro", "one")
TOPIC_WORD = ("outro", "tpms.")

LINES = [
    ("hook",    "Plenty of cars have no pressure sensor in their tires at all. So how does that little light know "
                "one is low?"),
    ("what",    "Here's what's really going on with tire pressure sensors. There are two kinds, and one is sneaky."),
    ("problem", "A tire can be a quarter low and still look fine. So in the US, new cars since two thousand "
                "seven must warn you within twenty minutes."),
    ("parts",   "The first kind is direct. Built onto the back of the valve stem, inside the wheel, sits a sensor "
                "with its own battery."),
    ("how",     "It measures the pressure and radios it to the car every thirty to sixty seconds as you drive. "
                "Drop a quarter low, and the light comes on."),
    ("rehook",  "But the sneaky kind has no sensor in the tire. So what is it measuring?"),
    ("key",     "Wheel speed. A tire low on air squashes down, so it's a little smaller. And a smaller tire has to "
                "spin faster to keep up."),
    ("result",  "The anti-lock brake sensors count every wheel's turns. When one keeps spinning faster than the rest, "
                "that tire is soft."),
    ("catch",   "The catch? If all four leak together, a basic system has nothing to compare. That's why you reset "
                "it after new tires."),
    ("outro",   "One kind asks the tire. The other just watches it spin. That's TPMS."),
]
GAPS = {"what": 0.15, "problem": 0.25, "parts": 0.3, "how": 0.2, "rehook": 0.3, "key": 0.25, "result": 0.25,
        "catch": 0.3, "outro": 0.3}
SAY = {"TPMS.": "T P M S", "TPMS": "T P M S", "US,": "U S,", "anti-lock": "anti lock"}

META = {
    "title": "How tire pressure sensors work (some cars don't have any) #cars #tpms #howitworks",
    "description": (
        "How TPMS works. A tire can lose a quarter of its pressure and still look normal, so in the US every new "
        "light vehicle built since September 2007 must light a warning within 20 minutes once a tire is 25% below "
        "the recommended cold pressure (FMVSS 138).\n\n"
        "Direct TPMS puts a battery-powered sensor on the back of each valve stem, inside the wheel. It radios "
        "pressure (and usually temperature) to the car every 30 to 60 seconds while driving. Indirect TPMS has no "
        "sensor in the tire: it uses the ABS wheel-speed sensors. A low tire has a slightly smaller rolling "
        "radius, so it turns a little faster than the others. Basic indirect systems can't see all four tires "
        "losing air together, and need a reset after new tires or a rotation; newer ones also analyse tire "
        "vibration. Animation simplified; the speed difference is exaggerated so you can see it.\n\n"
        "Does your car have sensors in the wheels, or the sneaky kind?"
    ),
    "tags": ["tpms", "how tpms works", "tire pressure sensor", "how tire pressure sensors work", "tire pressure light",
             "indirect tpms", "direct tpms", "low tire pressure", "how cars work", "car facts", "engineering explained"],
    "first_comment": "Next up: why rally cars bang and spit fire (anti-lag), how a starter motor cranks your engine, "
                     "or how a CVT works? Vote below",
    "tiktok_caption": "Some cars have no tire pressure sensor at all. So how do they know? How TPMS works #tpms #cartok #carfacts #howitworks #cars",
    "sources": [
        "https://www.law.cornell.edu/cfr/text/49/571.138",
        "https://www.standardbrand.com/en/training/standard-insights/a-closer-look-tire-pressure-monitoring-systems-tpms-operation",
        "https://www.brakeandfrontend.com/tech-tip-understanding-tire-pressure-monitoring-systems/",
        "https://theautopian.com/how-indirect-tire-pressure-monitoring-systems-work-and-why-we-should-celebrate-their-return",
    ],
}
