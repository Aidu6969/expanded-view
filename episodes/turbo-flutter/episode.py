"""Episode: What turbo flutter actually is. See research.md for every fact.
Open loop: "Stu tu tu tu. Every car fan loves that sound. But what's actually making it?" is paid off in the
key beat (the air bounces backwards through the still-spinning wheel). Different structure from the last five: a
live Greitzer surge simulation drives the air, the pressure, a real compressor-map orbit and the flutter sound."""
from ev.gfx import INK, RED

SLUG = "turbo-flutter"
TOPIC = "TURBO FLUTTER"
SERIES = ("HOW IT WORKS", 6)
SUBTITLE = ["Boosted air bouncing back", "through a wheel that won't stop"]
PUNCH = ("THE WHEEL NEVER STOPS.", "THE AIR BOUNCES BACK.")
HOOK_TITLE = [[("WHAT ", INK), ("TURBO FLUTTER", RED)], [("ACTUALLY IS", INK)]]
END_WORD = ("outro", "wheel")
TOPIC_WORD = ("outro", "turbo")

LINES = [
    ("hook",    "Stu tu tu tu. Every car fan loves that sound. But what's actually making it?"),
    ("what",    "Here's what's really happening when turbo flutter starts."),
    ("problem", "At full boost, your turbo's compressor wheel spins around a hundred thousand RPM, "
                "ramming air toward the engine."),
    ("lift",    "Then you lift off, and the throttle snaps shut. The air has nowhere to go, so it piles up, "
                "and the pressure spikes."),
    ("rehook",  "But the wheel can't just stop. So where does that air go?"),
    ("key",     "Backwards. The pressure beats the blades, and the air blasts back out through the spinning "
                "wheel. The pressure drops, the blades grab again, and it all repeats. Every stu is one of those "
                "bounces."),
    ("surge",   "Engineers call it compressor surge. On a turbo's map, you've fallen off the left edge."),
    ("myth",    "And the wheel never reverses. Only the air does."),
    ("harm",    "A little flutter probably won't kill a modern turbo. But turbo maker Garrett warns that staying "
                "in surge can, by hammering the thrust bearing."),
    ("fix",     "That's why a blow off valve exists. Engine vacuum pulls it open the instant you lift, and the "
                "trapped air escapes. That's the famous pssh."),
    ("outro",   "The wheel never stops. The air bounces back. That's turbo flutter."),
]
GAPS = {"what": 0.15, "problem": 0.25, "lift": 0.2, "rehook": 0.2, "key": 0.25, "surge": 0.25, "myth": 0.2,
        "harm": 0.2, "fix": 0.2, "outro": 0.25}
SAY = {"RPM": "R P M", "pssh": "psshh", "Stu": "stoo", "stu": "stoo", "tu": "too", "Garrett": "Garrett"}
YT_DROP = ["surge", "harm"]

META = {
    "title": "What is turbo flutter? The stutututu sound explained #turbo #cars #howitworks",
    "description": (
        "Turbo flutter is compressor surge. When the throttle snaps shut, boosted air is trapped between the "
        "compressor and the throttle plate, the pressure spikes and the flow collapses, so air pushes back out "
        "through the wheel. The pressure drops, the blades grab again, and the cycle repeats. The wheel itself "
        "never reverses, only the air does.\n\n"
        "Garrett says operating in surge can lead to premature turbo failure from heavy thrust loading, though "
        "occasional mild flutter on a modern turbo is unlikely to shorten its life noticeably. A blow-off valve "
        "uses manifold vacuum to vent the trapped air when you lift. Animation simplified and slowed.\n\n"
        "Would you keep the flutter or fit a blow-off valve?"
    ),
    "tags": ["turbo flutter", "what is turbo flutter", "compressor surge", "stututu", "blow off valve",
             "turbo sound", "how a turbo works", "turbocharger", "car facts", "how cars work", "engineering explained"],
    "first_comment": "Next up: why old Subarus rumble, how anti-lag spits fire, or flat-plane vs cross-plane V8s? "
                     "Vote below",
    "tiktok_caption": "What is turbo flutter? That stutututu is air bouncing back through your turbo #turboflutter #cartok #carfacts #howitworks #turbo",
    "sources": [
        "https://www.garrettmotion.com/wp-content/uploads/2019/10/GAM_Turbo-Tech-103_Expert-1.pdf",
        "https://www.hpacademy.com/previous-webinars/209-what-is-compressor-surge/",
        "https://en.wikipedia.org/wiki/Blowoff_valve",
        "https://gfb.com.au/tech/tech-articles/11-the-truth-about-compressor-surge/",
        "https://www.caradvice.com.au/587685/what-is-turbo-flutter-and-compressor-surge-is-it-bad/",
        "https://www.enginelabs.com/?p=6635",
    ],
}
