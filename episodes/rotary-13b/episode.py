"""Episode: How a rotary engine actually works (Mazda 13B twin-rotor Wankel). See research.md for every fact.
Open loop: "Fans say a rotary has only three moving parts. So where are the valves?" is paid off in the key beat
(there are none: the rotor itself uncovers and covers the ports) and in the punchline. Different from the last five
(matrix headlights road POV, fuel gauge float card, EV sound, RB26 rulebook, jake brake): a face-on x-ray of ONE
rotor in its housing, driven by real Wankel kinematics (epitrochoid housing, rotor centre orbits at e while the rotor
turns at 1/3 shaft speed via a 36:24 ring/fixed gear), a live chamber-volume graph, side ports that the rotor really
covers and uncovers, and an apex-seal close-up."""
from ev.gfx import INK, RED

SLUG = "rotary-13b"
TOPIC = "THE ROTARY"
SERIES = ("LEGENDARY ENGINES", 5)
SUBTITLE = ["A spinning triangle that is its own", "piston and its own valve"]
PUNCH = ("THE ROTOR", "IS THE VALVE.")
HOOK_TITLE = [[("HOW A ", INK), ("ROTARY ENGINE", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "the")
TOPIC_WORD = ("outro", "rotary.")

LINES = [
    ("hook",     "Fans say a rotary engine has only three moving parts. So where are the valves?"),
    ("what",     "Here's how a rotary engine actually works, inside Mazda's 13B."),
    ("problem",  "A normal engine slams pistons up and down, and needs camshafts and valves to let air in and out. "
                 "The rotary just spins."),
    ("parts",    "An oval housing. A triangle shaped rotor. Two rotors on one eccentric shaft. "
                 "That's all three moving parts."),
    ("gears",    "A gear inside the rotor rolls around a fixed gear, so the shaft spins three times for every "
                 "turn of the rotor."),
    ("rehook",   "But a triangle inside an oval leaves three gaps. So what are they for?"),
    ("chambers", "Each gap is a chamber. As the rotor turns, it grows, shrinks, grows and shrinks again. "
                 "Intake, compression, power, exhaust. Three power strokes every turn."),
    ("key",      "And the valves? It's the rotor itself. As it turns, it slides past ports cut into the housing, "
                 "uncovering them, then covering them again."),
    ("catch",    "The catch is the tips. Three thin apex seals hold every chamber shut, and when they wear, "
                 "compression leaks away."),
    ("outro",    "No cams. No springs. No valves. The rotor is the valve. That's the rotary."),
]
GAPS = {"what": 0.25, "problem": 0.3, "parts": 0.3, "gears": 0.3, "rehook": 0.3, "chambers": 0.3, "key": 0.35,
        "catch": 0.3, "outro": 0.3}
# YouTube cut A/B (14th episode = even): drop the piston comparison and the gear detail
YT_DROP = ["problem", "gears"]
SAY = {"13B": "thirteen B"}

META = {
    "title": "How a rotary engine works: so where are the valves? #rotary #mazda #jdm",
    "description": (
        "A Wankel rotary like Mazda's 13B has no pistons, camshafts or poppet valves. A rounded triangular rotor "
        "turns inside an oval (epitrochoid) housing; a gear inside the rotor meshes with a fixed gear, so the "
        "eccentric output shaft turns three times for every turn of the rotor. The 13B has two rotors of 654 cc "
        "each (1.3 litres) on one shaft, which is why fans call it a three-moving-part engine.\n\n"
        "The three gaps between rotor and housing are the combustion chambers. Each one grows and shrinks twice per "
        "rotor turn, going through intake, compression, power and exhaust, so every rotor makes three power strokes "
        "per turn. There are no valves: the rotor itself uncovers and covers the intake and exhaust ports as it "
        "passes. The weak point is sealing: the apex seals on the rotor tips wear, and compression leaks away. "
        "Animation simplified and slowed; the car shown is a generic illustration.\n\n"
        "Which legendary engine should we take apart next?"
    ),
    "tags": ["rotary engine", "how a rotary engine works", "wankel engine", "mazda 13b", "13b rotary", "rx7",
             "rx8", "renesis", "apex seals", "jdm", "engine animation", "how it works"],
    "first_comment": "Next: flat-plane vs cross-plane V8, the anti-lag bang, or the Audi five-cylinder warble? Vote below",
    "tiktok_caption": "How a rotary engine works: three moving parts and no valves. So how does it breathe? #rotary #mazda #rx7 #jdm #carsoftiktok",
    "sources": [
        "https://www.autocar.co.uk/car-news/technology/under-skin-understanding-bizarre-workings-rotary-engines",
        "https://www.carsguide.com.au/car-advice/what-is-a-rotary-engine-37430",
        "https://www.howacarworks.com/technology/how-a-rotary-wankel-engine-works",
        "https://www.wardsauto.com/news/archive-wards-mazda-1-3l-renesis-rotary/767389/",
        "https://australiancar.reviews/?p=52354",
    ],
}
