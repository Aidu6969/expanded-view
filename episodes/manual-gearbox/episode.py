"""Episode 3 — How a manual gearbox actually works (constant mesh + synchromesh)."""
from ev.gfx import INK, RED

SLUG = "manual-gearbox"
TOPIC = "GEARBOX"
SUBTITLE = ["Constant-mesh gears, locked one", "at a time by a synchro collar"]
PUNCH = ("MATCH THE SPEEDS,", "LOCK THE TEETH.")
HOOK_TITLE = [[("HOW A ", INK), ("MANUAL GEARBOX", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "match")       # "Match the speeds, then lock the teeth."
TOPIC_WORD = ("outro", "gearbox")

LINES = [
    ("hook",   "Every gear in your gearbox is spinning. Even the ones you're not using."),
    ("what",   "Here's how a manual transmission actually works. The gears never slide in and out. They stay meshed in pairs."),
    ("parts",  "The engine turns the countershaft, and every gear on it. Their partners sit on the output shaft, "
               "but they aren't attached. They just spin freely."),
    ("ratio",  "Each pair is a different ratio. A small gear turning a big one trades speed for pulling power. "
               "In neutral, none of them drives anything."),
    ("collar", "Between the gears sits a collar, locked to the output shaft. Press the clutch, shift into first, "
               "and a fork slides that collar sideways."),
    ("grind",  "But the collar is standing still, and the gear is still spinning. Slam their teeth together, and you get that grinding noise."),
    ("key",    "So first, a cone shaped synchro ring rubs against the gear. Friction drags it to the same speed. "
               "Only then do the teeth slide in and lock."),
    ("result", "Let the clutch out, and that one gear drives the output shaft and the wheels. Every other gear just keeps spinning."),
    ("outro",  "Old gearboxes had no synchros, so drivers did it by double clutching. Match the speeds, then lock the teeth. "
               "That's a manual gearbox."),
]
GAPS = {"what": 0.25, "parts": 0.25, "ratio": 0.25, "collar": 0.3, "grind": 0.25, "key": 0.3, "result": 0.3, "outro": 0.3}

META = {
    "title": "How a manual transmission works: every gear is always spinning #cars #manual #engineering",
    "description": (
        "In a manual gearbox the gears never slide in and out. They stay meshed in pairs: the countershaft gears "
        "turn with the engine, and their partners spin freely on the output shaft. Shifting slides a collar, "
        "locked to the output shaft, onto the dog teeth of one gear. Before the teeth touch, a cone-shaped synchro "
        "ring uses friction to bring the gear to the collar's speed, so nothing grinds.\n\n"
        "Simplified three-speed layout, animation slowed. Real gearboxes add more gears, a reverse gear and "
        "synchros on both sides of each collar.\n\n"
        "Did you learn to drive on a manual? 👇\n#ManualTransmission #HowItWorks #CarTech"
    ),
    "tags": ["manual transmission", "how a manual transmission works", "manual gearbox", "gearbox explained",
             "synchromesh", "synchro", "stick shift", "constant mesh", "double clutching", "how cars work",
             "engineering animation"],
    "first_comment": "Next up: the clutch, the differential, or how a key opens a lock? Vote below 👇",
    "tiktok_caption": "How a manual transmission works: every gear is spinning, even in neutral ⚙️ #manual #stickshift #cartok #howitworks #engineering",
    "sources": [
        "https://www.edumech.co.uk/learn/transmission-and-driveline/synchromesh-unit",
        "https://www.hagerty.com/media/maintenance-and-tech/how-a-manual-transmission-works/",
        "https://www.curbsideclassic.com/blog/tech/1929-cadillac-lasalle-synchro-mesh-transmission-shifting-is-made-simple-and-clashing-of-gears-is-ended",
        "https://uniquecarsandparts.com.au/how_it_works_synchromesh",
    ],
}
