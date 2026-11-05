"""Episode: How the RB26 actually works (Nissan RB26DETT, Skyline GT-R R32). See research.md for every fact.
Open loop: every fast Japanese car claimed 276 hp, so what was the GT-R hiding? Paid off in the key beat (race
version ~550 hp, 29 of 29 Group A wins). Different from the 2JZ episode: the "why" here is the racing rulebook
(2.6 L x 1.7 = class line), six throttles, and why the twin turbos are split three and three (even 240-degree
exhaust pulses per turbo)."""
from ev.gfx import INK, RED

SLUG = "rb26"
TOPIC = "RB26"
SERIES = ("LEGENDARY ENGINES", 4)
SUBTITLE = ["2.6 litres for the race rules, six throttles,", "two turbos fed three cylinders each"]
PUNCH = ("276 WAS THE PAPERWORK.", "NOT THE LIMIT.")
HOOK_TITLE = [[("HOW THE ", INK), ("RB26", RED)], [("ACTUALLY WORKS", INK)]]
END_WORD = ("outro", "so")
TOPIC_WORD = ("outro", "rb26.")

LINES = [
    ("hook",    "Every fast Japanese car claimed the same two hundred seventy six horsepower. "
                "So what was the GT-R hiding?"),
    ("what",    "It's under the hood. Here's how the RB26 actually works."),
    ("rule",    "That number was a gentlemen's agreement between Japan's carmakers. But this engine was "
                "built for a different rulebook. Racing."),
    ("size",    "That's why it's two point six litres. Race rules multiplied turbo engines by one point seven, "
                "putting it just under the four and a half litre class."),
    ("throttle", "Air comes in through six separate throttles, one for every cylinder."),
    ("turbos",  "Then two turbos, side by side. The front three cylinders spin one. The back three spin the other."),
    ("pulses",  "So why three and three? Those cylinders fire evenly, one every two hundred forty degrees, "
                "so each turbo gets a steady beat of exhaust."),
    ("key",     "Now the secret. In race trim, this engine made around five hundred fifty horsepower. "
                "Twice the official number."),
    ("result",  "And the race car won all twenty nine Group A races it entered in Japan."),
    ("outro",   "So two seventy six was the paperwork. Not the limit. That's the RB26."),
]
GAPS = {"what": 0.25, "rule": 0.3, "size": 0.3, "throttle": 0.3, "turbos": 0.3, "pulses": 0.3, "key": 0.35,
        "result": 0.3, "outro": 0.3}
# YouTube cut A/B (10th episode = even): drop the rulebook detour, keep hook -> intake -> turbos -> pulses -> key
YT_DROP = ["rule", "size"]
SAY = {"RB26": "R B twenty six", "GT-R": "G T R", "RB26.": "R B twenty six"}

META = {
    "title": "How the RB26 actually works: what the GT-R was hiding #rb26 #skyline #jdm",
    "description": (
        "Nissan's RB26DETT, the 2.6 litre twin-turbo straight six from the R32 Skyline GT-R, was rated at "
        "280 PS (276 hp) because of the Japanese makers' gentlemen's agreement. But it was designed for Group A "
        "racing, where turbo engines were multiplied by 1.7: 2.6 litres put it just under the 4.5 litre class. "
        "It breathes through six individual throttle bodies and two parallel turbos, the front three cylinders "
        "driving one and the back three the other, so each turbo gets an evenly spaced exhaust pulse every 240 "
        "degrees.\n\n"
        "In Group A trim the engine made around 550 PS, and the R32 GT-R won all 29 Group A touring car races it "
        "entered in Japan. Animation simplified and slowed; the cars shown are generic illustrations.\n\n"
        "Which legendary engine should we take apart next?"
    ),
    "tags": ["rb26", "rb26dett", "how the rb26 works", "skyline gt-r", "r32 gtr", "godzilla", "nissan skyline",
             "twin turbo", "inline six", "jdm", "gentlemen's agreement", "engine animation"],
    "first_comment": "Next: the rotary 13B, the flat-plane vs cross-plane V8, or why EVs fake engine sounds? Vote below",
    "tiktok_caption": "How the RB26 actually works: what the Skyline GT-R was hiding behind 276 hp #rb26 #skyline #gtr #jdm #carsoftiktok",
    "sources": [
        "https://www.nissan-global.com/EN/HERITAGE_COLLECTION/327_zexel_skyline_gt-r.html",
        "https://en.wikipedia.org/wiki/Nissan_RB_engine",
        "https://www.carthrottle.com/features/japanese-gentlemans-agreement-explained",
        "https://www.fastcar.co.uk/tuning/how-to-tune-a-nissan-rb26dett-engine/",
        "https://www.jdmbuysell.com/learn/engines/rb26dett/",
    ],
}
