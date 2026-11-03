"""Long-form #1: The history of the Honda NSX (first generation 1990-2005, closing note on 2016-2022).
Every fact is in research.md with a source. Photos: licensed Wikimedia Commons files only (assets/manifest.yaml).

ASSET IDS used below must be added with `python -m ev.long.assets add long/honda-nsx <id> "File:..."` once
commons.wikimedia.org / upload.wikimedia.org are allowed (docs/SETUP_ACCOUNTS.md step 3). Candidates per id are
in research.md section 3; check each license (the tool refuses NC/ND) and look at the photo before adding it.
  nsx_red_side   1991 NSX, red, side            nsx_front    first-gen NSX front, pop-up lights
  nsx_rear       first-gen NSX rear             nsx_show     NSX at a show (wide)
  nsx_interior   first-gen cockpit (verify gen) c30a         C30A engine
  c32b           C32B engine                    nordschleife Nürburgring Nordschleife
  suzuka         Suzuka circuit                 nsx_r        1992 NSX-R
  nsx_t          NSX-T targa                    nsx_2002     2002+ facelift, fixed headlights
  nsx_r2         2002 NSX-R (NA2)               ferrari_348  Ferrari 348 (rival)
  nsx_gen2       second-gen NSX                 nsx_type_s   second-gen Type S
"""

SLUG = "honda-nsx"
TITLE = "The Honda NSX"
FORMAT = "long"

