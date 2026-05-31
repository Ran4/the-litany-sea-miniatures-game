# Reference format — "Your life as a ___" lore video

Source studied: *"Your life as a Grey Knight (Warhammer 40k)"* (YouTube 0PNqjWR8cm0).
Runtime ~18.7 min, narration ~3,084 words at **~165 words/min**. We are targeting
**8–12 minutes ⇒ ~1,500–1,900 words** of narration.

## What the format IS (copy this — it's the genre)

1. **Second person, present-as-fate.** The entire script is "**You** were born…",
   "**You** learn…", "**You** will…". The viewer *is* the recruit. Never "the recruit"
   or "a Mnemarch" — always **you**.
2. **A single life, cradle to grave.** It follows ONE person's whole arc:
   - **Birth / origin** — an ordinary, fragile beginning; a wound or loss.
   - **The calling** — the strange gift or event that marks you as different and dooms
     your old life. (In Grey Knights: psychic visions. For us: see lore.)
   - **Taken / recruited** — you are removed from everything you knew. It is not
     presented as glory; it is presented as a kind of death.
   - **The training / unmaking** — brutal, total, transformative. You are remade. Most
     do not survive it. You lose your name, your face, your memory of who you were.
   - **First service / first battle** — terror, awe, the reality of the war.
   - **The long service** — what the rest of your existence is actually like, day to day.
   - **The truth** — a turn where the narrator reveals the darker cosmic truth the recruit
     half-learns (the secret of what they really are / what the war is really for).
   - **The end** — your death or final fate, quiet and certain, tying back to the opening.
3. **Tone:** intimate, melancholy, awed, doomed-but-meaningful. Grand cosmic stakes felt
   through one small life. It earns emotion; it is not a stat dump.
4. **Concrete sensory detail over exposition.** Name the friends you had as a child. Name
   the smell. Describe the one ritual object you hold. Specific > abstract, always.
5. **Pacing:** short paragraphs, frequent hard stops. The narrator lingers on images.
6. **Lore is delivered AS lived experience,** not as an encyclopedia. The viewer learns
   the faction's beliefs, hierarchy, units and signature mechanic *because they happen to you.*

## How OUR version differs from the reference (deliberately)

- **Visuals:** NOT crude cartoon. We render **dark painterly oil-illustration** plates
  (gpt-image-2), one per scene, consistent with the project's `style_guide.json`. Slow
  Ken-Burns pushes, crossfades, burned-in captions, an ambient tolling-bell music bed.
- **No real-world references.** Stay entirely inside the Litany Sea fiction.
- **Anchor the faction's actual game identity** so a player recognizes it: the verb
  **Set**, the **Two Witnesses**, **salt-stiffened** rigidity, bunkering in the **brine**,
  racing the **Long Toll**. The mechanics must surface as lived ritual, never as rules text.

## Deliverable shape

A `storyboard.json`: an ordered list of **scenes**, each with:
- `id` (e.g. "01_birth"),
- `chapter` (short title, e.g. "The Salt-Child"),
- `narration` (the spoken text for that scene; 1–4 short sentences),
- `image_prompt` (a vivid gpt-image-2 prompt for the plate, style-guide-consistent),
- `caption_hint` (optional: how to chunk captions, usually auto).

Total narration across all scenes ≈ 1,500–1,900 words ⇒ ~10 minutes at 165 wpm.
Aim for ~22–32 scenes (≈ 18–30 s each).
