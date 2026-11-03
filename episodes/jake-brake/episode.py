"""Episode: How a Jake brake works (compression release engine brake). See research.md for every fact.
First episode in the upgraded look (real-world opening, lit environment, camera moves)."""
from ev.gfx import INK, RED

SLUG = "jake-brake"
TOPIC = "JAKE BRAKE"
SERIES = ("HOW IT WORKS", 1)
SUBTITLE = ["The exhaust valve opens at the top", "of compression: the engine eats the energy"]
PUNCH = ("THE TRUCK IS", "DRIVING THE ENGINE.")
HOOK_TITLE = [[("WHY TRUCKS SOUND LIKE", INK)], [("MACHINE GUNS", RED)]]
END_WORD = ("outro", "the", 2)
TOPIC_WORD = ("outro", "jake")

LINES = [
    ("hook",    "That machine gun sound from trucks going downhill? It's the engine fighting itself. On purpose."),
    ("what",    "It's called a Jake brake. Here's how a Jake brake actually works."),
    ("problem", "A loaded semi on a long downhill can't ride its wheel brakes the whole way. They'd overheat."),
    ("normal",  "Off the fuel, every piston still squeezes air on the way up. But that air pushes the piston back "
                "down, like a spring. Most of the energy comes back."),
    ("jake",    "The Jake brake breaks the spring. Using engine oil pressure, it pops the exhaust valve open, just "
                "before the top of the stroke."),
    ("key",     "Bang. The squeezed air blasts out the exhaust. Nothing is left to push the piston back down. "
                "That energy is gone."),
    ("result",  "Now the engine is an air compressor the truck has to turn. That holds it back, and the wheel brakes "
                "stay cool."),
    ("sound",   "Each blast is a sharp pulse of air out the exhaust. Six cylinders, back to back. That's the machine "
                "gun. It's so loud, many towns post No Engine Brake signs."),
    ("outro",   "So the engine isn't driving the truck. The truck is driving the engine. That's the Jake brake."),
]
GAPS = {"what": 0.25, "problem": 0.3, "normal": 0.3, "jake": 0.3, "key": 0.35, "result": 0.3, "sound": 0.3,
        "outro": 0.3}
SAY = {"Jake": "Jake"}

META = {
    "title": "Why trucks sound like machine guns downhill: how a Jake brake works #trucks #jakebrake #engineering",
    "description": (
        "A Jake brake (compression release engine brake) opens the exhaust valve right before the top of the "
        "compression stroke. The air the piston just squeezed blasts out of the exhaust instead of pushing the "
        "piston back down, so the energy is thrown away and the engine becomes an air compressor the truck has to "
        "turn. That holds a loaded truck back on long grades and keeps the wheel brakes cool for emergencies.\n\n"
        "The sharp release from each cylinder is the machine-gun sound, which is why many towns post No Engine "
        "Brake signs, usually aimed at unmuffled trucks. The name comes from Jacobs, the first company to make "
        "them; Clessie Cummins invented the system. Animation simplified and slowed.\n\n"
        "What truck or car sound should we explain next?"
    ),
    "tags": ["jake brake", "how a jake brake works", "engine brake", "compression release brake", "semi truck",
             "truck sounds", "why trucks sound like machine guns", "diesel engine", "trucking", "engine animation"],
    "first_comment": "Next: why EVs fake engine sounds, how your fuel gauge lies, or the RB26? Vote below",
    "tiktok_caption": "Why trucks sound like machine guns going downhill: how a Jake brake works #jakebrake #trucktok #semitruck #diesel #howitworks",
    "sources": [
        "https://en.wikipedia.org/wiki/Compression_release_engine_brake",
        "https://ethw.org/ASME-Landmark:Jacobs_Engine_Brake_Retarder",
        "https://www.slashgear.com/1943176/what-do-no-engine-brake-signs-mean/",
    ],
}
