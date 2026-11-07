"""Episode: How passive keyless entry works. See research.md for every fact.
Open loop: "Your car knows if your key is in your pocket or sitting on the roof. It can't see it. So how does it
know?" is paid off in the key beat (the key measures how loud each antenna's low-frequency field is and reports
back) and the punchline. Different structure from the last five: an overhead driveway map (not a chase cam or a
mechanism cutaway) with the car's antenna bubbles drawn on the ground, a challenge/response packet exchange, a
live four-bar signal-strength panel as the key moves inside, and a relay-attack map with the bubble stretched to
the house."""
from ev.gfx import INK, RED

SLUG = "keyless-entry"
TOPIC = "KEYLESS ENTRY"
SERIES = ("HOW IT WORKS", 5)
SUBTITLE = ["A one-meter radio bubble", "and a key that measures it"]
PUNCH = ("IT CAN'T SEE YOUR KEY.", "IT LISTENS FOR IT.")
HOOK_TITLE = [[("HOW ", INK), ("KEYLESS ENTRY", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "it")
TOPIC_WORD = ("outro", "keyless")

LINES = [
    ("hook",    "Your car knows if your key is in your pocket, or on the roof. It can't see it. So how does "
                "it know?"),
    ("what",    "Here's what's really going on with keyless entry."),
    ("problem", "The button on your key works from about a hundred meters away. Way too far to tell who's "
                "standing at the door."),
    ("parts",   "So there's a second radio. Antennas in the door handles, bumper and cabin send a weak, "
                "low frequency signal, around a hundred and twenty five kilohertz, that only reaches a meter or "
                "two."),
    ("how",     "Grab the handle, and the car sends a wake up call with a random challenge. The key "
                "scrambles it with a secret code only your car knows, and answers on its long range radio."),
    ("rehook",  "But inside or outside?"),
    ("key",     "Your key measures how loud each antenna sounds, and reports back. Loud from the cabin? You're in. "
                "Only the door? You're out."),
    ("relay",   "That's the weak spot. Thieves use two relay boxes to stretch that bubble into your hallway. "
                "Researchers did it on ten car models, up to fifty meters away."),
    ("fix",     "Newer keys sleep when they stop moving, and some time the signal at light speed, so a relay "
                "gives itself away."),
    ("outro",   "Your car never sees your key. It just listens for it. That's keyless entry."),
]
GAPS = {"what": 0.15, "problem": 0.25, "parts": 0.25, "how": 0.25, "rehook": 0.25, "key": 0.25, "relay": 0.3,
        "fix": 0.25, "outro": 0.25}
SAY = {}

META = {
    "title": "How keyless entry works: how your car knows where your key is #cars #keyfob #howitworks",
    "description": (
        "Passive keyless entry uses two radios. Antennas in the door handles, bumper and cabin send a weak "
        "low-frequency signal (around 125 kHz) that reaches only a meter or two. When you grab the handle, the car "
        "sends a random challenge; the key wakes up, encrypts it with a secret key shared with the car, and "
        "answers on a long-range UHF radio (315 or 433 MHz). The key also measures how strong each antenna's "
        "field is, which tells the car whether the key is inside or outside.\n\n"
        "The weak spot: a relay attack. Two devices forward the car's short-range signal to the key and back, so "
        "the car thinks the key is next to it. A 2011 ETH Zurich study did this on 10 car models from 8 "
        "manufacturers, with the key up to 50 m away. Fixes: fobs that sleep when they stop moving, and "
        "ultra-wideband keys that time the signal's flight. Animation simplified; ranges vary by car.\n\n"
        "Does your car have keyless entry, and do you keep the key in a pouch?"
    ),
    "tags": ["keyless entry", "how keyless entry works", "key fob", "passive keyless entry", "relay attack",
             "car key", "keyless car theft", "car tech", "how cars work", "car facts", "engineering explained"],
    "first_comment": "Next up: what that turbo flutter 'stututu' really is, why old Subarus rumble, or how ABS "
                     "stops a skid? Vote below",
    "tiktok_caption": "How your car knows the key is in your pocket. How keyless entry actually works #keyfob #cartok #carfacts #howitworks #cars",
    "sources": [
        "https://www.hella.com/techworld/us/technical/car-electronics-and-electrics/keyless-go/",
        "https://onlinedocs.microchip.com/oxy/GUID-BAA8542B-0F40-4D9C-830C-561D4001CB62-en-US-2/GUID-B911342E-D68F-4E22-BF14-9EF0CFABB035.html",
        "https://www.s3.eurecom.fr/docs/ndss11_francillon.pdf",
        "https://www.motor1.com/news/813405/how-keyless-car-theft-works/",
        "https://www.csem.ch/en/annual-report/2022/3db-access-ultra-wideband-technology-improves-vehicle-security/",
    ],
}
