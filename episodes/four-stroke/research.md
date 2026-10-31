# FOUR STROKES — research notes

Every fact the narration states, with a source. Unsure items and how they were resolved.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | At 3,000 RPM each cylinder fires 25 times a second | Arithmetic from #3: one power stroke per two crank revolutions -> 3000 / 2 = 1500 per minute = 25 per second. https://en.wikipedia.org/wiki/Four-stroke_engine |
| 2 | Four strokes: intake, compression, power, exhaust | https://en.wikipedia.org/wiki/Four-stroke_engine ; https://www.britannica.com/technology/four-stroke-cycle |
| 3 | Four strokes of the piston = two turns of the crankshaft per cycle | https://en.wikipedia.org/wiki/Four-stroke_engine ("the crankshaft completes two revolutions per cycle"); Britannica four-stroke cycle |
| 4 | Connecting rod links piston to crankshaft, converting reciprocating motion to rotation | https://en.wikipedia.org/wiki/Connecting_rod ; https://en.wikipedia.org/wiki/Crankshaft |
| 5 | Head has intake and exhaust valves and a spark plug (spark-ignition engine) | https://en.wikipedia.org/wiki/Four-stroke_engine |
| 6 | Intake: intake valve open, piston moves down, draws in air and fuel | Wikipedia Four-stroke engine (intake stroke). Note: true for port-injected / carburetted engines; direct-injection engines draw air and inject fuel into the cylinder. Kept "air and fuel" as the classic description; noted as a simplification in the description. |
| 7 | Compression: both valves closed, piston squeezes the mixture | Wikipedia Four-stroke engine; Britannica |
| 8 | "About ten times smaller": typical petrol compression ratio ~10:1 | https://en.wikipedia.org/wiki/Compression_ratio (typical petrol engines roughly 8:1 to 12:1; modern ones often ~10-13:1). "About ten" is a fair round figure. The animation's clearance volume is set to exactly 10:1. |
| 9 | Spark fires just before the piston reaches the top (spark advance, BTDC) | https://en.wikipedia.org/wiki/Ignition_timing (spark timed before TDC so peak pressure arrives just after TDC) |
| 10 | Burning gas expands and pushes the piston down; the power stroke is the only one that produces work | Wikipedia Four-stroke engine; Britannica ("only the power stroke delivers work") |
| 11 | Exhaust: exhaust valve opens, rising piston pushes burnt gas out | Wikipedia Four-stroke engine |
| 12 | A flywheel's stored energy carries the crank through the non-power strokes | https://en.wikipedia.org/wiki/Flywheel ; https://www.kfz-tech.de/Engl/Schwungrad.htm |
| 13 | Camshaft turns at half crankshaft speed, so each valve opens once per cycle (every two crank turns) | https://en.wikipedia.org/wiki/Camshaft (four-stroke camshafts rotate at half the crankshaft speed) |
| 14 | Nikolaus Otto built the first practical four-stroke engine in 1876 | https://en.wikipedia.org/wiki/Otto_engine ; https://accelleron.com/charge-magazine/how-nikolaus-august-otto-created-the-4-stroke-internal-combustion-engine (Beau de Rochas described the cycle in 1862, hence "first practical") |
| 15 | "Suck, squeeze, bang, blow" mnemonic | Common mechanics' mnemonic for the four strokes, e.g. https://motoiq.com/suck-squish-bang-blow-part-six-ignition-timing-basics |

## Misconceptions to avoid
- The spark does not fire exactly at the top; it is advanced (before TDC). Script says "just before the top".
- It is not an explosion that kicks the piston; it is fast burning + gas expansion ("burning gas expands").
- Cam at half speed, not crank speed.
- Otto did not invent the concept (Beau de Rochas 1862): "first practical one".

## Simplifications made on screen
- Single cylinder, DOHC with direct-acting buckets, timing belt 2:1 sprockets. Animation slowed and stopped
  between strokes so each one is readable.
- Valve events drawn exactly at TDC/BDC (no overlap, no early exhaust opening); real engines open/close a little
  before/after.
- Spark drawn ~20 crank degrees before TDC.
