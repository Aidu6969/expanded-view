# TPMS (tire pressure monitoring): research

Every fact the narration states, with a source. Checked 2026-11-12.

## Facts used in the video

1. **A tire can be a quarter low and the US requires a warning; new light vehicles since (September) 2007; within
   20 minutes.** FMVSS No. 138 (49 CFR 571.138) S4.2(a): the telltale must illuminate "not more than 20 minutes after"
   a tire reaches "the pressure 25 percent below the vehicle manufacturer's recommended cold inflation pressure, or the
   pressure specified in the 3rd column of Table 1 ... whichever is higher." S2: passenger cars, MPVs, trucks and buses
   with GVWR 10,000 lb or less (except dual-wheel axles). S7.3: "all vehicles manufactured on or after September 1,
   2007 must comply" (phase-in from Oct 2005: 20 %, then 70 %). Narration: "in the US, new cars since two thousand
   seven must warn you within twenty minutes" (heavy trucks excluded; "new cars" is the plain-language version).
   - https://www.law.cornell.edu/cfr/text/49/571.138
   - Background (TREAD Act after the Ford Explorer / Firestone tire failures required this rule):
     https://theautopian.com/how-indirect-tire-pressure-monitoring-systems-work-and-why-we-should-celebrate-their-return
   "Still look fine": a quarter low is often not obvious by eye on a modern radial; stated as the reason a warning is
   needed. Kept soft ("can ... still look fine").
2. **Two kinds: direct and indirect.** Standard Brand: direct systems use a sensor in each wheel; indirect systems
   "rely on the ABS Brake system to monitor and compare wheel speeds."
   - https://www.standardbrand.com/en/training/standard-insights/a-closer-look-tire-pressure-monitoring-systems-tpms-operation
3. **Direct: the sensor sits on the back (base) of the valve stem inside the wheel, with its own battery.**
   Brake & Front End: "The radio transmitter is actually the valve stem's base"; "The typical modern direct TPM sensor
   has a 10-year lithium battery that is not replaceable." Standard Brand: "4 or 5 sensors (one in each wheel, and
   sometimes the spare)." (Some older designs strap to the rim with a band; the valve-stem type is the common one.)
   - https://www.brakeandfrontend.com/tech-tip-understanding-tire-pressure-monitoring-systems/
   - https://www.standardbrand.com/en/training/standard-insights/a-closer-look-tire-pressure-monitoring-systems-tpms-operation
4. **It measures pressure (and temperature) and radios it to the car every 30 to 60 seconds while driving.**
   Brake & Front End: sensors "only send a signal to the receiver about every 30 to 60 seconds at speeds of 15+ to 20+
   mph. Then, when sitting still, they transmit a pressure reading about once each hour." Standard Brand lists the
   transmitted data: pressure, temperature, identification, accelerometer. On screen the packet shows PSI + an ID.
   Radio frequency (315 / 433 MHz) NOT stated: regional assignment not verified.
5. **"Drop a quarter low, and the light comes on."** = FMVSS 138 25 % threshold (fact 1). On screen: 35 PSI placard
   example, line at 26 PSI (35 x 0.75 = 26.25). 35 PSI is an illustrative placard value, labelled EXAMPLE.
6. **Indirect: no sensor in the tire; it uses the ABS wheel-speed sensors.** Standard Brand (above). Brake & Front
   End describes the indirect system's "calibration and detection" modes using wheel-speed data.
7. **A low tire squashes and is a little smaller (smaller rolling radius), so it spins faster to keep up.**
   Standard Brand: a tire losing air "becomes smaller in diameter, which causes it to rotate faster than the others."
   Autopian article and Nira/Audi coverage (Modern Tire Dealer) describe the same rolling-radius method.
   The real difference is small (a fraction of a percent); the on-screen turn counters exaggerate it and say so.
   - https://www.standardbrand.com/en/training/standard-insights/a-closer-look-tire-pressure-monitoring-systems-tpms-operation
   - https://theautopian.com/how-indirect-tire-pressure-monitoring-systems-work-and-why-we-should-celebrate-their-return
8. **If all four leak together, a basic system has nothing to compare.** Standard Brand: indirect "can detect
   under-inflation in up to three tires simultaneously but not all four"; "if all four tires lose the same amount of air
   the relative change will be zero." Newer systems (Nira Dynamics TPI, Infineon MRFA) add tire-vibration/resonance
   analysis and CAN detect all four low; hence "a basic system" in the narration and the note in the description.
9. **You reset it after new tires.** Brake & Front End: after a tire rotation or replacement, "the 'reset' button must
   be pressed." Autopian quoting Nira TPI: "The driver should reset the system and re-initialize calibration" after
   tire or wheel changes.
   - https://www.brakeandfrontend.com/tech-tip-understanding-tire-pressure-monitoring-systems/

## Unsure items and how they were resolved
- Lamp symbol shape: FMVSS 138 points to FMVSS 101 Table 1; not verified in detail, so the script says "that little
  tire light" and the drawn lamp is a generic tire-section icon with "!" (our own drawing, amber).
- Temperature rule of thumb (1 psi per 10 F): not sourced in this run, not used.
- 315 vs 433 MHz by region: not verified, not used.
- Brake & Front End notes some indirect systems need ~12 psi drop: not stated; narration says only "a little smaller"
  and "spinning faster".

## Misconceptions to avoid
- "Every car has a sensor in each tire": false; indirect systems have none (the hook).
- "The light means a flat": it means 25 % low (or the Table 1 minimum), not necessarily flat.
- "Indirect can never see four low tires": basic ones can't; newer vibration-analysis ones can. Narration says
  "a basic system".

## Simplifications made on screen
- Wheel speed difference exaggerated (labelled), rotation slowed.
- Radio packets drawn as arcs and a pill; receiver location generic.
- Sensor cutaway simplified (battery, board, pressure port).
