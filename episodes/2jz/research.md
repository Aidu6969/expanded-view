# 2JZ — research notes (episode 8)

Angle: "Everyone says a stock 2JZ can take double its factory power." Answer: broadly yes for ~600 hp,
and here is the hardware that makes it so. Engine shown = 2JZ-GTE (Mk4 Supra twin-turbo).

## Facts stated in the video
| # | Claim (narration / on screen) | Source |
|---|---|---|
| 1 | 2JZ is a 3.0 litre (2,997 cc) straight six, used in the Toyota Supra; 86 mm bore x 86 mm stroke | https://en.wikipedia.org/wiki/Toyota_JZ_engine |
| 2 | Cast-iron block (aluminium head) — "not aluminium" refers to the block | https://en.wikipedia.org/wiki/Toyota_JZ_engine ("cast-iron block, aluminium cylinder head") |
| 3 | Closed-deck block | https://www.jdpower.com/cars/shopping-guides/guide-to-understanding-the-toyota-2jz-gte-engine ("cast iron, closed deck block"); https://www.enginelabs.com/news/inside-a-legend-tearing-down-a-2jz-engine-with-stephan-papadakis/ ("closed-deck beefy iron block"); https://nzperformance.co.nz/blogs/build-guides/how-much-power-can-a-stock-2jz-or-1jz-handle ("The closed-deck block and the iron construction") |
| 4 | Closed deck = the deck is solid around the cylinders (vs an open deck where the water jacket is open at the top), which supports the top of the bores | general definition; consistent with the sources above. Narration says only "solid around every cylinder, so the bores stay braced" |
| 5 | Forged steel crankshaft | J.D. Power ("counterweighted forged steel crankshaft"); EngineLabs ("the OEM crankshaft is a beefy forged unit") |
| 6 | Seven main bearings | https://motoiq.com/extreme-engine-tech-building-a-high-boost-2jz-with-brian-crower-and-je-pistons-part-1 ("With 7 main bearings the crank is well supported"); a seven-main straight six has a bearing between every crankpin: https://en.wikipedia.org/wiki/Straight-six_engine |
| 7 | A straight six has perfect primary and secondary balance; front and rear trios mirror each other | https://en.wikipedia.org/wiki/Straight-six_engine ("perfect primary and secondary engine balance"; "front and rear trio of cylinders moving in pairs"; "crank throws ... three planes offset at 120°") |
| 8 | Factory: two identical turbos in sequence; first one at low rpm, second joins around 4,000 rpm | Wikipedia ("sequential twin turbochargers"); J.D. Power ("One kicks in at low RPMs, and the other joins at 4,000. The turbos are also identical in size."); https://www.torquecars.com/toyota/2jz-tuning.php ("second turbo comes on stream by 4000rpm. Both turbos are the same size.") |
| 9 | Export (North America/Europe) rating 320 hp | Wikipedia ("320 hp (239 kW; 324 PS) at 5600 rpm") |
| 10 | Tuners run around 600 hp on stock internals ("double") | TorqueCars ("around 600bhp of reliable power on stock internals"); NZ Performance ("around 500 to 600hp as the sensible ceiling for the factory bottom end"); https://www.realstreetperformance.com/blog/how-much-will-a-stock-2jz-hold (engines kept "under 600whp" live long). EngineLabs reports 700-800 hp claims; we use the conservative ~600. |
| 11 | What usually kills a stock one is a bad tune / detonation hitting pistons and rods | NZ Performance ("Detonation from a lean or aggressive map hammers the rods and ring lands"); Real Street ("detonation can kill a stock engine very quickly, regardless of the power level") |

## On-screen extras
- Firing order 1-5-3-6-2-4, throws 1&6 / 2&5 / 3&4 paired at 120° — standard straight-six layout (Wikipedia straight-six: three planes 120° apart).
- Balance graph is computed from slider-crank kinematics (stroke 86, rod 142 mm): primary + secondary
  inertia terms of one piston vs the sum of six (sums to zero for both orders).
- Rod length 142 mm is used only for the model geometry (not stated in narration).

## Unsure / resolved
- Open vs closed deck: Wikipedia is silent; three independent sources say closed deck. Kept.
- "Double": Japanese cars were rated 280 PS (Gentlemen's Agreement); export 320 hp. We quote 320 and
  "around six hundred", i.e. roughly double — not the 700-800 hp folklore.
- Rod/piston materials: not confirmed as forged by any source, so the video does not call them forged.
- Sequential system detail (exhaust bypass valve pre-spools turbo 2): only forum sources; not stated.
- Japanese 280 PS figure: not used.

## Misconceptions avoided
- "The 2JZ has forged rods and pistons" — not claimed.
- "Any stock 2JZ holds 1,000 hp" — not claimed; we say ~600 and name detonation as the usual killer.
