# ABS (anti-lock brakes): research

Every fact the narration states, with a source. Checked 2026-11-10.

## Facts used in the video

1. **Hard braking can lock a wheel: the wheel stops turning while the car keeps moving (100% slip).**
   Slip ratio = (vehicle speed - wheel speed) / vehicle speed; a free-rolling tire is 0%, a fully locked tire 100%.
   - https://open-exam-prep.com/study-guides/ase-a5/electronic-brake-control-systems/abs-fundamentals-control-cycles
2. **A tire that is still turning while slipping a little grips harder than a locked, sliding tire.**
   "A tire that is just on the verge of slipping (10 to 20% slippage) produces more friction with respect to the road
   than one which is locked and skidding (100% slippage)." (aa1car). The ASE guide gives 15-20%. On screen the peak is
   shaded as a band "~10-20% SLIP", not a single number.
   - https://www.aa1car.com/library/abs1.htm
   - https://open-exam-prep.com/study-guides/ase-a5/electronic-brake-control-systems/abs-fundamentals-control-cycles
3. **A sliding tire has almost no sideways grip, so steering does nothing.**
   "Once a tire begins sliding, its lateral (side-to-side) grip drops to near zero, preventing the driver from steering
   around obstacles regardless of how far the steering wheel is turned." aa1car: once it skids it has "about as much
   directional stability as a hockey puck on ice."
   - https://open-exam-prep.com/study-guides/ase-a5/electronic-brake-control-systems/abs-fundamentals-control-cycles
   - https://www.aa1car.com/library/abs1.htm
4. **Each wheel has a toothed ring and a sensor that counts the teeth; the computer counts pulses.**
   "The wheel speed sensors (WSS) consist of a magnetic pickup and a toothed sensor ring (sometimes called a 'tone'
   ring)"; the module "counts pulses to monitor changes in wheel speed."
   - https://www.aa1car.com/library/abs1.htm
5. **The computer watches the wheels; a wheel slowing much faster than the others is about to lock.**
   "If one wheel starts to slow at a faster rate than the others, or at a faster rate than that which is programmed
   into the antilock control module, it indicates the wheel is starting to slip and is in danger of ... locking up."
   (Narration says "faster than the car" = faster than the vehicle can decelerate, which is the same test.)
   - https://www.aa1car.com/library/abs1.htm
6. **One valve closes to hold the pressure, another opens to let some out, then a pump pushes it back.**
   Solenoid valves "hold, release and reapply" pressure (aa1car). ASE guide: normally-open isolation (inlet) valve
   closes = hold; normally-closed dump (outlet) valve opens and vents fluid to a low-pressure accumulator = release;
   the electric return pump moves fluid from the accumulator back into the high-pressure circuit = reapply.
   - https://www.aa1car.com/library/abs1.htm
   - https://open-exam-prep.com/study-guides/ase-a5/electronic-brake-control-systems/abs-fundamentals-control-cycles
7. **It cycles over a dozen times a second.** aa1car: "up to dozens of times per second depending on the system";
   ASE guide: "15 to 20 times per second". Narration: "over a dozen times a second" (true for both). Animation is
   slowed and labelled.
8. **The pedal pulsates / buzzes when ABS works, and that is normal.** "This produces a pulsating effect, which can
   usually be felt in the brake pedal during hard braking. The driver may also hear a buzzing or chattering noise"
   (aa1car). Owner's manuals say the same.
   - https://www.aa1car.com/library/abs1.htm
   - https://techinfo.honda.com/rjanisis/pubs/OM/AH/AT502525IOM/enu/details/131272047-12058.html
9. **With ABS: don't pump, press hard and hold, steer.** AARP driver-safety guide: "Stay on the brakes. Do not pump
   the brakes!", firmly depress and keep pressure, steer where you want to go. Honda owner's manuals give the same
   advice (press firmly, do not pump).
   - https://www.aarp.org/auto/driver-safety/antilock-brakes-know-how-they-work/
   - https://techinfo.honda.com/rjanisis/pubs/OM/AH/AT502525IOM/enu/details/131272047-12058.html
10. **Description only:** first production car with electronic four-wheel multi-channel ABS: Mercedes-Benz W116
    S-Class with Bosch, presented August 1978, as an option.
    - https://autobuzz.my/2018/12/06/throwback-thursday-40-years-since-the-introduction-of-abs-in-the-w116-mercedes-benz-s-class/

## Hook / myth
"Everyone was taught: in a skid, pump the brakes." That was the advice for cars without ABS (pumping keeps the wheels
from staying locked so you can steer). The video's answer: a rolling tire grips more and can steer; ABS does the
pumping per wheel, much faster; so with ABS you do NOT pump. The narration never says pumping is wrong for old cars.

## Unsure / resolved
- Peak-grip slip: 10-20% (aa1car) vs 15-20% (ASE prep). Shown as a band, no number spoken.
- Cycle rate: "dozens" vs 15-20 Hz -> "over a dozen times a second".
- On dry pavement locked vs rolling friction differ less (HyperPhysics:
  https://hyperphysics.gsu.edu/hbase/Mechanics/frictire.html); the video says "on a wet road" for the lock-up and
  makes the steering point the main payoff. ABS can lengthen stops on gravel/snow: not claimed either way.
- Hydraulic diagram is one channel, simplified (real units have a valve pair per channel and a shared pump).

## Misconceptions avoided
- ABS does not "make you stop shorter" in every case: not claimed.
- The wheel speed sensor does not measure the car's speed directly; the computer compares wheels.
