# Keyless entry (passive keyless entry / PEPS) — research

Searched 2026-11-07. Every fact the video states, with its source.

## Facts used
1. **Two radios: a short-range low-frequency (LF) link from the car to the key and a long-range UHF link from the
   key back to the car.** The car's control unit sends on LF and "receives a response on a UHF frequency (433 MHz
   or 315 MHz)". LF is 125 kHz and is "used to clearly locate the ID transmitter".
   https://www.hella.com/techworld/us/technical/car-electronics-and-electrics/keyless-go/
   PKES keys combine an LF tag with "short range communication (within 1-2 m in active ... mode)" and "a
   fully-fledged UHF transceiver for longer range communication (within 10 to 100 m)"; LF typically 120-135 kHz.
   https://www.s3.eurecom.fr/docs/ndss11_francillon.pdf (Francillon, Danev, Capkun, NDSS 2011)
   -> narration: "a weak, low frequency signal, around a hundred and twenty five kilohertz, that only reaches a
   meter or two"; the key "answers on its long range radio".
2. **The fob button works from far away (up to ~100 m); passive functions only within ~2 m.** HELLA: active
   locking "from distances of up to 100 m"; passive functions only "in the immediate vicinity of the vehicle
   (approx. 2 m)". -> narration: "the button on your key works from about a hundred meters away".
3. **Antenna locations: door handles, rear bumper, cabin, trunk.** HELLA: "The front door handles contain the
   receiving antennas"; antennas "built into the rear bumper", plus interior, trunk and parcel-shelf antennas.
4. **Trigger: grabbing the handle.** HELLA: passive unlock is "performed by gripping the door handle"; the sensor
   then tries to find an authorised ID transmitter; opening takes ~50-60 ms.
5. **Challenge-response cryptography.** Microchip PEPS reference design: the fob "can wake up on this LF field";
   it "encrypts the received challenge data (using AES) and returns the correct cipher response, together with
   the positioning information" over UHF.
   https://onlinedocs.microchip.com/oxy/GUID-BAA8542B-0F40-4D9C-830C-561D4001CB62-en-US-2/GUID-B911342E-D68F-4E22-BF14-9EF0CFABB035.html
   -> narration: "scrambles it with a secret code only your car knows" (plain-English for encrypting the
   challenge with a shared key).
6. **Inside vs outside = signal strength measured by the key.** Microchip: the fob "measures the strength of the
   magnetic field, which is used to determine the position of the fob relative to the vehicle (outside or
   inside)". Example tool uses an RSSI in/out threshold.
   https://onlinedocs.microchip.com/oxy/GUID-BAA8542B-0F40-4D9C-830C-561D4001CB62-en-US-2/GUID-9583A4D4-AF05-44E0-8A47-9FB4E2B8C8B2.html
   HELLA: a 3D LF antenna in the key measures "the received field strengths in all three spatial directions",
   which "enables the system to differentiate precisely between the interior and exterior of the vehicle".
7. **Relay attack: two devices stretch the short link.** Motor1: "Relay theft commonly involves two people working
   together. One operates near the vehicle while another gets close enough to the key fob." ... "the car
   mistakenly recognizes it as present." https://www.motor1.com/news/813405/how-keyless-car-theft-works/
   Francillon et al.: "extensive evaluation on 10 car models from 8 manufacturers"; the attack works while "the
   true distance between the key and car remains large (tested up to 50 meters, non line-of-sight)".
   https://www.s3.eurecom.fr/docs/ndss11_francillon.pdf ; https://www.ndss-symposium.org/ndss2011/relay-attacks-on-passive-keyless-entry-and-start-systems-in-modern-cars/
8. **Countermeasure 1: sleeping fobs.** Motor1: "Some systems put a stationary fob into a low-power or sleep
   state, helping reduce the opportunity for certain relay attacks." (Ford markets a "motion sensing key fob".)
9. **Countermeasure 2: ultra-wideband time of flight.** CSEM: "UWB is based on time-of-flight (TOF)
   measurements", timing "UWB radio pulses to travel from a vehicle to its key at the speed of light", which
   makes relaying "virtually impossible". Bosch describes UWB ToF + encryption confirming "physical proximity".
   https://www.csem.ch/en/annual-report/2022/3db-access-ultra-wideband-technology-improves-vehicle-security/
   https://bosch-mobility.com/en/solutions/software-and-services/perfectly-keyless

## Unsure / resolved
- Whether the key or the car makes the inside/outside call: Microchip says the key measures field strength and
  returns positioning info; the car acts on it. Narration: "Your key measures how strong each antenna sounds,
  and reports back" — accurate to both.
- Exact LF frequency varies (120-135 kHz); we say "around a hundred and twenty five kilohertz".
- Exact ranges vary by car; we say "a meter or two" and "about a hundred meters".
- "A relay gives itself away": inference from time-of-flight (a relay adds path length and processing delay);
  CSEM/Bosch say ToF makes relay attacks nearly impossible. Kept qualitative, no numbers.
- Study date: NDSS, February 2011; 9 of the 10 were cars, 1 an aftermarket system. We say "ten car models" as the
  paper's abstract does.

## Misconceptions avoided
- The car does not "see" or GPS-locate the key; it is all short-range magnetic field strength.
- Keyless does not mean the car is always shouting: the search is triggered (handle touch / start button).
- Relay attackers do not crack the cryptography; they just forward the genuine exchange.