LINES = [
    # ---- cold open: the open loop (paid off in "senna")
    ("hook", "There's a legend every car fan has heard. Ayrton Senna, the greatest driver of his era, took a Honda "
             "prototype, told the engineers it wasn't good enough, and turned it into the car that scared Ferrari. "
             "It's a great story. Honda's own records tell a different one. And the truth about how the NSX was "
             "actually made is a lot more interesting."),
    ("stakes", "In 1990, Honda put a mid-engine supercar on sale. Acura called it the first supercar from Japan. It had an aluminium body "
               "nobody had mass-produced before, an engine with titanium connecting rods, and it was meant to be "
               "easy to live with. This is the history of the Honda NSX."),
    # ---- part 1: the idea
    ("idea_ch", "Part one. The idea."),
    ("idea1", "It started in 1984, with a strange little test car. Honda's engineers at the Wako research centre took "
              "a tiny first generation City, and moved the engine to the middle, ahead of the rear wheels. They "
              "called the layout U M R: underfloor, midship engine, rear wheel drive."),
    ("idea2", "The same year, Honda asked the Italian design house Pininfarina to build a concept around the idea. "
              "The H P X had a two litre V6 mounted behind the driver. It was only a show car. But it told Honda the "
              "concept could work."),
    ("idea3", "Full development began in the autumn of 1985, under project leader Shigeru Uehara. Honda quotes him "
              "saying it's the dream of every development engineer to create a sports car. The prototype got a "
              "working name: N S X. New Sportscar eXperimental."),
    ("idea4", "The first prototype was running by the middle of 1986. It would take four more years, a new "
              "kind of body, and a new factory, before anyone could buy one."),
    # ---- part 2: aluminium
    ("alu_ch", "Part two. The aluminium gamble."),
    ("alu1", "Uehara's team wanted the car light, and steel was too heavy. So Honda did something no carmaker had "
             "done in a production car. The NSX got an all aluminium monocoque. Honda calls it a world first for a "
             "production vehicle at the time."),
    ("alu2", "Honda says the switch took about 140 kilograms out of the body, and nearly 200 kilograms out of the "
             "whole car. The body used five different aluminium alloys. But aluminium is hard to work with. Honda "
             "heated it to 600 degrees and pushed it through a die, to make the honeycomb section side sills. And "
             "because aluminium carries heat away so fast, Honda Engineering had to design a new spot welder, with "
             "far more current."),
    ("alu3", "Then it built a dedicated factory, in Tochigi, finished in May 1990. There was no conveyor belt. "
             "Skilled workers were picked from across Honda, the bodies turned on rotating welding tables, and the "
             "plant built about 25 cars a day."),
    ("alu4", "All that work shows in the numbers. At launch, a Japanese market NSX with the manual gearbox "
             "weighed 1,350 kilograms. For a mid-engine car with a three litre V6, that was light."),
    # ---- part 3: the engine
    ("eng_ch", "Part three. The heart."),
    ("eng1", "The original plan was a three litre V6 without VTEC, at around 250 horsepower. Late in development, "
             "Honda changed its mind. The production car got the C30A: a three litre, ninety degree V6, with double "
             "overhead cams and VTEC, mounted sideways behind the seats."),
    ("eng2", "VTEC gave it two personalities. Below 5,800 RPM, mild cam lobes kept it smooth. Above that, the tall "
             "lobes took over, and it pulled to an 8,000 RPM red line. In Japan it made 280 metric horsepower. "
             "In America, 270."),
    ("eng3", "To rev like that, the parts had to be light. The NSX was the first production car with titanium "
             "connecting rods. Honda says each one was about 30 percent lighter than steel, and that alone raised "
             "the engine's maximum speed by about 700 RPM."),
    ("eng4", "Around the engine, Uehara's team reportedly studied the cockpit of an F 16 fighter jet, for its "
             "all round visibility. The result was a low glass canopy with a wide view out."),
    # ---- part 4: the Green Hell
    ("ring_ch", "Part four. The Green Hell."),
    ("ring1", "Honda didn't tune the NSX on a test track in Japan. It went to Germany. Honda R and D Europe set up "
              "a garage in Müllenbach, two kilometres from the Nürburgring Nordschleife. Over twenty kilometres "
              "long, with more than 200 corners, many of them blind."),
    ("ring2", "Honda calls it the first long term overseas test by a Japanese carmaker. Lap after lap, the Ring "
              "found every weakness in the chassis. And this is where the real stiffening happened. Honda says the "
              "German testing raised the body's rigidity by fifty percent. The team also spent a month at Suzuka, "
              "Honda's own circuit, early in development."),
    # ---- part 5: Senna (pays off the hook)
    ("senna_ch", "Part five. Enter Senna."),
    ("senna1", "So where does Senna come in? In February 1989, the reigning Formula One champion, who drove for "
               "McLaren Honda, got to drive the car. Honda quotes what he told them: I'm not sure I can give you "
               "proper advice on a mass production car. But I feel it's a little fragile."),
    ("senna2", "He meant rigidity. And two months later, Honda's own timeline shows the rigidity targets were "
               "raised. So Senna's feedback mattered. But he wasn't the development driver. That was Honda's "
               "Motoharu Kurosawa. And the fifty percent came from the Nürburgring. The legend isn't wrong. It's "
               "just the short version."),
    # ---- part 6: launch
    ("launch_ch", "Part six. The shock."),
    ("launch1", "The NSX made its world debut at the Chicago Auto Show, on February 9th, 1989, as an Acura. It went "
                "on sale in America in the summer of 1990, at 65 thousand dollars. Acura called it the most "
                "expensive Japanese car in history. In Japan, sales started that September, and some buyers waited "
                "up to three years for one."),
    ("launch2", "What shocked people wasn't only the speed. It was a mid-engine exotic you could use every day. "
                "Motor Trend called it the best sports "
                "car ever built. Hagerty would later say it proved you could have exoticism and usability, and "
                "called Ferrari's 348 a much more difficult car to drive."),
    ("launch3", "Even Gordon Murray, who was designing the McLaren F1, drove one. He later said the NSX's ride and "
                "handling became the F1's new design target. He'd asked Honda for an engine first. Honda said no, "
                "and the F1 got a BMW V12 instead."),
    # ---- part 7: evolution
    ("launch4", "In its first year, Acura sold 1,940 of them in America. By the end of 2004, American sales had "
                "reached 8,733. For a 65 thousand dollar car, built at 25 a day, that was a hit."),
    ("evo_ch", "Part seven. Fifteen years."),
    ("evo1", "Honda kept improving it. In 1992, the Japan only NSX R stripped out about 120 kilograms. Only 483 "
             "were built. In 1995 came the NSX T, with a removable roof. In 1997 the manual cars got a bigger 3.2 "
             "litre V6, and a six speed gearbox, with 290 horsepower in America."),
    ("evo1b", "The 1995 update also brought an automatic with Sequential SportShift. And in 1999, Acura built the Alex "
              "Zanardi Edition for America: a hard top coupe, limited to 49 cars, with revised suspension, and 149 "
              "pounds less weight."),
    ("evo2", "In 2002 the pop up headlights were replaced with fixed xenon lamps, and a second NSX R arrived, "
             "almost 100 kilograms lighter than the standard car. By the end of 2005, after fifteen years, "
             "production stopped. Honda had sold just over 18,000 of them."),
    ("evo3", "Even its home moved. In the early 2000s, production left the Tochigi plant it was born in, and went "
             "to Honda's factory in Suzuka."),
    ("gen2", "The name came back in 2016, as something completely different. A twin turbo V6, three electric "
             "motors, all wheel drive, and 573 horsepower, built in Ohio. The final Type S made 602. The last one "
             "left the factory in November 2022."),
    # ---- outro
    ("outro", "So, did Senna make the NSX? He told Honda it felt a little fragile, and Honda listened. But the car "
              "was made by a test car built from a City, a factory with no conveyor belt, titanium rods, and "
              "thousands of laps of the Green Hell. Senna made it famous. Honda's engineers made it great."),
    ("cta", "If you want to see what VTEC is actually doing inside that engine, the animation is on this channel. "
            "And tell me in the comments: which legend should we tell next?"),
]

