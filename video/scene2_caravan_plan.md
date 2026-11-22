# Scene 2 — The Caravan Arrives (≤25s)

Picks up from the opening's "awaiting the caravan." Tender & hopeful tone.
Same world as the opening: Tang dynasty Silk Road desert, rammed-earth watchtower,
golden hour, 16:9. Her face stays hooded except one brief lit glimpse (Shot D).

## Shot list

| # | Time | Beat | Camera |
|---|------|------|--------|
| A | 0–5s | Small caravan emerges from the haze toward the tower/army | Slow wide, low angle, dust |
| B | 5–10s | Hooded girl dismounts, greets the general, bows | Medium / over-shoulder |
| C | 10–16s | General presses two marked pebbles into her palm | Macro insert, shallow focus |
| D | 16–19s | Light catches her face inside the hood (one clear look) | Slow push-in |
| E | 19–25s | Caravan turns and departs across the dunes into the sun | Rising aerial pull-back |

---

## Reusable blocks — paste these into EVERY shot unchanged

**WORLD:** Tang dynasty Silk Road desert at golden hour, rolling sand dunes, a
weathered rammed-earth watchtower, snow-capped mountains on the far horizon,
low warm sun, blowing dust and fine sand in the air. Warm amber and soft teal
palette, cinematic IMAX 70mm look, shallow depth of field, fine film grain,
vertical… no — 16:9 widescreen.

**GIRL (character):** a young girl about 7 years old, slight build, delicate
features, large dark eyes, fair skin (match the provided reference photos
exactly). She wears a hooded desert travel cloak of sand-ochre wool over a pale
under-robe, a wrapped scarf, practical for a long desert trek; a small pale-blue
ribbon detail. Her face is shadowed inside the hood (except where noted).

