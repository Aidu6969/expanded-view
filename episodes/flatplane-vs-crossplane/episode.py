"""Episode: flat-plane vs cross-plane V8, why a Ferrari V8 screams and a muscle car V8 burbles. See research.md.
Open loop: "Same eight cylinders. So why does a Ferrari V8 scream, while a muscle car V8 burbles?" is paid off in
the key beats (one bank of a cross-plane fires at uneven gaps; a flat-plane bank fires evenly, like a four).
Different structure from the last five: a split-screen street hook, a big 3D crankshaft whose pins morph from a
cross to a flat line (with an end-on pin clock), and two per-bank 720-degree firing dials that show the gaps;
then the cost (second-order shake) and a tach sweep. Engine notes are synthesized from the same firing model."""
from ev.gfx import INK, RED

SLUG = "flatplane-vs-crossplane"
TOPIC = "FLAT PLANE"
SERIES = ("LEGENDARY ENGINES", 7)
SUBTITLE = ["Crank pins in one plane: each bank", "fires evenly, like a four cylinder"]
PUNCH = ("SAME EIGHT CYLINDERS.", "DIFFERENT CRANK.")
HOOK_TITLE = [[("FLAT PLANE ", RED), ("VS", INK)], [("CROSS PLANE V8", INK)]]
END_WORD = ("outro", "Same")
TOPIC_WORD = ("outro", "flat")

LINES = [
    ("hook",   "Same eight cylinders. So why does a Ferrari V8 scream, while a muscle car V8 burbles?"),
    ("what",   "Here's what's really going on, flat plane versus cross plane."),
    ("cross",  "In a muscle car V8, the crank's four pins sit ninety degrees apart. Look from the end, and they make "
               "a cross."),
    ("even",   "A cylinder fires every ninety degrees. Perfectly even."),
    ("rehook", "So if it's even, where does the burble come from?"),
    ("key",    "Each side of the V has its own exhaust. And on one side, the bangs come at uneven gaps. A short one, "
               "a long one, a longer one. That stumble is the burble."),
    ("flat",   "Now flatten the crank. All four pins in one plane, half a turn apart. The firing just alternates. "
               "Left, right, left, right."),
    ("scream", "So each side fires evenly, like two four cylinders side by side. And the lighter crank revs higher. "
               "That's the scream."),
    ("cost",   "The catch? It shakes like a four cylinder, which is why most big V8s stayed cross plane. "
               "Then the Corvette Z06 went flat plane, all the way to eighty six hundred RPM."),
    ("outro",  "Same eight cylinders. Different crank. That's flat plane."),
]
GAPS = {"what": 0.15, "cross": 0.2, "even": 0.2, "rehook": 0.25, "key": 0.2, "flat": 0.35, "scream": 0.2,
        "cost": 0.3, "outro": 0.3}
SAY = {"V8": "V eight", "V8s": "V eights", "Z06": "Z oh six", "RPM": "R P M"}

META = {
    "title": "Flat plane vs cross plane V8: why Ferraris scream #v8 #ferrari #corvette",
    "description": (
        "Same eight cylinders, different crank. A cross-plane V8 (most muscle cars and trucks) has its four crank "
        "pins 90 degrees apart, so the engine fires every 90 degrees overall, but each bank fires at uneven gaps "
        "(90, 180, 270, 180 degrees). Each bank feeds its own exhaust, and that uneven beat is the classic burble.\n\n"
        "A flat-plane crank puts all four pins in one plane, 180 degrees apart. Firing alternates left, right, "
        "left, right, so each bank fires evenly, like two four-cylinder engines. The crank needs less counterweight, "
        "so it is lighter and revs higher, but it shakes like a four-cylinder (second-order vibration), which is why "
        "most large V8s stayed cross-plane. Ferrari's V8s and the 2023 Corvette Z06 (8,600 rpm) use flat-plane "
        "cranks. Animation simplified and slowed; all engine sounds in this video are synthesized.\n\n"
        "Burble or scream: which one do you want?"
    ),
    "tags": ["flat plane crank", "cross plane crank", "flat plane vs cross plane", "why do ferraris sound different",
             "v8 sound", "v8 burble", "corvette z06", "ferrari v8", "muscle car", "crankshaft", "how engines work"],
    "first_comment": "Next up: how anti-lag spits fire, how your car knows a tire is low, or why everyone LS swaps everything? Vote below",
    "tiktok_caption": "Flat plane vs cross plane V8: why a Ferrari screams and a muscle car burbles #v8 #flatplane #ferrari #cartok #howitworks",
    "sources": [
        "https://en.wikipedia.org/wiki/Crossplane",
        "https://www.autocar.co.uk/node/105081",
        "https://jalopnik.com/1878133/why-flat-plane-crank-v8-engines-sound-different/",
        "https://en.wikipedia.org/wiki/Ferrari_F154_engine",
        "https://www.motorauthority.com/news/1132938_2023-chevrolet-corvette-z06-debuts-october-26-with-screaming-flat-plane-crank-v-8-and-8-600-rpm-redline",
    ],
}