SHOTS = {
    "hook": [{"type": "title", "text": "THE HONDA NSX", "sub": "THE SUPERCAR SENNA BUILT?"},
             {"type": "photo", "asset": "nsx_red_side", "at": "prototype,", "move": "push"},
             {"type": "fact", "text": "\"SENNA MADE THE NSX\"", "sub": "THE LEGEND", "at": "story.", "asset": "nsx_front"},
             {"type": "photo", "asset": "nsx_rear", "at": "truth", "move": "pull"}],
    "stakes": [{"type": "photo", "asset": "nsx_show", "move": "pan_l", "label": "HONDA NSX · 1990"},
               {"type": "specs", "title": "WHAT MADE IT DIFFERENT", "at": "aluminium",
                "rows": [("Body", "All-aluminium monocoque"), ("Engine", "3.0 L V6 with VTEC"),
                         ("Connecting rods", "Titanium"), ("Layout", "Mid-engine, RWD")]}],
    "idea_ch": [{"type": "chapter", "no": 1, "title": "THE IDEA", "asset": "nsx_front"}],
    "idea1": [{"type": "timeline", "title": "HOW IT STARTED",
               "items": [("1984", "UMR test car from a Honda City"), ("1984", "Pininfarina HP-X concept"),
                         ("1985", "Full development begins"), ("1989", "Chicago reveal"), ("1990", "On sale")]}],
    "idea2": [{"type": "fact", "text": "HP-X\nPININFARINA, 1984", "sub": "2.0 L V6 · MID-ENGINE · CONCEPT ONLY"}],
    "idea3": [{"type": "fact", "text": "N · S · X", "sub": "NEW SPORTSCAR eXPERIMENTAL", "asset": "nsx_show"}],
    "alu_ch": [{"type": "chapter", "no": 2, "title": "THE ALUMINIUM GAMBLE", "asset": "nsx_red_side"}],
    "alu1": [{"type": "photo", "asset": "nsx_red_side", "move": "pan_r", "label": "ALL-ALUMINIUM MONOCOQUE"}],
    "alu2": [{"type": "specs", "title": "ALUMINIUM VS STEEL (HONDA)", "highlight": 1,
              "rows": [("Body", "~140 kg lighter"), ("Whole car", "~200 kg lighter"), ("Alloys used", "5"),
                       ("Extrusion temp.", "600 °C")]},
             {"type": "fact", "text": "A NEW SPOT WELDER", "sub": "ALUMINIUM DRAINS HEAT: IT NEEDED MORE CURRENT",
              "at": "because"}],
    "alu3": [{"type": "fact", "text": "TOCHIGI, MAY 1990\nNO CONVEYOR BELT", "sub": "ABOUT 25 CARS A DAY"}],
    "idea4": [{"type": "photo", "asset": "nsx_rear", "move": "pan_l"}],
    "alu4": [{"type": "specs", "title": "NSX (JAPAN, 1990)", "highlight": 0,
              "rows": [("Weight, manual", "1,350 kg"), ("Length", "4,430 mm"), ("Height", "1,170 mm")]}],
    "launch4": [{"type": "specs", "title": "SALES IN AMERICA", "highlight": 1,
                 "rows": [("First year", "1,940"), ("By end of 2004", "8,733")]}],
    "evo1b": [{"type": "fact", "text": "ZANARDI EDITION", "sub": "1999 · 49 CARS · 149 LB LIGHTER", "asset": "nsx_r"}],
    "evo3": [{"type": "photo", "asset": "suzuka", "move": "pan_r", "label": "SUZUKA"}],
    "eng_ch": [{"type": "chapter", "no": 3, "title": "THE HEART", "asset": "c30a"}],
    "eng1": [{"type": "photo", "asset": "c30a", "move": "push", "label": "C30A · 3.0 L V6 · VTEC"}],
    "eng2": [{"type": "specs", "title": "C30A (1990)", "highlight": 1,
              "rows": [("VTEC switch", "5,800 rpm"), ("Red line", "8,000 rpm"), ("Japan", "280 PS"),
                       ("USA", "270 hp")]}],
    "eng3": [{"type": "fact", "text": "TITANIUM CONNECTING RODS", "sub": "A PRODUCTION-CAR FIRST · ~30% LIGHTER · +700 RPM"},
             {"type": "photo", "asset": "c32b", "at": "alone", "move": "pull"}],
    "eng4": [{"type": "photo", "asset": "nsx_interior", "move": "push", "label": "THE CANOPY"}],
    "ring_ch": [{"type": "chapter", "no": 4, "title": "THE GREEN HELL", "asset": "nordschleife"}],
    "ring1": [{"type": "photo", "asset": "nordschleife", "move": "pan_l", "label": "NÜRBURGRING NORDSCHLEIFE"}],
    "ring2": [{"type": "fact", "text": "+50% RIGIDITY", "sub": "FROM THE GERMAN TESTING (HONDA)"},
              {"type": "photo", "asset": "suzuka", "at": "month", "move": "push", "label": "SUZUKA"}],
    "senna_ch": [{"type": "chapter", "no": 5, "title": "ENTER SENNA", "asset": "nsx_front"}],
    "senna1": [{"type": "fact", "text": "\"I FEEL IT'S A\nLITTLE FRAGILE.\"", "sub": "AYRTON SENNA, FEBRUARY 1989 (VIA HONDA)"}],
    "senna2": [{"type": "timeline", "title": "WHAT ACTUALLY HAPPENED",
                "items": [("FEB 1989", "Senna: \"a little fragile\""), ("APR 1989", "Rigidity targets raised"),
                          ("NÜRBURGRING", "+50% body rigidity"), ("DEV. DRIVER", "Motoharu Kurosawa")]}],
    "launch_ch": [{"type": "chapter", "no": 6, "title": "THE SHOCK", "asset": "nsx_show"}],
    "launch1": [{"type": "photo", "asset": "nsx_show", "move": "pan_r", "label": "CHICAGO · 9 FEB 1989"},
                {"type": "fact", "text": "$65,000", "sub": "\"THE MOST EXPENSIVE JAPANESE CAR IN HISTORY\" (ACURA)",
                 "at": "65"}],
    "launch2": [{"type": "compare", "left": ("Honda NSX", "nsx_red_side"), "right": ("Ferrari 348", "ferrari_348"),
                 "rows": [("Layout", "Mid V6", "Mid V8", ""), ("Daily use", "Easy", "Demanding", "L")]}],
    "launch3": [{"type": "fact", "text": "THE McLAREN F1'S\nDESIGN TARGET", "sub": "GORDON MURRAY ON THE NSX'S RIDE AND HANDLING"}],
    "evo_ch": [{"type": "chapter", "no": 7, "title": "FIFTEEN YEARS", "asset": "nsx_2002"}],
    "evo1": [{"type": "photo", "asset": "nsx_r", "move": "push", "label": "NSX-R · 1992 · 483 BUILT"},
             {"type": "photo", "asset": "nsx_t", "at": "1995", "move": "pan_l", "label": "NSX-T · 1995"},
             {"type": "specs", "title": "1997: 3.2 L", "at": "1997",
              "rows": [("Engine", "C32B 3.2 L V6"), ("Gearbox", "6-speed manual"), ("USA", "290 hp")]}],
    "evo2": [{"type": "photo", "asset": "nsx_2002", "move": "push", "label": "2002 FACELIFT"},
             {"type": "photo", "asset": "nsx_r2", "at": "second", "move": "pull", "label": "NSX-R · 2002"},
             {"type": "fact", "text": "18,000+", "sub": "SOLD IN 15 YEARS", "at": "production"}],
    "gen2": [{"type": "photo", "asset": "nsx_gen2", "move": "push", "label": "NSX · 2016"},
             {"type": "photo", "asset": "nsx_type_s", "at": "final", "move": "pull", "label": "NSX TYPE S · 602 HP"}],
    "outro": [{"type": "photo", "asset": "nsx_front", "move": "pull"},
              {"type": "fact", "text": "SENNA MADE IT FAMOUS.\nHONDA'S ENGINEERS MADE IT GREAT.", "at": "senna",
               "asset": "nsx_rear"}],
    "cta": [{"type": "title", "text": "EXPANDED VIEW", "sub": "WHICH LEGEND NEXT?"}],
}

