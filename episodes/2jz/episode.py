"""Episode 8 — Why the 2JZ is so strong (Toyota 2JZ-GTE, Supra Mk4). See research.md for every fact."""
from ev.gfx import INK, RED

SLUG = "2jz"
TOPIC = "2JZ"
SUBTITLE = ["Iron closed-deck block, forged crank,", "seven main bearings, twin turbos"]
PUNCH = ("NOT A MYTH.", "JUST OVERBUILT.")
HOOK_TITLE = [[("WHY THE ", INK), ("2JZ", RED)], [("IS SO STRONG", INK)]]
END_WORD = ("outro", "not")
TOPIC_WORD = ("outro", "2jz.")

LINES = [
    ("hook",    "Everyone says a stock 2JZ can take double its factory power."),
    ("what",    "True? This is the three litre straight six from Toyota's Supra. Here's why the 2JZ is so strong."),
    ("block",   "First, the block. It's cast iron, not aluminium, and it's closed deck. The top is solid around "
                "every cylinder, so the bores stay braced under boost."),
    ("crank",   "Inside, a forged steel crankshaft sits in seven main bearings, one on each side of every cylinder. "
                "There's nowhere for it to flex."),
    ("balance", "And a straight six balances itself. The front three pistons mirror the back three, so the shaking "
                "forces cancel out instead of hammering the bearings."),
    ("turbos",  "From the factory it had two identical turbos, working in sequence. The first one spools down low. "
                "Around four thousand RPM, the second one joins in."),
    ("key",     "Export cars made three hundred twenty horsepower. Tuners run around six hundred on the stock "
                "internals. That's double."),
    ("limit",   "What usually kills one isn't the iron. It's a bad tune, and detonation hammering the pistons and rods."),
    ("outro",   "So it's not a myth. Just overbuilt. That's the 2JZ."),
]
GAPS = {"what": 0.25, "block": 0.3, "crank": 0.3, "balance": 0.3, "turbos": 0.3, "key": 0.35, "limit": 0.3,
        "outro": 0.3}

META = {
    "title": "Why the 2JZ is so strong: can it really take double? #2jz #supra #jdm",
    "description": (
        "Toyota's 2JZ-GTE, the 3.0 litre straight six from the Mk4 Supra, has a cast-iron closed-deck block, a "
        "forged steel crankshaft running in seven main bearings, and sequential twin turbos: the first spools low, "
        "the second joins around 4,000 rpm. A straight six is also naturally balanced, so the bearings aren't "
        "fighting shaking forces.\n\n"
        "Export cars were rated at 320 hp. Tuners commonly run around 600 hp on the stock internals; the usual killer "
        "is detonation from a bad tune, not the block. Animation simplified and slowed; numbers vary by build, fuel "
        "and tune.\n\n"
        "What's the most power you've seen on a stock-bottom-end 2JZ? 👇\n#2JZ #Supra #HowItWorks"
    ),
    "tags": ["2jz", "2jz gte", "why is the 2jz so strong", "toyota supra", "mk4 supra", "2jz engine",
             "inline six", "closed deck block", "sequential twin turbo", "jdm", "engine animation"],
    "first_comment": "Next legend: the LFA V10, the RB26, or the rotary? Vote below 👇",
    "tiktok_caption": "Why the 2JZ is so strong: can a stock one really take double its power? 🔥 #2jz #supra #jdm #cartok #engine",
    "sources": [
        "https://en.wikipedia.org/wiki/Toyota_JZ_engine",
        "https://www.jdpower.com/cars/shopping-guides/guide-to-understanding-the-toyota-2jz-gte-engine",
        "https://www.enginelabs.com/news/inside-a-legend-tearing-down-a-2jz-engine-with-stephan-papadakis/",
        "https://motoiq.com/extreme-engine-tech-building-a-high-boost-2jz-with-brian-crower-and-je-pistons-part-1",
        "https://en.wikipedia.org/wiki/Straight-six_engine",
        "https://www.torquecars.com/toyota/2jz-tuning.php",
        "https://nzperformance.co.nz/blogs/build-guides/how-much-power-can-a-stock-2jz-or-1jz-handle",
        "https://www.realstreetperformance.com/blog/how-much-will-a-stock-2jz-hold",
    ],
}
