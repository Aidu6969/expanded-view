# MATRIX HEADLIGHTS (adaptive driving beam) — research notes

Every fact the narration states, with a source. Researched 2026-11-06.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | High beams light the road much farther ahead (than low beams). | NHTSA final rule, 87 FR 9916 (Feb 22, 2022), p. 9918: lower beams provide "reduced light intensity in longer-distance regions"; upper beams "relatively high levels of illumination in both close-in and longer distance regions" and "are intended primarily for distance illumination" https://www.govinfo.gov/content/pkg/FR-2022-02-22/html/2022-02451.htm |
| 2 | High beams dazzle other drivers, so most people barely use them. | NHTSA rule, p. 9919: "Research has shown that most drivers under-utilize the upper beams"; upper beams are for use "when not meeting or closely following another vehicle". IIHS: "Few drivers use their high beams" https://www.iihs.org/news/detail/few-drivers-use-their-high-beams-study-finds |
| 3 | In one study, only 18% of drivers alone on the road had high beams on. | IIHS (2016): "Of about 3,200 isolated vehicles observed, 18 percent had their high beams on." Isolated = "other vehicles were 10 seconds or more away". Same URL. |
| 4 | The high beam is cut into slices (segments); each LED lights its own slice. | Audi Technology Portal: "the high-beam unit is made up of 25 individual segments ... light-emitting diodes ... are activated and deactivated or dimmed individually" https://www.audi-technology-portal.de/en/electrics-electronics/lighting-technology/matrix-led-headlights ; Audi press text quoted by Autoblog: "In each headlight, 25 light-emitting diodes generate a highly variable high-beam light" https://www.autoblog.com/2013/08/14/audi-a8-matrix-led-headlight/ |
| 5 | Audi A8, 2013: 25 LEDs per headlight (high beam). | Autoblog, Aug 14, 2013 (A8 shown at Frankfurt, Sept 2013): "In each headlight, 25 light-emitting diodes generate a highly variable high-beam light." Audi portal (status 2013): 25 segments. |
| 6 | A camera watches for other cars, oncoming and ahead. | Audi press text (Autoblog): "When the on-board camera detects other vehicles ahead..."; Audi portal: "other cars, which it recognizes using a camera". NHTSA rule: ADB reacts to "oncoming or preceding vehicles". evkx: "A forward camera and other vehicle inputs provide information about traffic" https://evkx.net/dictionary/matrix-led-headlights |
| 7 | It switches off only the LEDs aimed at the other car; every other slice stays on full. | Audi (Autoblog): "the Audi Matrix LED headlights mask the relevant sections of the high-beam by dimming or shutting off individual diodes. Very bright illumination is preserved in the remaining zones." NHTSA: "less illumination to occupied areas of the road and more illumination to unoccupied areas"; for LED lamps systems "extinguish individual LEDs". evkx: "dim or switch off selected light segments around detected oncoming or preceding vehicles while keeping more of the high beam active elsewhere". |
| 8 | Road full of traffic: basically a low beam. Empty road: full high beam. | NHTSA rule, p. 9919: "When the roadway ahead is fully occupied by oncoming or preceding vehicles, the adaptive beam is essentially a lower beam. When there are no oncoming or preceding vehicles, the adaptive beam is essentially an upper beam." |
| 9 | In America it only became legal in 2022. | NHTSA final rule permitting ADB headlamps, Federal Register Vol. 87 No. 35, Feb 22, 2022, effective Feb 22, 2022 (same govinfo URL). SEMA: "NHTSA Issues Final Rule Allowing Adaptive Driving Beam Headlights" https://www.sema.org/news-media/enews/2022/07/nhtsa-issues-final-rule-allowing-adaptive-driving-beam-headlights |

## Unsure / resolved
- "First car with matrix headlights": NOT claimed. Sources only confirm the 2013 A8 had them; the script says
  "On the Audi A8 back in twenty thirteen", not "the first".
- 25 "LEDs" vs 25 "segments": Audi uses both wordings for the same high-beam unit; the script says LEDs, matching
  Audi's press text. Autoblog's "43 LEDs" counts high + low beam, so not used. Segment counts vary by car and
  generation (description says so).
- Camera location (behind the windshield) is typical but not in the sources we read, so the narration says
  "a camera at the front".
- "The gap slides along with the car": follows from the system continuously masking the detected vehicle's
  section (Audi: masks the relevant sections when the camera detects vehicles; NHTSA: "actively modifies").
- "Became legal in 2022" = NHTSA's rule allowing ADB on new vehicles, effective Feb 22, 2022. Before that, US
  rules required separate upper/lower beam patterns, so ADB functionality could not be offered.
- No beam distances in metres are stated: the rule's SAE J3069 test points (30/60/120/155 m) are test distances,
  not reach figures.

## Misconceptions to avoid
- It doesn't "bend" or "redirect" light away from people: the slices aimed at them are simply dimmed/switched off.
- It is not auto high beam (which switches the whole high beam on/off); matrix/ADB keeps the rest on.
- The low beam stays on underneath; only the high-beam unit is segmented (Audi: "the high-beam unit").

## Simplifications made on screen
- One 25-slice fan drawn from the car's centre (real cars have two lamps whose patterns overlap).
- Slice angles, beam lengths, car speeds and the margin around each car are illustrative.
- Low beam drawn as a short asymmetric pool; no numbers.
