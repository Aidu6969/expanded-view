"""Episode 2 — How a turbo actually works."""
from ev.gfx import INK, RED

SLUG = "turbocharger"
TOPIC = "TURBO"
SUBTITLE = ["Exhaust-driven turbine + compressor", "on one shaft"]
PUNCH = ("EXHAUST IN,", "BOOST OUT.")
HOOK_TITLE = [[("HOW A ", INK), ("TURBO", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "exhaust", 1)   # second "exhaust" in the outro: "Exhaust in, boost out."
TOPIC_WORD = ("outro", "turbo")

LINES = [
    ("hook",   "Your exhaust can spin this at up to two hundred thousand RPM."),
    ("what",   "A turbocharger is two wheels on one shaft. A turbine on the exhaust side, and a compressor on the intake side."),
    ("problem", "An engine's power is limited by how much air it can pull in. More air lets it burn more fuel, for more power. "
                "But on its own, it only breathes at atmospheric pressure."),
    ("turbine", "So the turbo puts the exhaust to work. Hot gas leaving the cylinders rushes into the turbine housing and spins the turbine wheel."),
    ("comp",   "The shaft spins the compressor on the other end. It pulls in fresh air and squeezes it into the engine. "
               "That extra pressure is called boost."),
    ("cooler", "Squeezing air heats it up, so it usually goes through an intercooler first. Cooler air is denser, so even more fits in each cylinder."),
    ("gate",   "More boost makes more exhaust, which makes even more boost. So a wastegate opens and lets some exhaust bypass the turbine, holding boost in check."),
    ("outro",  "Exhaust spins the turbine, the turbine spins the compressor, and the compressor feeds the engine. Exhaust in, boost out. That's a turbo."),
]
GAPS = {"what": 0.25, "problem": 0.25, "turbine": 0.3, "comp": 0.22, "cooler": 0.25, "gate": 0.3, "outro": 0.3}

META = {
    "title": "How a turbo turns exhaust into power #turbo #cars #engineering",
    "description": (
        "A turbocharger is two wheels on one shaft. Exhaust gas spins the turbine, and the turbine spins the "
        "compressor, which packs extra air into the engine. More air lets the engine burn more fuel and make more "
        "power. An intercooler cools the squeezed air so it's denser, and a wastegate bypasses exhaust to keep boost "
        "in check.\n\n"
        "Shaft speed and boost vary by engine; the animation is slowed down and simplified to show the flow.\n\n"
        "What should we take apart next? 👇\n#Turbocharger #HowItWorks #CarTech"
    ),
    "tags": ["turbo", "turbocharger", "how a turbo works", "turbo explained", "boost", "wastegate", "intercooler",
             "forced induction", "engine animation", "how engines work", "car tech"],
    "first_comment": "Manual gearbox synchros, the differential, or how a key opens a lock: what should Expanded View take apart next?",
    "tiktok_caption": "How a turbo turns your exhaust into boost 🌀 #turbo #cartok #howitworks #engineering #carsoftiktok",
    "sources": [
        "https://en.wikipedia.org/wiki/Turbocharger",
        "https://audi-technology-portal.de/en/drivetrain/engine-efficiency-technologies/exhaust-turbocharger",
        "https://www.garrettmotion.com/es/turbocharger-technology/how-a-turbo-works/basic/",
        "https://www.garrettmotion.com/knowledge-center-category/turbo-replacement/intercoolers-how-do-they-work",
    ],
}
