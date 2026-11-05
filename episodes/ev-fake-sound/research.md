# Why electric cars make fake sounds (AVAS / FMVSS 141): research

Researched 2026-11-05. Every claim the narration makes, with its source.

| # | Claim in the video | Source |
|---|---|---|
| 1 | Electric cars are very quiet at low speed; at higher speed, tyre and wind noise dominate | FMVSS 141 final rule (NHTSA, Dec 2016): "At higher speeds, in contrast, tire and wind noise are the primary contributors to a vehicle's noise output." https://govinfo.gov/content/pkg/FR-2016-12-14/pdf/2016-28804.pdf |
| 2 | Hybrids/EVs were about 50 % more likely than combustion cars to hit a pedestrian in low-speed manoeuvres (turning, slowing/stopping, backing up, entering/leaving parking, starting in traffic) | NHTSA Research Note DOT HS 812 371 (Feb 2017): "approximately 50 percent higher likelihood of hitting pedestrians than ICE vehicle in low-speed maneuvers (OR=1.52, RR=1.51)". All speeds: ~20 % higher (OR 1.20). https://crashstats.nhtsa.dot.gov/Api/Public/Publication/812371 |
| 3 | So it's the law (US) | FMVSS 141 requires hybrid and electric vehicles to emit minimum sound "while in reverse and while the vehicle is in forward motion up to 30 km/h"; required for all HVs/EVs from September 1, 2020. https://www.govinfo.gov/content/pkg/FR-2018-02-26/html/2018-03721.htm |
| 4 | EU too (on-screen) | Reg. (EU) 540/2014 Annex VIII: AVAS on new vehicle types from 1 July 2019, all new vehicles from 1 July 2021; sounds "from start up to approximately 20 km/h and during reversing". https://legislation.gov.uk/eur/2014/540/annex/VIII/2017-09-22 ; https://paultan.org/2019/07/02/all-new-evs-in-europe-must-now-add-fake-engine-noise/ |
| 5 | The sound comes from a speaker, usually in the front bumper | Siemens AVAS white paper (2020): "most vehicles today are equipped with one speaker on the front bumper and optionally one in the back." https://www.plm.automation.siemens.com/media/global/en/SiemensSW-Acoustic-vehicle-alerting-system_WhitePaper_tcm27-76714.pdf |
| 6 | The faster you go, the louder it gets | FMVSS 141: "requiring vehicle-emitted sound to increase in sound pressure level by a specified amount as the vehicle's speed increases" (2016 rule). EU: sound level or characteristics vary "in synchronisation with vehicle speed" (Annex VIII III.3(a)). |
| 7 | Above about 19 mph (30 km/h) it goes quiet, because tyres and wind make the car audible on its own | 30 km/h = 18.6 mph (2018 response). Crossover speed = "the speed at which tire noise, wind resistance, or other factors make an EV or HV detectable by pedestrians without the aid of an alert sound" (statutory definition quoted in the 2016 rule). EU limit ~20 km/h (no rationale stated; not claimed in narration, shown on screen only as the EU number). |
| 8 | The sound is for the people outside (pedestrians), not the driver | Purpose of FMVSS 141 / PSEA: detectability by pedestrians (2016 rule, as above); AVAS = acoustic vehicle alerting system for pedestrians (Annex VIII). |
| 9 | Hyundai Ioniq 5 N plays engine-like sounds through ten speakers (8 inside, 2 outside) | Jalopnik (2023): "the N Active Sound+ system incorporates 10 speakers, eight inside the car and two on the outside", with "ICE-like engine and exhaust sounds". https://jalopnik.com/hyundai-really-wants-its-ioniq-5-n-ev-to-feel-like-a-ra-1850628672 |
| 10 | It briefly cuts power to fake a gear shift (N e-shift) | Jalopnik: simulates gearshifts "by controlling the torque of the Ioniq 5 N's motors" / "momentarily disengaging the motors". Edmunds (2026): "briefly interrupting power delivery during gear changes." https://www.edmunds.com/car-news/hyundai-ev-fake-shift-expanding-to-more-cars.html |

## Unsure / resolved
- Pitch: the US final rule dropped the proposed pitch-shifting requirement ("not required in the final rule"); EU/UN R138 has a frequency-shift test per Siemens, unverified in R138 text. The narration only says "louder", which both rules support. The animation's sound wave grows in amplitude, not pitch.
- "2x more likely" figures seen online are NOT supported; the NHTSA numbers are OR 1.52 (low-speed manoeuvres) and ~1.2 overall. The study's HE group is mostly hybrids (47 hybrid, 3 electric in the fatality appendix), so the narration says "hybrids and electric cars".
- US also requires a sound when stationary in gear (not in park). Not stated in the video.
- Speaker placement varies by maker; narration says "a speaker in the front bumper" as the typical case (Siemens). The animation shows one speaker behind the front bumper.
- No real car recordings: the AVAS hum and the "engine" sound in the twist are synthesized by us; the car drawn is a generic EV, no badges. The Ioniq 5 N is named only, not drawn.

## Misconceptions avoided
- Not "EVs are dangerous": the overall effect NHTSA found is small; the claim is limited to low-speed manoeuvres.
- The warning sound is not mainly for the driver (that's the separate performance-sound feature).
