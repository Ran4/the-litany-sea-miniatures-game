# The Litany Sea — a SIXES miniatures-game rulebook

This repo generates an illustrated tabletop-wargame rulebook as **`.docx` → `.pdf`**.
The book is *content-as-data*: a JSON file holds the world/factions/scenarios, a Python
script lays it out, and an `assets/` folder holds the artwork. You edit the data (and/or
the layout/art), then re-run the pipeline.

- **Game system:** **SIXES** — a fast D6 skirmish game (one target number, alternating
  activations, 2 actions/model). The core rules are static text inside `sixes_book.py`.
- **Setting:** **The Litany Sea** — a war over the nature of truth on the drying wound of a
  grieving god; objectives are fragile memory-crystals you must capture *without shattering
  them*, under a shared receding-tide doomsday clock. Four asymmetric factions that each
  *score differently*: Mnemarchs (Set crystals), Ash Iconoclasts (Shatter), Brine-Factors
  (Sell), Sediment (Re-Dream / swarm).

## Regenerate the book (run after ANY change)

```bash
uv run render_maps.py     # scenario deployment maps  -> assets/map_*.png   (only if maps changed)
uv run gen_images.py      # gpt-image-2 art           -> assets/*.png       (skips existing; needs OPENAI_API_KEY in .env)
uv run sixes_book.py      # reads sixes_content.json + assets/ -> sixes_rulebook.docx
soffice --headless --convert-to pdf --outdir . sixes_rulebook.docx
```

For a text/data-only change you usually just need the last two lines (`sixes_book.py` +
`soffice`). Always regenerate the **PDF** too — that's the deliverable. Open it with
`xdg-open sixes_rulebook.pdf` the first time.

## The one design rule — DO NOT BREAK IT

**No modifier soup.** Never add chains of `+1/-1` to target numbers that cancel out.
Every bonus must be an **extra die, a re-roll, ignore-X, auto-pass, or a binary on/off
effect** — never target-number arithmetic, and modifiers must never stack into a sum.
Every special rule must (a) change a player decision, (b) be instant to apply, (c) tie to a
visible board state. If a rule only changes a number on the way to the same result, cut it.
This is the whole point of the game; keep it when adding anything.

## Where content lives: `sixes_content.json`

Top-level keys: `setting`, `council`, `factions[]`, `scenarios[]`, `campaign`, `advanced`,
`prose` (`winner` is just provenance, unused by the layout).

Edit this file to change lore, stats, points, scenarios, rules text, etc. — **no Python
needed**. The layout script reads it defensively (missing keys are skipped).

### How to add things

- **A unit** → append to `factions[i].units[]`:
  ```json
  {"name":"", "role":"", "M":"5\"", "SK":"4+", "DEF":"5+", "W":1, "A":1,
   "weapons":["..."], "wargear":["..."], "specialRules":["..."], "points":12, "flavor":"..."}
  ```
  (`M/SK/DEF` are strings like `"5\""`/`"4+"`; `W/A/points` are integers.)
- **A named character** → append to `factions[i].characters[]` (same stats plus
  `"title"` and `"uniqueRule":{"name":"","text":""}`).
- **A faction-specific weapon** → append to `factions[i].weaponsTable[]`:
  `{"name","range","shots","damage","special"}`.
- **A faction rule / subfaction** → `factions[i].factionSpecialRules[]` (`{name,text}`) or
  `factions[i].subfactions[]` (`{name,twist,ruleName,ruleText}`). `signatureRule` is the
  one mechanic that defines the faction.
- **A scenario** → append to `scenarios[]`:
  `{name, hook, setup, deployment, objectives, specialRules:[{name,text}], twist, length, victory}`.
  Then add a matching deployment map (see below) — scenario index N uses `assets/map_N.png`.
- **Campaign / advanced rules** → `campaign.progression[]`, `campaign.injuries[]` (`{roll,result}`),
  `advanced.terrainTypes[]`, `advanced.environmentEvents[]` (`{roll,name,text}`), `advanced.optionalRules[]`.