**GENERAL (character):** a battle-worn Tang general in lamellar armor, deep-red
cape, plumed helmet, weathered scarred hands (match the opening's general).

**PEBBLES:** two small flat river pebbles, pale grey-green, each bearing a faint
hand-carved spiral symbol.

**NEGATIVE / avoid:** modern objects, text or logos, watches, distorted or
inconsistent faces, extra fingers, warped limbs.

---

## Per-shot prompts

### Shot A — Caravan arrives (~5s)
> [WORLD] A small Silk Road caravan — two or three camels laden with bundles,
> a couple of hooded travelers on foot, [GIRL] riding the lead camel — emerges
> from the golden heat-haze and blowing dust, approaching the watchtower where
> armored soldiers and dark-red banners wait. Slow wide shot drifting forward
> and slightly down, warm low-sun flare, drifting dust. Tender, hopeful, awe.
> Smooth steady motion. [NEGATIVE]

### Shot B — Greeting (~5s)
> [WORLD] [GIRL] dismounts and steps toward [GENERAL]. They stand facing each
> other in warm low light; she bows her head respectfully, he inclines his head
> in return. Gentle over-the-shoulder framing, shallow depth of field, dust
> motes floating in the sunbeams. Her face shadowed inside the hood. Warm,
> intimate, calm. [NEGATIVE]

### Shot C — The pebbles (~6s)  ← the "plant" for later
> [WORLD] Extreme macro close-up: [GENERAL]'s weathered scarred hand opens and
> gently presses [PEBBLES] into the girl's small open palm; her small fingers
> slowly close around them. Shallow focus, warm backlight, floating dust.
> Tender, quiet, meaningful. Very slow, delicate motion. [NEGATIVE]

### Shot D — Face glimpse (~3s)  ← generate the STILL first, then animate
> **Keyframe still (make this image first, approve the face, then animate it):**
> Photoreal portrait, [GIRL]'s face framed inside a sand-colored travel hood,
> warm golden-hour side light falling across her face, soft shadow, a quiet
> brave expression, large dark eyes. Match the reference face exactly. 16:9.
>
> **Then animate:** slow push-in; she lifts her head and the shaft of golden
> light crosses her face for a moment, then the hood's shadow returns. Minimal,
> gentle motion. [NEGATIVE]

### Shot E — Departure (~6s)
> [WORLD] [GIRL], hood up again, rides the lead camel as the small caravan turns
> and sets off across the vast rolling dunes toward the low sun; long shadows and
> a trail of dust behind them; the watchtower and army small in the distance.
> Rising aerial pull-back, epic but warm and hopeful. Smooth continuous motion.
> [NEGATIVE]

---

## Efficiency tips
- **Chain the clips:** use the LAST frame of each clip as the FIRST frame
  (image-to-video) of the next — especially A→B and D→E — so they flow seamlessly.
- **Keyframe-first on Shot D:** approve the single face still before spending a
  video generation on it. That's the only shot where her likeness must be exact.
- Generate each shot a little LONGER than the target (e.g. 6–7s); trimming is
  free, re-generating is not. I'll cut them to land the scene at ≤25s.

---

## Using Grok Imagine (workflow)

Grok makes short (~6s) clips and works best **image-first**: generate a still,
pick the best variation, then animate it. That also pins the face and the world.

**For each shot:**
1. **Make the still.** In Grok Imagine, choose **image**, set aspect ratio to
   **16:9**, paste the shot's *image prompt* (below). Generate a few; pick the best.
2. **Animate it.** Hit **make video** on that still, paste the shot's *motion line*,
   generate ~6s. Grok clips are ~6s — that's fine, I'll trim.
3. **Continuity:** download the **last frame** of each clip and use it as the
   **starting image** of the next shot (especially A→B and D→E).
4. **Her face (Shot D only):** upload the clearest **park photo** as the reference
   image for that still. Generate several and pick the closest face, *then* animate.
5. Grok may add its own **sound** — ignore it; send me the video and I'll mute it
   and score it.

**Prompt style for Grok:** keep it short and concrete — 2–3 sentences. Put the
look in the image prompt; keep the motion line simple ("slow", "gentle"), because
Grok gets chaotic with busy motion.

Reusable **style suffix** (add to every image prompt):
> Tang dynasty Silk Road desert, golden hour, blowing dust, warm amber and teal,
> cinematic film still, shallow depth of field, 16:9.

### Grok-tuned prompts

**A — Caravan arrives**
- *Image:* A small caravan of two camels with bundles and two hooded travelers approaches a weathered desert watchtower where soldiers with dark-red banners wait. Wide view, low warm sun behind them. [style suffix]
- *Motion:* Slow forward drift toward the tower, dust blowing gently.

**B — Greeting**
- *Image:* A small hooded child in a sand-colored desert cloak stands facing a battle-worn Tang general in red cape and plumed helmet, warm low sunlight, dust motes. Medium shot, her face shadowed by the hood. [style suffix]
- *Motion:* The child bows her head slowly; the general nods. Minimal movement.

**C — The pebbles** (the plant)
- *Image:* Extreme close-up of a weathered scarred hand pressing two small pale grey-green river pebbles, each carved with a faint spiral, into a child's small open palm. Warm backlight, floating dust. [style suffix]
- *Motion:* The small fingers slowly close around the pebbles. Very slow, delicate.

**D — Face glimpse** (upload the park photo as reference for the image)
- *Image:* Photoreal close-up of a ~7-year-old girl's face inside a sand-colored desert hood, warm golden light across her face, quiet brave expression, large dark eyes. [style suffix]
- *Motion:* Slow push-in; a shaft of light crosses her face, then shadow returns.

**E — Departure**
- *Image:* Aerial wide view of a small caravan of camels riding away across vast golden dunes toward the low sun, long shadows and a trail of dust, a tiny watchtower behind. [style suffix]
- *Motion:* Slow rising pull-back as they ride into the distance.

**A note on the face:** Grok isn't a precise face-lock tool, so the glimpse in
Shot D may not match her exactly. The hood hides most of it; if the face drifts,
we fall back to a more shadowed partial and save the full reveal for a later
scene where we can get the likeness right.

## When you have the clips
Send me the five clips (in order) and I'll assemble them to ≤25s with smooth
transitions and compose the new lighter "journey" theme — a warmer, more
intimate motif (think solo flute / erhu over soft strings) than the general's
organ crescendo, timed to the final cut.
