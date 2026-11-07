# Research: How a rotary engine works (Mazda 13B)

Sources read 2026-11-07:
- [A] Autocar, "Under the skin: understanding the bizarre workings of rotary engines" — https://www.autocar.co.uk/car-news/technology/under-skin-understanding-bizarre-workings-rotary-engines
- [C] CarsGuide, "What is a rotary engine?" (2018) — https://www.carsguide.com.au/car-advice/what-is-a-rotary-engine-37430
- [H] How a Car Works, "How a rotary Wankel engine works" — https://www.howacarworks.com/technology/how-a-rotary-wankel-engine-works
- [W] WardsAuto, "Mazda 1.3L Renesis rotary" (Ten Best Engines archive, 2005) — https://www.wardsauto.com/news/archive-wards-mazda-1-3l-renesis-rotary/767389/
- [R] australiancar.reviews, "Mazda 13B-MSP 'Renesis' engine" — https://australiancar.reviews/?p=52354

## Facts stated in the video
| # | Claim (narration / screen) | Source |
|---|---|---|
| 1 | Fans say a (twin-rotor) rotary has only three moving parts: two rotors + the output shaft. | [C] "For a twin-rotor setup, there are only three." [A] "a much smaller parts count than a piston engine" |
| 2 | The 13B is a twin-rotor, 1.3 L engine; 654 cc per rotor, 1,308 cc total (screen). | [H] "1308cc (654cc per rotor)"; [W] "1.3L twin-rotor rotary", 1,308 cc; [R] page title "Mazda 13B-MSP 'Renesis' engine" |
| 3 | A piston engine moves pistons up and down and needs camshafts and valves; the rotary has no poppet valves or valvetrain and no reciprocating parts. | [A] "There are no poppet valves or valvetrain", "no reciprocating parts at all"; [C] "does away with pistons, valves, camshafts" |
| 4 | The housing is roughly oval (epitrochoid); the rotor is a triangle with slightly convex faces. | [C] rotor "shaped much like a triangle, but each face ... slightly convex"; housing "basically oval-shaped ... epitrochoid shape"; [A] "triangular-shaped rotor" |
| 5 | Two rotors on one eccentric shaft. | [A] "most common format is twin-rotor"; [W] twin-rotor; [H] planetary gearing links rotor to output shaft on an eccentric orbit |
| 6 | A gear inside the rotor rolls around a fixed gear; the shaft turns three times per rotor turn. | [A] rotor has a "toothed hole at its centre that engages with a fixed gear"; shaft rotates "three times for every single rotation of the rotor". [C] same 3:1 |
| 7 | Triangle in an oval leaves three gaps = three chambers. | [C] the rotor "creates three separate sealed-off areas" |
| 8 | Each chamber grows, shrinks, grows, shrinks: intake, compression, power, exhaust, once per rotor turn; three power strokes per rotor turn. | [H] "the same four-stroke cycle ... induction, compression, power and exhaust", "three power strokes for each revolution of the rotor"; [A] each rotor makes power once per crankshaft revolution |
| 9 | No valves: the rotor itself uncovers and covers ports in the housing as it passes. | [A] "ports that are opened and closed as the rotor passes over them, doing away with the need for valves" |
| 10 | Apex seals on the three tips seal the chambers; they wear and compression is lost. | [H] "These seals were prone to wear and breakdown, causing the engine to lose compression and hence power"; [C] seal failures make chambers "leak into each other"; [A] names the apex seals |

## Animation model (geometry, not a claim in narration)
- Wankel kinematics: rotor centre orbits the shaft centre at eccentricity e; rotor turns at 1/3 shaft speed in the
  same direction. Housing = epitrochoid x = e·cos3α + R·cos α, y = e·sin3α + R·sin α; the apexes lie on it exactly.
  R/e = 7 (Mazda's 13B: R = 105 mm, e = 15 mm is the commonly quoted generating geometry; used only as a
  proportion, not stated).
- Internal ring gear : fixed gear = 3 : 2 (drawn 36 : 24 teeth) gives the 1/3 ratio (rolling-contact check in
  scene.check_physics). Sources only say "fixed gear" and "three times", so no tooth numbers are stated.
- Ports drawn as side ports in the side housing (Renesis-style; narration only says "ports cut into the housing", so no port type is claimed);
  the rotor body really covers them in the animation (point-in-polygon), and check_physics asserts that the intake
  port is only uncovered by an expanding chamber and the exhaust port only by a shrinking one, outside the overlap
  around top dead centre.
- Plugs drawn at the minor axis opposite the ports; spark when the tracked chamber is at minimum volume.

## Unsure / resolved
- "Three moving parts" is a fan simplification (oil pump, etc. ignored) — framed as "Fans say", source [C].
- Redline (9,000 rpm Renesis per [W]) not used, to keep the script on mechanism.
- Older 13Bs used peripheral exhaust ports; narration says only "ports cut into the housing", true for both.
- Spark plug count per rotor not stated (only [H] "two spark plugs" generically); two plugs drawn, no claim.

## Misconceptions avoided
- Not "no pistons at all, so no compression": it still runs the four-stroke cycle.
- Not "the shaft and rotor turn at the same speed": shaft is 3x.
- Not claiming rotaries always fail: we say seals wear and compression leaks.
