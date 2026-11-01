# LOCKSTITCH (sewing machine) — research notes

Every fact the narration states, with a source. Researched 2026-11-01.

Note on this run: page fetching was limited. The FIRGELLI rotary-hook article was read in full (HTTP 200).
Wikipedia, HowStuffWorks and Explain That Stuff could not be fetched this run (fetch permission timed out), so
for the basic textbook facts (rows 1, 2, 3, 7) the Wikipedia articles are cited as the standard reference
without a fresh quote. Narration was kept to facts that are uncontroversial and that the FIRGELLI article
supports wherever it covers them. No numbers (speeds, dates) are stated in the video.

| # | Claim in the script | Source |
|---|---------------------|--------|
| 1 | A sewing machine makes a lockstitch from two threads: the upper (needle) thread and a lower thread from a bobbin underneath | FIRGELLI: "interlocking the needle and bobbin threads into a lockstitch"; "Bobbin and case: supply the lower thread." https://www.firgelliauto.com/blogs/mechanisms/sewing-machine-rotary-hook ; Wikipedia, Lockstitch https://en.wikipedia.org/wiki/Lockstitch |
| 2 | The two threads lock together inside the fabric | FIRGELLI: "the take-up mechanism then removes the slack so the needle thread and bobbin thread interlock within the material." |
| 3 | A machine needle's eye is at the point (it never passes all the way through, unlike hand sewing) | Wikipedia, Sewing machine (eye-pointed needle, needle reciprocates and is not passed through the cloth) https://en.wikipedia.org/wiki/Sewing_machine ; consistent with FIRGELLI (needle loop formed as the needle rises, needle stays attached to the needle bar) |
| 4 | The needle carries the top thread down through the fabric; as it starts to rise, the thread forms a small loop | FIRGELLI: "As the needle starts rising, its thread forms a loop beside the needle scarf." |
| 5 | The hook's point catches that loop and carries it around the bobbin case | FIRGELLI: "The hook point enters that loop and carries it around the bobbin case." / "A rotary hook catches a loop of needle thread and carries it around the bobbin case." |
| 6 | The bobbin case is held still while the hook turns around it | FIRGELLI: "The bobbin case is restrained from following the hook, while the bobbin inside it supplies thread." (drawn with a stop tab; narration does not state it) |
| 7 | The take-up lever pulls the slack back up, closing the loop so the threads lock inside the fabric | FIRGELLI: "Needle and take-up: create the loop and draw the completed stitch tight." Lever name: Wikipedia, Sewing machine |
| 8 | Feed dogs move the cloth forward one stitch between stitches | Wikipedia, Sewing machine (feed dogs under the presser foot advance the fabric) https://en.wikipedia.org/wiki/Sewing_machine |
| 9 | The (rotary) hook turns twice for every stitch | FIRGELLI: "The illustrated drive turns the hook twice per needle cycle." / "fixed 2:1 hook-to-needle ratio". True for full rotary hooks like the one drawn; oscillating shuttles differ, so the description says "on a full rotary hook like the one shown". |

## Unsure items and how they were resolved
- Why the loop forms (friction against the cloth as the needle rises) is commonly explained but not in the source
  read this run -> narration says only that the thread "puffs out into a small loop".
- "Knot": a lockstitch is an interlock, not a tied knot. Narration never says knot; the YouTube title says
  "the knot you never see" as a figure of speech; the description says the threads interlock.
- Hook direction / exact timing differ between machines. Model: hook point meets the needle just after the
  needle's lowest point; two hook turns per stitch; second turn idle; feed only while the needle is above the
  cloth (checked by scene.check_physics()).
- Speeds (stitches per minute) were not stated: only one industrial model figure was found (JUKI DDL-8700,
  5,500 spm, quoted by FIRGELLI) and household speeds were not sourced.
- Real feed dogs sit either side of the needle and move with an elliptical motion; drawn as one toothed block
  beside the needle hole moving rise -> forward -> drop -> back (simplified).
- Thread colours: top thread cyan, bobbin thread red, purely for clarity.
