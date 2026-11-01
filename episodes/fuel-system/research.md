# FUEL SYSTEM — research notes

Every fact the narration states, with a source. Sources read 2026-11-01.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | In fuel-injected cars the electric fuel pump sits inside the fuel tank | Wikipedia, Fuel pump: "In fuel-injected petrol engines, an electric fuel pump is typically located inside the fuel tank." https://en.wikipedia.org/wiki/Fuel_pump |
| 2 | Being submerged in fuel keeps the pump cool | Wikipedia, Fuel pump: "By submerging the pump in fuel at the bottom of the tank, the pump is cooled by the surrounding fuel" https://en.wikipedia.org/wiki/Fuel_pump |
| 3 | The line runs through a filter (in-line filter between tank and engine; in some returnless systems the filter is part of the in-tank module) | aa1car, Returnless EFI: "an in-line filter is positioned somewhere between the fuel tank and engine" https://www.aa1car.com/library/returnless_efi.htm |
| 4 | A fuel rail feeds the injectors (one pressurised rail, injection valves open on an electric signal); multi-point = one injector per cylinder | aa1car, Fuel injection basics ("the fuel rail that supplies the injectors"; MPI sprays into each intake port) https://www.aa1car.com/library/fuel_injection_basics.htm ; Wikipedia, Manifold injection https://en.wikipedia.org/wiki/Manifold_injection |
| 5 | Port-injection pressure 40 to 60 psi | Wikipedia, Fuel pump: "typically 40–60 psi (3–4 bar)"; aa1car: "between 40 and 55 psi" |
| 6 | A regulator holds the pressure steady (returnless: in the in-tank pump assembly, as drawn) | aa1car, Fuel injection basics: "On returnless EFI systems, the regulator is part of the fuel pump assembly inside the fuel tank."; Returnless EFI: regulator "operates at a constant pressure" |
| 7 | The computer energises the injector; an electromagnet (solenoid) pulls the valve open | aa1car, Fuel injection basics: "A fuel injector is nothing more than a spring-loaded solenoid pintle valve. When energized by the computer, the solenoid pulls the valve open." |
| 8 | Fuel goes in as a fine mist into the intake port, near / through the intake valve | aa1car (sprays "into the cylinder head intake port"); Wikipedia, Manifold injection (injectors "installed very close to the intake valve(s)", fuel forms "a fine fuel vapour") |
| 9 | Longer pulse = more fuel | aa1car, Fuel injection basics: "The longer the pulse width, the greater the volume of fuel delivered." |
| 10 | Oxygen sensor in the exhaust reports rich/lean; the computer corrects the pulse width | aa1car, Fuel injection basics: "The primary sensor for fuel mixture control is the Oxygen sensor."; lean signal -> computer "richening up the fuel mixture (increasing the pulse width of the injectors)" |
| 11 | Direct injection: injectors spray straight into the cylinder; an engine-mounted second (high-pressure) pump; far higher pressure | aa1car (spray "directly into the combustion chamber", "much higher operating pressures"); Wikipedia, Fuel pump ("high-pressure mechanical pumps mounted on the engine"; DI pumps operate "at a much higher pressure") |
| 12 | Tank fumes are trapped in a charcoal canister and later burned by the engine | aa1car, Returnless EFI: "Fuel vapors pass through a vent hose to a charcoal-filled canister which temporarily traps and stores the vapors. Later, the vapors are purged ... and routed into the engine." |

## Unsure items and how they were resolved
- Low-fuel driving overheating the pump: widely repeated but not found in a primary source read this run -> NOT stated.
- 14.7:1 ratio and injector milliseconds: not stated by the sources read -> left out of the narration. The on-screen
  pulse graph is schematic (no numbers).
- "Spray into each cylinder" (topic angle) is only true for direct injection; port injection sprays into the intake
  port. Narration says "into the air rushing toward the intake valve" for port injection and treats direct injection
  separately.
- Regulator location differs (return systems: on the rail; returnless: in the tank module). The narration says only
  "a regulator holds it steady"; the drawing shows the returnless layout.
- High-pressure DI pump drawn driven by a cam lobe (common layout); narration only says "a second pump on the engine".

## Misconceptions to avoid
- The pump does not suck fuel from the engine end; it pushes from the tank.
- Port injectors do not spray into the combustion chamber.

## Simplifications made on screen
- Engine drawn above the tank (exploded schematic), not to scale; one cylinder section for the close-up.
- Animation slowed; injection pulses and engine cycle not at real speed.
