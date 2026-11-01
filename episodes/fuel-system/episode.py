"""Episode 6 — Where your gas goes: how a car's fuel system works (port injection, plus a direct-injection aside)."""
from ev.gfx import INK, RED

SLUG = "fuel-system"
TOPIC = "FUEL SYSTEM"
SUBTITLE = ["A pressurized pipeline from the tank", "to a timed mist at every cylinder"]
PUNCH = ("TANK, PUMP,", "RAIL, MIST.")
HOOK_TITLE = [[("WHERE YOUR ", INK), ("GAS", RED)], [("ACTUALLY GOES", INK)]]
END_WORD = ("outro", "tank,")
TOPIC_WORD = ("outro", "fuel")

LINES = [
    ("hook",    "Where does your gas actually go after you fill up?"),
    ("what",    "This is how a car's fuel system works. It's a pressurized pipeline from the tank to every cylinder."),
    ("problem", "The gas sits low in the tank, but the engine needs it up front, under pressure, "
                "at exactly the right moment."),
    ("parts",   "So an electric pump sits inside the tank, submerged in gas, which keeps it cool. "
                "A line runs through a filter to the fuel rail, which feeds one injector per cylinder."),
    ("how",     "The pump pushes fuel at forty to sixty pounds per square inch, and a regulator holds it steady."),
    ("key",     "Then the computer fires a pulse of electricity. An electromagnet pulls the injector open, "
                "and fuel bursts out as a fine mist, into the air rushing toward the intake valve."),
    ("result",  "Longer pulse, more fuel. An oxygen sensor in the exhaust reports if the mix is rich or lean, "
                "and the computer corrects it."),
    ("direct",  "Many newer engines add a second pump on the engine, and spray straight into the cylinder "
                "at far higher pressure."),
    ("outro",   "And the fumes? A charcoal canister traps them, and the engine burns them later. "
                "Tank, pump, rail, mist. That's the fuel system."),
]
GAPS = {"what": 0.2, "problem": 0.2, "parts": 0.2, "how": 0.2, "key": 0.3, "result": 0.2, "direct": 0.2,
        "outro": 0.3}

META = {
    "title": "Where does your gas go? How a car fuel system works #cars #engine #howitworks",
    "description": (
        "After you fill up, an electric fuel pump sitting inside the tank (submerged in gas, which also cools it) "
        "pushes fuel through a filter to the fuel rail. A regulator holds the pressure steady, typically around "
        "40 to 60 psi in a port-injected engine, and the rail feeds one injector per cylinder.\n\n"
        "Each injector is a solenoid valve. The engine computer energizes it, the valve opens and fuel sprays as a "
        "fine mist into the intake port. The longer the pulse, the more fuel; an oxygen sensor in the exhaust tells "
        "the computer whether the mix is rich or lean so it can correct it. Direct-injection engines add an "
        "engine-mounted high-pressure pump and spray straight into the cylinder. Tank vapors are stored in a "
        "charcoal canister and burned by the engine later. Animation simplified, not to scale.\n\n"
        "What should we take apart next? 👇\n#FuelSystem #HowItWorks #CarMaintenance"
    ),
    "tags": ["fuel system", "how a fuel system works", "how fuel injection works", "fuel pump", "fuel injector",
             "fuel rail", "where does gas go", "car fuel system explained", "port fuel injection",
             "direct injection", "how cars work", "engineering animation"],
    "first_comment": "Next up: how a sewing machine ties a knot you never see, the oil field pumpjack, or what your "
                     "clutch pedal actually does? Vote below 👇",
    "tiktok_caption": "Where does your gas actually go after you fill up? How a car fuel system works ⛽ "
                      "#cars #howitworks #engine #fuelinjection #carsoftiktok",
    "sources": [
        "https://en.wikipedia.org/wiki/Fuel_pump",
        "https://www.aa1car.com/library/fuel_injection_basics.htm",
        "https://www.aa1car.com/library/returnless_efi.htm",
        "https://en.wikipedia.org/wiki/Manifold_injection",
    ],
}
