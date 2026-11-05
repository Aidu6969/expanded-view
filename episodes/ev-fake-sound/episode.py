"""Episode: Why electric cars make fake sounds (AVAS / US FMVSS 141, EU 540/2014). See research.md for every fact.
Open loop: "who is that sound actually for?" is paid off in the key beat (the speaker goes quiet above ~30 km/h
because tyres and wind are loud enough: it was always for the people outside). Twist: performance EVs fake an
engine for the driver too. Different structure from the last five (engine cutaways): a street scene, a crash-risk
bar chart, a speaker cutaway and a noise-vs-speed crossover graph."""
from ev.gfx import INK, RED

SLUG = "ev-fake-sound"
TOPIC = "FAKE ENGINE SOUND"
SERIES = ("HOW IT WORKS", 2)
SUBTITLE = ["A speaker that warns people outside,", "until your tires are loud enough"]
PUNCH = ("THE SILENCE WAS", "THE DANGER.")
HOOK_TITLE = [[("WHY ELECTRIC CARS", INK)], [("FAKE THEIR SOUND", RED)]]
END_WORD = ("outro", "the", 0)
TOPIC_WORD = ("outro", "fake")

LINES = [
    ("hook",    "Your electric car makes that spaceship hum on purpose. So who is that sound actually for?"),
    ("what",    "Not who you think. Here's why electric cars make fake engine sounds."),
    ("problem", "A gas engine announces itself. An electric motor is almost silent, so at parking lot speeds, "
                "people don't hear you coming."),
    ("data",    "U.S. safety researchers found hybrids and electric cars were about fifty percent more likely to "
                "hit a pedestrian in low speed moves, like backing up or turning."),
    ("law",     "So now it's the law. The car reads its own speed and plays a sound through a speaker in the front "
                "bumper. The faster you go, the louder it gets."),
    ("rehook",  "But above about nineteen miles an hour, it goes quiet. Why?"),
    ("key",     "Because by then, your tires and the wind are loud enough on their own. The speaker was never "
                "for you. It's for the people outside."),
    ("twist",   "Some fast electric cars fake it for the driver too. Hyundai's Ioniq 5 N plays engine sounds "
                "through ten speakers, and cuts power for a split second to fake a gear shift."),
    ("outro",   "So that hum isn't a gimmick. The silence was the danger. That's the fake engine sound."),
]
GAPS = {"what": 0.2, "problem": 0.3, "data": 0.3, "law": 0.3, "rehook": 0.3, "key": 0.35, "twist": 0.35,
        "outro": 0.3}
SAY = {"Ioniq": "eye-onic", "5": "five", "N": "en", "U.S.": "U S", "Hyundai's": "hun-day's"}

META = {
    "title": "Why electric cars make fake engine sounds (it's not for you) #ev #electriccar #cars",
    "description": (
        "Electric cars are almost silent at low speed, and NHTSA research found hybrids and EVs were about 50% "
        "more likely than gas cars to hit a pedestrian in low-speed moves like backing up or turning. So the US "
        "(FMVSS 141) and the EU now require an alert sound: a speaker, usually in the front bumper, plays a tone "
        "that gets louder as the car speeds up.\n\n"
        "Above about 30 km/h (19 mph) in the US, about 20 km/h in the EU, tire and wind noise make the car "
        "audible on its own, so the speaker goes quiet. Separately, some performance EVs like the Hyundai Ioniq 5 N "
        "play engine sounds for the driver and briefly cut power to fake gear shifts. Animation simplified; all "
        "sounds in this video are synthesized.\n\n"
        "Do you like EV sounds, or would you rather drive in silence?"
    ),
    "tags": ["why electric cars make noise", "ev fake engine sound", "electric car sound", "AVAS",
             "pedestrian warning sound", "FMVSS 141", "electric vehicle", "ioniq 5 n", "how it works",
             "car animation"],
    "first_comment": "Next up: how your fuel gauge lies, headlights that dodge other drivers, or the Mazda rotary? Vote below",
    "tiktok_caption": "Why electric cars make fake engine sounds, and who it's really for #ev #electriccar #cartok #howitworks #carfacts",
    "sources": [
        "https://govinfo.gov/content/pkg/FR-2016-12-14/pdf/2016-28804.pdf",
        "https://www.govinfo.gov/content/pkg/FR-2018-02-26/html/2018-03721.htm",
        "https://crashstats.nhtsa.dot.gov/Api/Public/Publication/812371",
        "https://legislation.gov.uk/eur/2014/540/annex/VIII/2017-09-22",
        "https://www.plm.automation.siemens.com/media/global/en/SiemensSW-Acoustic-vehicle-alerting-system_WhitePaper_tcm27-76714.pdf",
        "https://jalopnik.com/hyundai-really-wants-its-ioniq-5-n-ev-to-feel-like-a-ra-1850628672",
        "https://www.edmunds.com/car-news/hyundai-ev-fake-shift-expanding-to-more-cars.html",
    ],
}