- **Lore / fiction** → `setting.*` and `prose.*` (`openingFiction`, `worldIntro`,
  `grandTimeline[]`, `sectionEpigraphs[]`, `closingFiction`).
- **A whole new faction** → append to `factions[]`. Also add its art: faction index `i`
  expects `assets/fac_<i>.png` (splash), `assets/unit_<i>_1.png` (character), and
  `assets/unit_<i>_2.png` (rank-and-file). Add prompts for those ids to `images_prompts.json`
  and run `gen_images.py`, or the book just renders without them.

Keep points/stats inside engine ranges: `M` 4–8", `SK` 2+–5+, `DEF` 3+–6+, `W` 1–4,
`A` 1–4, ~10–35 pts/model, warbands ~100–150 pts.

## Artwork

Two kinds, both embedded by `sixes_book.py` if the file exists in `assets/` (it degrades
gracefully if missing):

**1. Painted illustrations — gpt-image-2.** Prompts live in `images_prompts.json` (a list of
`{id, kind, size, quality, factionIndex?, prompt, caption}`). `style_guide.json` is the
shared visual identity (dark painterly oil, rust-red sun, salt/brine palette) — keep new
prompts consistent with it. Image ids and where they appear:
`cover` (title), `world_toll` + `world_shatter` (Part I), `fac_0..3` (faction splashes),
`unit_0_1..unit_3_2` (2 portraits/faction: `_1` = character, `_2` = unit).
- **Re-roll one image:** delete its `assets/<id>.png` and rerun `gen_images.py` (others are
  skipped — cheap and fast). To change *what* it depicts, edit its `prompt` in
  `images_prompts.json` first.
- gpt-image-2 call: `client.images.generate(model="gpt-image-2", prompt=..., size="1024x1024"|"1536x1024"|"1024x1536", quality="high"|"medium"|"low")` → `data[0].b64_json`.
- Be VERY specific in prompts (130–220 words, stacked concrete modifiers) and always
  forbid text/letters/logos in the image.

**2. Deployment maps — matplotlib (deterministic, precise).** `render_maps.py` holds
`MAPS = [...]`, one hand-authored spec per scenario (board size, tidal `bands`, `grid`,
`regions`, `deploy` zones, `crystals`, `terrain`, `arrows`, `notes`). Scenario index N →
`assets/map_N.png`. Edit the spec to match the scenario's `setup`/`deployment`/`objectives`,
then `uv run render_maps.py`. These are diagrams, not AI art — keep them accurate.

## File map

| File | Purpose |
|---|---|
| `sixes_content.json` | **All book content** (world, factions, scenarios, campaign, prose). Edit this most. |
| `sixes_book.py` | Layout generator: static SIXES core rules + content + embeds `assets/`. Edit for layout/visual/core-rule changes. |
| `render_maps.py` | Scenario deployment maps (`MAPS=[...]` specs) → `assets/map_*.png`. |
| `gen_images.py` | Generates gpt-image-2 art from `images_prompts.json` → `assets/*.png` (skips existing). |
| `images_prompts.json` / `style_guide.json` | Art prompts and the shared visual style. |
| `assets/` | 15 painted plates + 5 maps (PNG). |
| `build_brief.py` / `art_brief.json` / `brief/` | One-off: built the compact lore brief fed to the art workflow. Not needed to rebuild the book. |
| `sixes_rulebook.py` | **Obsolete v1** single-file generator (generic, no lore/art). Ignore. |
| `sixes_rulebook.docx` / `.pdf` | Build outputs (gitignored). |

## Gotchas

- The `.docx` is large (~28 MB) because full-res PNGs are embedded; the PDF is ~5 MB. To
  shrink, downscale images in `assets/` before building.
- `.env` holds `OPENAI_API_KEY` and is gitignored — never commit it or print the key.
- `*rulebook.docx`/`*rulebook.pdf` are gitignored (regenerate them; don't commit).
- Python is run with **`uv`** (inline-script deps in each file's header), not pip.