CHAPTERS = [("idea_ch", "The idea"), ("alu_ch", "The aluminium gamble"), ("eng_ch", "The heart: C30A and VTEC"),
            ("ring_ch", "The Green Hell"), ("senna_ch", "Enter Senna"), ("launch_ch", "The shock"),
            ("evo_ch", "Fifteen years, and the second NSX")]

SAY = {"Müllenbach": "Mullen-bakh", "Nürburgring": "Nurburgring", "Uehara": "Weh-hah-rah",
       "Kurosawa": "Koo-ro-sah-wah", "Tochigi": "Toh-chee-ghee", "Wako": "Wah-koh", "Pininfarina": "Pinin-fareena",
       "C30A": "C thirty A", "F1's": "F one's", "F1": "F one", "R": "R"}

SFX = [("hook", "legend", "whoosh_big", 0.5), ("idea_ch", "Part", "impact", 0.4), ("alu_ch", "Part", "impact", 0.4),
       ("eng_ch", "Part", "impact", 0.4), ("ring_ch", "Part", "impact", 0.4), ("senna_ch", "Part", "impact", 0.4),
       ("launch_ch", "Part", "impact", 0.4), ("evo_ch", "Part", "impact", 0.4), ("eng2", "Above", "nsx_vtec", 0.5)]
