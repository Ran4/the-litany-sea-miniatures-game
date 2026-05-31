# `minis/` — miniatures, unit boxes & starter sets

Studio "product photo" renders of the game's models, sold the way a real miniatures-wargame
range would be. Three pipelines, all gpt-image-2, all driven from the game data in
`../sixes_content.json` and all sharing the same per-faction look:

1. **`renders/`** — the bare **unpainted plastic miniatures**, one distinct plastic shade per
   faction so the four armies read apart even unpainted (paint later if you're not lazy).
   One render per character and per unit (8 + 32 = **40 models**).
2. **`boxes/`** — a **unit box** (boxed-set product shot) for every one of those 40 models:
   painterly box-front art + faction-coloured border + an inset strip of that model's plastic.
3. **`starters/`** — **three two-player starter sets**, each a *different* pair of factions at
   a *different* size, with a box shot, a "what's in the box" contents flat-lay, and a
   press-out cardboard-terrain shot (3 images each = **9**).

These are **deliberately not** the painterly oil book-art in `../assets/` (though the box/
starter *cover art* is rendered in that same painterly style). Source of truth for *which
models exist* is `../sixes_content.json` (`factions[i].characters[]` / `factions[i].units[]`).

## The four faction plastic shades

Chosen to be four clearly-distinct tones that don't blur into each other across a table:

| Idx | Faction | Plastic shade | Box / cover branding |
|---|---|---|---|
| 0 | Mnemarchs | pale warm **bone-ivory grey** | verdigris-bronze & bone-white |
| 1 | Ash Iconoclasts | dark **charcoal gunmetal grey** | char-black & ember-orange |
| 2 | Brine-Factors | cool **verdigris teal blue-green** | iodine-teal & brass-amber |
| 3 | Sediment | warm muddy **ochre sand-tan** | drowned-grey & ochre sand |

Plastic shades live in `minis_style.json` (`factionShades`); branding/blurbs/short shade names
live in `boxes_style.json`. If you add a 5th faction, add a 5th entry to **both**, distinct
from these four.

## id scheme

`f<faction>_c<n>` = character, `f<faction>_u<n>` = unit, numbered in `sixes_content.json`
order. e.g. `f0_c1` = Antiphon Vael; `f3_u6` = Standing Salt. The same id is reused across
`renders/<id>.png` and `boxes/<id>.png`. Starter shots are `starters/<setid>_<box|contents|terrain>.png`.

## Files

| File | Purpose |
|---|---|
| `minis_style.json` | Shared plastic look (`plasticStyle`) + per-faction plastic `factionShades`. Edit to restyle **all** minis. |
| `minis_prompts.json` | One entry per model `{id, factionIndex, kind, name, role, size, quality, body, caption}`. `body` = **only** silhouette/pose/gear. Single source of truth for both minis **and** boxes. |
| `gen_minis.py` | Mini renders → `renders/<id>.png`. |
| `boxes_style.json` | Shared box-packaging look + per-faction `factionBranding` / `plasticShort` / `factionBlurb`. |
| `gen_boxes.py` | Unit-box product shots → `boxes/<id>.png` (reuses `minis_prompts.json` bodies). |
| `starters.json` | The 3 starter sets `{id, name, tier, factions:[a,b], boxShape, clashArt, contents, terrain}`. |
| `gen_starters.py` | Starter box/contents/terrain shots → `starters/<setid>_<shot>.png`. |
| `renders/` `boxes/` `starters/` | Output PNGs (~2–3 MB each). |

All three generators: composed from `__file__`-relative paths (cwd-independent), threaded,
retry 3×, **skip any output that already exists** (reruns are cheap), and read
`OPENAI_API_KEY` from `../.env`. Each accepts optional id args to render only a subset.

---

## 1. Miniatures (`gen_minis.py`)

Prompt = `plasticStyle`  +  `"The miniature depicts: " + body`  +  `factionShades[factionIndex]`.
So a `body` describes **only** the figure (stance, weapons, wargear, silhouette); the studio
framing, "no paint / no text" guards, and the plastic colour are added automatically.

```bash
uv run minis/gen_minis.py              # all 40 (skips existing)
uv run minis/gen_minis.py f3_u6 f0_c1  # only these ids
```

## 2. Unit boxes (`gen_boxes.py`)

Prompt = `boxStyle` + box-front art (the model's `body`, reframed as a painterly action scene
with `factionBlurb`) + `factionBranding[fi]` border + `plasticShort[fi]` inset strip. It reuses
`minis_prompts.json`, so a box always matches its mini — fix the `body` once and regenerate both.

```bash
uv run minis/gen_boxes.py              # one box for every model (skips existing)
uv run minis/gen_boxes.py f1_u3        # only this id
```

## 3. Starter sets (`gen_starters.py`)

Each entry in `starters.json` pairs **two** factions at a size and yields three shots:
`_box` (closed dual-faction box), `_contents` (top-down flat-lay: plastic minis in *both*
faction shades + rulebook + dice + tokens + terrain), `_terrain` (assembled press-out
cardboard scenery with minis for scale). Branding/blurb/plastic come from `boxes_style.json`.

The three sets (distinct pairings, ascending size):

| id | name | factions | tier |
|---|---|---|---|
| `starter_small` | Duel of the Set Hour | Mnemarchs (0) vs Ash Iconoclasts (1) | small / 2-player intro |
| `starter_medium` | Tide and Ledger | Brine-Factors (2) vs Sediment (3) | medium / battle set |
| `starter_large` | The Grand Litany | Mnemarchs (0) vs Sediment (3) | large / collector's box |

```bash
uv run minis/gen_starters.py                       # all sets × all 3 shots (skips existing)
uv run minis/gen_starters.py starter_small         # one set (all 3 shots)
uv run minis/gen_starters.py starter_large_terrain # one exact shot
```

---

## Common recipes

- **Re-roll one image:** delete its PNG and rerun that generator with its id — everything else
  is skipped, so it's fast and cheap. To change *what* it depicts, edit the source first
  (`minis_prompts.json` body, or the `starters.json` field).
- **Restyle everything of a kind:** edit the shared style file (`minis_style.json` /
  `boxes_style.json` / the templates in `gen_starters.py`), delete that output folder, rerun.
- **Recolour a faction:** edit `factionShades` (and `boxes_style.json` branding/`plasticShort`),
  delete that faction's outputs (`renders/f<i>_*`, `boxes/f<i>_*`, affected starters), rerun.
- **Add a new model:** add it to `../sixes_content.json`, append an entry to
  `minis_prompts.json` (see body tips below), then `gen_minis.py f<i>_u<n>` and
  `gen_boxes.py f<i>_u<n>`.
- **Add / change a starter:** edit `starters.json` (keep `factions` to a 2-faction pair; pick a
  pair not already used if you want all distinct), then `gen_starters.py <id>`.

### `body` writing tips (keep models on-style)

- Describe a **single tabletop miniature**: one figure (or a clearly bounded multi-figure
  group / vehicle) in a readable hero pose; one primary weapon held clearly.
- Lead with the pose verb (striding / kneeling / mid-throw / planted), then the gear.
- For palanquins, litters, skiffs, sledges and swarms, say **"the … is the integral base"** /
  **"N figures, one base"** so it renders as one model, not a scene.
- Don't put colour, lighting, backdrop or "no text" in `body` — those come from the style files.
- `size`: `1024x1536` (portrait) for a single upright figure; `1024x1024` (square) for wide
  bases / groups. Boxes are always square; starter contents/terrain are `1536x1024`.
  `quality`: `medium` is the cost/quality default; bump a hero to `high` if you want.

## gpt-image-2 call (reference)

```python
client.images.generate(model="gpt-image-2", prompt=…,
                       size="1024x1024"|"1536x1024"|"1024x1536",
                       quality="high"|"medium"|"low") -> data[0].b64_json
```

## Notes

- `../.env` holds `OPENAI_API_KEY` (gitignored) — never commit or print it.
- gpt-image-2 can't render legible text, and the whole range forbids it anyway: every prompt
  hard-forbids words, so all box titles / labels / tokens come out as blank embossed plates or
  abstract painted bands. That's intentional — don't try to add real lettering via the prompt.
- None of these are embedded in the rulebook by `../sixes_book.py`; they're a separate
  catalogue/marketing set. (To put one in the book, wire its PNG into the layout the same way
  `../assets/` art is embedded.)
