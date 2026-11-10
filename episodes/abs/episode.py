"""Episode: How ABS (anti-lock brakes) works. See research.md for every fact.
Open loop: "Everyone was taught, in a skid, pump the brakes. So why would letting go of the brakes help you stop?"
is paid off in the key beat (a tire that's still turning grips harder than a sliding one, and a sliding tire can't
steer) and in the punchline (your car pumps the brakes for you, faster than you could).
Different structure from the last five: a side-on wet-road skid with live car-speed vs wheel-speed bars, a spinning
tone ring with its pulse train, a one-channel hydraulic circuit (inlet valve, outlet valve, accumulator, pump), a
grip-vs-slip graph with a sideways-grip curve, and a pressure sawtooth for the cycling."""
from ev.gfx import INK, RED

SLUG = "abs"
TOPIC = "ABS"
SERIES = ("HOW IT WORKS", 7)
SUBTITLE = ["Anti-lock brakes: hold, release,", "reapply, over a dozen times a second"]
PUNCH = ("YOUR CAR PUMPS THE BRAKES", "FASTER THAN YOU.")
HOOK_TITLE = [[("HOW ", INK), ("ABS", RED), (" BRAKES", INK)], [("ACTUALLY WORK", INK)]]
END_WORD = ("outro", "your")
TOPIC_WORD = ("outro", "abs.")

LINES = [
    ("hook",    "Everyone was taught, in a skid, pump the brakes. So why would letting go of the brakes help "
                "you stop?"),
    ("what",    "Here's what's really going on, and how anti-lock brakes do it for you."),
    ("problem", "Stomp the pedal on a wet road, and a wheel can stop turning while the car keeps going. That's a lock up."),
    ("parts",   "Every wheel has a toothed ring, and a sensor counting the teeth. A computer watches all four."),
    ("how",     "When one wheel slows way faster than the car, it's about to lock. A valve closes to hold the "
                "pressure, another opens to let some out."),
    ("rehook",  "But why let go at all?"),
    ("key",     "Here's the answer. A tire that's still turning grips harder than one that's sliding. And a sliding tire has almost "
                "no sideways grip, so steering does nothing."),
    ("pump",    "Then a pump pushes the pressure back, over a dozen times a second. That buzz in the pedal is "
                "ABS working."),
    ("history", "Bosch and Mercedes put the first electronic four wheel system on the road in nineteen seventy "
                "eight."),
    ("drive",   "So with ABS, don't pump. Press hard, hold it, and steer around the trouble."),
    ("outro",   "Your car pumps the brakes faster than you ever could. That's ABS."),
]
GAPS = {"what": 0.15, "problem": 0.25, "parts": 0.25, "how": 0.25, "rehook": 0.3, "key": 0.25, "pump": 0.25,
        "history": 0.3, "drive": 0.25, "outro": 0.3}
SAY = {}

META = {
    "title": "Why your car pumps the brakes for you: how ABS works #cars #brakes #howitworks",
    "description": (
        "How anti-lock brakes work. Brake hard on a slippery road and a wheel can lock: it stops turning while the "
        "car keeps moving. A sliding tire grips less than one that is still turning and slipping a little, and it "
        "has almost no sideways grip, so the steering does nothing.\n\n"
        "ABS watches every wheel with a toothed tone ring and a sensor. When one wheel slows faster than the car "
        "can, a valve closes to hold the brake pressure, a second valve lets some out, and a pump pushes it back: "
        "hold, release, reapply, over a dozen times a second. That's the buzz you feel in the pedal. With ABS, "
        "don't pump: press hard, hold it, and steer. The first production car with electronic four-wheel ABS was "
        "the 1978 Mercedes S-Class, with Bosch. Animation simplified and slowed; one brake channel shown.\n\n"
        "Have you ever felt your ABS kick in?"
    ),
    "tags": ["abs", "how abs works", "anti lock brakes", "how anti lock brakes work", "abs brakes", "pump the brakes",
             "wheel speed sensor", "brake system", "how cars work", "car facts", "engineering explained"],
    "first_comment": "Next up: flat-plane vs cross-plane V8 sound, how your car knows a tire is low, or why rally "
                     "cars spit fire? Vote below",
    "tiktok_caption": "Why letting go of the brakes helps you stop. How ABS anti-lock brakes actually work #abs #cartok #carfacts #howitworks #cars",
    "sources": [
        "https://www.aa1car.com/library/abs1.htm",
        "https://open-exam-prep.com/study-guides/ase-a5/electronic-brake-control-systems/abs-fundamentals-control-cycles",
        "https://www.aarp.org/auto/driver-safety/antilock-brakes-know-how-they-work/",
        "https://autobuzz.my/2018/12/06/throwback-thursday-40-years-since-the-introduction-of-abs-in-the-w116-mercedes-benz-s-class/",
    ],
}
