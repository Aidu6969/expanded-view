# Turbo flutter: research

Sources read 2026-11-08. Every claim the narration makes is below.

## Facts stated in the video
1. **Flutter comes from the compressor, after a sudden throttle close.** "If the turbocharger's compressor wheel is spinning at high speed when the throttle is suddenly closed", flow "reduces beyond the surge line of the compressor". https://en.wikipedia.org/wiki/Blowoff_valve
2. **Turbo speed: around a hundred thousand RPM** (narration says "around"). HP Academy: "somewhere in the region of 80 to maybe 140000 RPM"; its test car reached "about 95000 RPM". https://www.hpacademy.com/previous-webinars/209-what-is-compressor-surge/
3. **Throttle snaps shut, air is trapped, pressure spikes, flow drops.** "This traps a whole lot of boosted air between the turbocharger and the throttle body" https://www.caradvice.com.au/587685/what-is-turbo-flutter-and-compressor-surge-is-it-bad/ ; "momentarily giving you a spike in intake pressure but with no airflow" https://www.carthrottle.com/post/engineering-explained-wastegates-blow-off-valves-and-turbo-flutter/
4. **Flow collapses and reverses back through the wheel, then the cycle repeats.** "leading to a collapse in flow and possibly even flow reversal"; "This rapid cycle of pressurisation and depressurisation repeats until the compressor has slowed sufficiently or the throttle is re-opened." (Wikipedia, above). The blades "grip" again and "This causes the characteristic fluttering sound of compressor surge." https://gfb.com.au/tech/tech-articles/11-the-truth-about-compressor-surge/
5. **Engineers call it compressor surge; left edge of the compressor map.** "Surge is the left hand boundary of the compressor map. Operation to the left of this line represents a region of flow instability." Garrett Turbo Tech 103: https://www.garrettmotion.com/wp-content/uploads/2019/10/GAM_Turbo-Tech-103_Expert-1.pdf . Sudden throttle close "immediately drives the operating point to the far left of the compressor map, right into surge." (same).
6. **The wheel does not reverse; only the air does.** "the turbo will never stop dead or reverse direction because of compressor surge." (GFB). HP Academy: "it does not stop", "it's also not going to end up spinning backwards."
7. **A little flutter probably won't kill a modern turbo.** "closed throttle flutter on modern turbochargers is unlikely to cause a noticeable drop in turbocharger lifespan." (CarAdvice). GFB: "in the majority of cases it will not cause significant turbo wear or damage." (GFB sells valves, so this is an against-interest statement.)
8. **Garrett's warning, thrust bearing.** "Continued operation within this region can lead to premature turbo failure due to heavy thrust loading." (Garrett). Wikipedia: "cyclic torque on the compressor and may lead to increased stresses on the bearings and compressor impeller." HP Academy: "quite a lot of force being placed on the thrust bearings".
9. **Blow-off valve: engine vacuum opens it at lift-off, the air escapes.** "the manifold goes into immediate vacuum. That vacuum signal then opens the blow-off valve." https://www.enginelabs.com/?p=6635 ; "A vacuum hose connected to the intake manifold downstream of the throttle provides a reference pressure for the blowoff valve." (Wikipedia). "A BOV functions to vent intake pressure to atmosphere" (Garrett). Bypass valves recirculate to the compressor inlet instead (Garrett, HP Academy).
10. **The "pssh" sound** comes from venting to atmosphere: Car Throttle describes it, and Garrett defines the venting. Recirculating valves are quieter.

## Unsure, and how it was resolved
- **Terminology:** CarAdvice calls closed-throttle flutter "reversion" and reserves "compressor surge" for open-throttle flutter. Garrett, Wikipedia and HP Academy all call the lift-off case surge. The video follows Garrett.
- **Wheel speed in surge:** sources differ (CarAdvice: drops rapidly; EngineLabs: "the compressor wheel speeds up in surge"). The video only says it never stops or reverses, which GFB and HP Academy state plainly. No claim about speeding up or slowing down.
- **Cycles per second:** none of the nine sources gives a figure. The video states none, and the on-screen cycle is labelled ANIMATION SLOWED.
- **Does flutter harm the turbo?** Sources disagree, so the line gives both: a little probably won't, sustained surge can (Garrett).
- **"A blow-off valve keeps the turbo spinning" / "flutter helps it re-spool":** contested. Not claimed.

## Model behind the animation
The flow, pressure and the dot on the map come from the Greitzer lumped-parameter surge model (duct inertia + plenum + cubic compressor characteristic + throttle), integrated numerically. It is a teaching model in non-dimensional units; the map has no numbers on it. Slowed so the cycle is readable.

## Misconceptions avoided
- "The wheel spins backwards" (it does not).
- "Flutter means more power" (no source supports that; Car Throttle: "no performance nor reliability benefit").
- Blow-off vs bypass: the video only shows venting to atmosphere, which is the pssh.

## Sources
- https://en.wikipedia.org/wiki/Blowoff_valve
- https://www.garrettmotion.com/wp-content/uploads/2019/10/GAM_Turbo-Tech-103_Expert-1.pdf
- https://www.hpacademy.com/previous-webinars/209-what-is-compressor-surge/
- https://gfb.com.au/tech/tech-articles/11-the-truth-about-compressor-surge/
- https://www.caradvice.com.au/587685/what-is-turbo-flutter-and-compressor-surge-is-it-bad/
- https://www.carthrottle.com/post/engineering-explained-wastegates-blow-off-valves-and-turbo-flutter/
- https://www.enginelabs.com/?p=6635
