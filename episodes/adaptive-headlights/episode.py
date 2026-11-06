"""Episode: How matrix (adaptive driving beam) headlights work. See research.md for every fact.
Open loop: "This car has its high beams on, aimed right at that driver. And he isn't blinded. So where did the
light go?" is paid off in the key beat (the light is never sent: the LEDs aimed at him are switched off) and the
punchline. Different structure from the last five: driver's-eye night road (perspective, not 3/4 cutaway) with the
high beam drawn as 25 slices on the road, a low-vs-high reach beat, a lamp cutaway with a 25-LED strip, a camera
viewfinder beat, and a live LED strip whose tiles switch off as cars move through the beam."""
from ev.gfx import INK, RED

SLUG = "adaptive-headlights"
TOPIC = "MATRIX HEADLIGHTS"
SERIES = ("HOW IT WORKS", 4)
SUBTITLE = ["A high beam cut into slices", "that switch off around other cars"]
PUNCH = ("IT WAS NEVER", "SWITCHED ON.")
HOOK_TITLE = [[("HOW ", INK), ("MATRIX HEADLIGHTS", RED)], [("ACTUALLY WORK", INK)]]
END_WORD = ("outro", "it")
TOPIC_WORD = ("outro", "matrix")

LINES = [
    ("hook",    "This car has its high beams on, aimed right at that driver. And he isn't blinded. So where did "
                "the light go?"),
    ("what",    "Here's what's really going on inside matrix headlights."),
    ("problem", "High beams light the road much farther ahead. But they dazzle everyone in front of you, so most "
                "people barely use them. In one study, only eighteen percent of drivers alone on the road had them "
                "on."),
    ("parts",   "So engineers cut the high beam into slices. On the Audi A8 back in twenty thirteen, each headlight "
                "had twenty five LEDs, and each one lights its own slice of the road."),
    ("camera",  "A camera at the front watches the road for other cars, coming toward you and driving ahead of you."),
    ("rehook",  "So how do you stop light that's already flying at someone?"),
    ("key",     "You don't. You never send it. The computer switches off only the LEDs aimed at the other car, and "
                "every other slice stays on full. A dark gap wraps around that car and slides along with it."),
    ("result",  "Road full of traffic? It's basically a low beam. Empty road? Full high beam. And in America, it "
                "only became legal in twenty twenty two."),
    ("outro",   "So the light didn't go anywhere. It was never switched on. That's matrix headlights."),
]
GAPS = {"what": 0.2, "problem": 0.3, "parts": 0.3, "camera": 0.3, "rehook": 0.3, "key": 0.35, "result": 0.3,
        "outro": 0.3}
SAY = {"leds": "L E Dees", "led": "L E D", "a8": "A eight"}

META = {
    "title": "How matrix headlights work: high beams that don't blind anyone #cars #headlights #howitworks",
    "description": (
        "Matrix LED headlights (adaptive driving beam) split the high beam into slices. On the 2013 Audi A8, "
        "each headlight's high beam had 25 LEDs. A forward camera spots oncoming cars and cars ahead, and the "
        "system dims or switches off only the LEDs that would shine at them, so a dark gap follows each car "
        "while the rest of the road stays on high beam.\n\n"
        "Why it matters: high beams let you see much farther, but they dazzle other drivers, so people rarely "
        "use them. In an IIHS study, only 18 percent of drivers with no other traffic nearby had their high "
        "beams on. With the road full of traffic an adaptive beam is essentially a low beam; on an empty road "
        "it's a full high beam. NHTSA's rule allowing adaptive driving beams on new cars in the US took effect "
        "in February 2022. Animation simplified; segment counts vary by car.\n\n"
        "Would you trust a camera to run your high beams?"
    ),
    "tags": ["matrix headlights", "how matrix headlights work", "adaptive headlights", "adaptive driving beam",
             "matrix led", "high beams", "headlights", "car tech", "how cars work", "car facts",
             "engineering explained"],
    "first_comment": "Next up: the Mazda rotary, how keyless entry knows the key is in your pocket, or what that "
                     "turbo flutter sound really is? Vote below",
    "tiktok_caption": "High beams that don't blind anyone. How matrix headlights actually work #headlights #cartok #carfacts #howitworks #cars",
    "sources": [
        "https://www.govinfo.gov/content/pkg/FR-2022-02-22/html/2022-02451.htm",
        "https://www.iihs.org/news/detail/few-drivers-use-their-high-beams-study-finds",
        "https://www.audi-technology-portal.de/en/electrics-electronics/lighting-technology/matrix-led-headlights",
        "https://www.autoblog.com/2013/08/14/audi-a8-matrix-led-headlight/",
        "https://evkx.net/dictionary/matrix-led-headlights",
    ],
}
