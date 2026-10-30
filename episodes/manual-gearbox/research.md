# Manual gearbox (constant mesh + synchromesh) — research notes

Sources:
- [E] edumech, Synchromesh unit: https://www.edumech.co.uk/learn/transmission-and-driveline/synchromesh-unit
- [H] Hagerty, How a manual transmission works: https://www.hagerty.com/media/maintenance-and-tech/how-a-manual-transmission-works/
- [C] Curbside Classic, 1929 Cadillac/LaSalle Synchro-Mesh (reprints MoToR, 1928): https://www.curbsideclassic.com/blog/tech/1929-cadillac-lasalle-synchro-mesh-transmission-shifting-is-made-simple-and-clashing-of-gears-is-ended
- [U] Unique Cars and Parts, How it works: synchromesh: https://uniquecarsandparts.com.au/how_it_works_synchromesh

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | Gears don't slide in and out; they stay meshed in pairs | [E] misconceptions: "Gears are permanently meshed; synchromesh locks gears to the shaft." [C] "Mainshaft second gear is in constant mesh with its mate on the countershaft." |
| 2 | Output-shaft gears aren't attached; they spin freely until selected | [E] "Main shaft gear - Free to rotate on the shaft until locked by the synchromesh unit." [C] "when not in use rotates freely on a bronze bushing." [H] "Sliding collars lock certain gears in place while allowing others to rotate freely." |
| 3 | Engine turns the countershaft and every gear on it | [C] countershaft driven from the clutch/main drive gear; countershaft gears are one cluster (standard layout) |
| 4 | Each pair is a different ratio; small driving big trades speed for torque | basic gear-ratio law ([H] explains ratios); stated qualitatively only, no numbers |
| 5 | In neutral nothing is locked, so no gear drives the output | [E] gears free "until locked"; [C] in neutral the gears "rotate freely" |
| 6 | Collar is locked (splined) to the output shaft; a fork slides it | [C] "the sliding coupling which is splined to the mainshaft is moved ... through the usual shifter shaft and shifter fork"; [E] inner hub "Splined to the main shaft", selector fork "move[s] the synchromesh unit" |
| 7 | Clutch pressed while shifting (engine disconnected) | [U] driver "having disengaged one gear, had to release the clutch pedal" (double declutch description); [C] "plate clutch disengaged" |
| 8 | Unequal speeds make the teeth clash / grind | [C] title: "clashing of gears is ended"; [E] baulk ring prevents engagement while speeds differ |
| 9 | A cone-shaped synchro ring rubs on the gear; friction brings it to the same speed; only then the teeth engage and lock | [U] "engagement of the dogs is preceded by contact between two friction surfaces, normally an internal and an external cone ... tends to synchronize the speeds"; [E] steps 2–5: baulk ring pressed on the gear's cone, prevents the sleeve engaging until speeds match, then the sleeve engages the dog teeth |
| 10 | Old gearboxes had no synchros; drivers double-clutched to match speeds | [U] "The point of double declutching is to synchronize the speed of the input shaft"; [C] synchromesh introduced by Cadillac/LaSalle in 1928 (1929 models). No year is stated in the video. |

## Unsure items and how they were resolved
- Wikipedia could not be fetched this run; facts were taken from the four sources above.
- Synchro ring material (often brass) is not stated in narration; the ring is drawn brass-coloured only.
- Reverse gear (idler) left out entirely: not sourced this run and not needed for the explanation.
- First-gear pull-away scenario: with the clutch pressed the input side is free, so the synchro's friction slows the free gear (and the input side) to the collar's speed (car standing = zero). This is the standard synchro function [E][U]; the animation shows exactly that.

## Misconceptions to avoid
- "The shifter slides gears into mesh" (sliding-mesh boxes are obsolete for forward gears in cars) [E].
- "Synchromesh changes the ratio" — the ratio comes from the gear pair; the synchro only matches speeds [E].

## Simplifications made on screen
- Three forward gears, one collar with the synchro shown on the first-gear side only; real boxes have 5–6 gears, reverse,
  and a synchro ring on each side of each collar.
- Animation slowed (labelled). Tooth counts are real meshes (module 6, equal centre distance) but not a specific car's ratios.
