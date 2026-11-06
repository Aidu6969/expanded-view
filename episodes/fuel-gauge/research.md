# FUEL GAUGE — research notes

Every fact the narration states, with a source. Researched 2026-11-06.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | Inside the tank, a float rides on the fuel at the end of a long arm (float arm). | GM patent US7784342: "A float 20 is attached to an end of float arm 18 and is configured to buoyantly reside upon the upper surface of the fuel" https://patents.google.com/patent/US7784342 ; The News Wheel: "a float ... on a long, thin metal rod connected to a resistor" https://thenewswheel.com/how-your-car-measures-gas-and-why-it-lies-to-you/ |
| 2 | The arm drags a wiper across a strip of resistors; resistance changes with float position. | US7784342: carbon resistor card with contact pads "arranged in an arc"; a wiper on the float arm "wipes across the contact pads"; "the resistance ... varies in relation to float arm displacement". Chrysler patent US4838082: "a sliding electrical contact which wipes over a stationary resistive element" https://patents.google.com/patent/US4838082 ; Autoblog: "a lighter-than-gas float and a rheostat" https://www.autoblog.com/features/gas-gauge |
| 3 | The car turns that resistance into the needle position. | US5257300 (Ford): variable resistor "generates a liquid level signal" that is processed and sent to the fuel gauge https://patents.google.com/patent/US5257300 ; US4838082 drives an air-core magnetic fuel gauge from the sender voltage. |
| 4 | Fuel sloshes when you brake or turn; the gauge averages the signal so the needle moves slowly on purpose. | US5257300: "fuel level variations due to movement of the vehicle (known as 'fuel slosh') cause the sensor signal to include transient errors ... the actual fuel level can still be determined by obtaining the average of the sensor signal over a sufficiently long time period"; output slew limited to ~10-20 mV/s. US4838082: damper circuit so input changes appear at the output only "at some later time". |
| 5 | The gauge sits on full for a while, then moves faster toward empty. | Autoblog: "your gas gauge stays on full for quite a while before the needle even moves and then it moves faster and faster as it approaches empty". NPR: may stay on full "for a day or two" https://www.npr.org/transcripts/135064825 |
| 6 | In a full tank the float is pinned at the top, so the first gallons don't move it. | The News Wheel: "the float is either going to hit the top or just reach as far up as it can go. So, starting with a full tank, you need to go through a fair amount of gas before the float starts to move again". Autoblog: float "might be submerged for some amount of time" near full. |
| 7 | The rest is tuning: drivers told carmakers they like it; it reads full before the tank is full and stays there. | Autoblog (Ford engineer Phil Pierron): "[Customers] want it to stay on full for an amount of time"; "The engineers calibrate them to do that ... because you, the customer, have told them that's the way you like it"; called "full reserve". NPR (Pierron): "the gauge will get to full at something a little less than the rated capacity of the tank" and "stays on full for an amount of time that the customer feels comfortable with". |
| 8 | Ford aims for around 20 or 30 miles on full. | NPR (Pierron, Ford): "We usually try and target, you know, probably around 20 or 30 miles". |
| 9 | Empty isn't empty; there's no secret reserve tank; the real empty point isn't marked. | Autoblog: "there isn't technically a reserve tank, there's simply a real empty point that is not marked on the gauge". NPR (Pierron): "when he gets to empty, he knows he can drive still a little farther." |

## Misconceptions to avoid
- "There's a hidden reserve tank": no, it's unmarked fuel in the same tank (Autoblog).
- "The gauge is broken / cheap": the behaviour is deliberate calibration plus float limits.
- No specific gallons/miles left at E are stated: it varies by car and no source gives a general figure.
  The description warns not to make a habit of running it dry.
- Ohm ranges vary by maker (the GM patent example's numbers were only seen in a summary), so no ohm values or
  resistance direction are stated in the narration; the on-screen bar is illustrative.
- 20-30 miles is Ford's stated target (attributed to Ford), not an industry rule.

## Simplifications made on screen
- Tank shape, float arm length, stop angles and the gauge calibration curve are illustrative (labelled
  ILLUSTRATION · NOT TO SCALE); the curve is computed from the drawn tank profile + float stops + a tuned mapping.
- Slosh averaging shown as a simple moving average; real systems vary (RC integrators, digital filters).
- The low-fuel lamp is shown lit in the empty scene; its threshold is not stated.
- All sounds synthesized (fuel pour, slosh, car pulling away); Kokoro narrator (ElevenLabs paused by owner).