SFX_PROMPTS = {"nsx_vtec": ("naturally aspirated sports car V6 engine revving hard past 6000 rpm, cam changeover, "
                            "exterior recording, no music", 3.0)}

META = {
    "title": "The Honda NSX: the supercar Senna didn't build (full history)",
    "description": (
        "Everyone says Ayrton Senna made the Honda NSX. He did drive a prototype in 1989 and told Honda it felt "
        "\"a little fragile\". But the real story of how the NSX was made runs through a Honda City test mule, the "
        "first all-aluminium monocoque in a production car, titanium connecting rods, a factory with no conveyor "
        "belt, and thousands of laps of the Nürburgring.\n\n"
        "Sources: Honda Global heritage and engine pages, Acura's NSX chronology, Honda press releases, Wikipedia, "
        "Hagerty. Figures differ by market; we use Honda's own numbers where they exist.\n\n"
        "Which legendary car should we cover next?"
    ),
    "tags": ["honda nsx", "nsx history", "acura nsx", "senna nsx", "honda nsx documentary", "nsx type r",
             "c30a", "vtec", "japanese supercar", "jdm legends", "car history", "nsx 1990"],
    "first_comment": "Next long story: Toyota Supra, Mazda RX-7, or Nissan Skyline GT-R? Vote below.",
    "category": "AUTOS_VEHICLES",
}
