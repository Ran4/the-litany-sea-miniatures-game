# Lore videos — "Your Life as a ___" faction films

This folder generates narrated, illustrated **lore videos** for *The Litany Sea* factions,
in the style of the YouTube "Your life as a ___" Warhammer lore videos: a **second-person
life story** (you are born → called → taken → unmade → first battle → the cosmic truth →
your death), told over slow Ken-Burns pans across painterly plates, with burned-in captions
and a tolling ambient bed.

The content is **data** (`storyboards/<faction>.json`); Python turns it into an `.mp4`.
One faction = one storyboard = one video. **`mnemarchs` is the finished reference.**

## TL;DR — render a faction video

```bash
cd lore_videos
uv run render.py mnemarchs          # runs all four stages -> mnemarchs.mp4
```

`render.py` just chains the four stages below (each re-runnable on its own, each skips work
that already exists, so re-runs are cheap):

```bash
uv run gen_narration.py    mnemarchs   # ElevenLabs TTS  -> build/<f>/audio/*.mp3 + timeline.json
uv run gen_scene_images.py mnemarchs   # gpt-image-2 art -> build/<f>/scenes/*.png   ($ + slow)
uv run gen_music.py        mnemarchs   # procedural bed  -> build/<f>/music/bed.wav
uv run build_video.py      mnemarchs   # assemble        -> <f>.mp4   (the long render)
```

Needs `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` in `../.env` (already there). The ElevenLabs
key only needs the **text-to-speech** permission. The first `xdg-open mnemarchs.mp4` to watch.

## How it works (data flow)

```
storyboards/<faction>.json ─┬─► gen_narration.py ─► audio/<id>.mp3  + timeline.json (durations)
   (scenes: narration,      ├─► gen_scene_images.py ─► scenes/<id>.png   (1536x1024 painterly plate)
    image_prompt, chapter)  └─► (captions are derived from narration at build time)
                                            │
   ../style_guide.json ──────────► wraps every image_prompt (shared visual identity)
                                            ▼
timeline.json ─► gen_music.py ─► music/bed.wav   (drone + brine-wind + bell tolls, sized to narration)
                                            ▼
   everything ─► build_video.py ─► <faction>.mp4
       Pass A: per-scene Ken Burns clip (slow zoom/pan, cached by image mtime)
       Pass B: one ffmpeg graph — xfade cross-dissolves + burned EB-Garamond captions
               + chapter titles + narration over a side-chain-ducked music bed
```

Audio and video stay in lock-step: each scene's video length is its **freshly-probed**
narration length + one crossfade, and the xfade offsets are chosen so scene *i*'s narration
begins exactly as its plate dissolves in. Captions are timed off the cumulative narration
durations (so they always match the voice).

## The storyboard schema (`storyboards/<faction>.json`)

```jsonc
{
  "title": "Your Life as a Mnemarch",
  "faction": "Mnemarchs — Order of the Set Hour",
  "protagonist": "Sael of the Low Pans — …",      // one-line who-they-are
  "total_words_estimate": 1837,
  "scenes": [
    {
      "id": "01_low_pans",                          // unique, ordered; names the asset files
      "chapter": "Mirror-Water",                    // chapter title (shown briefly at top on change)
      "narration": "You were born barefoot on …",   // STRICT second person; 1-4 short sentences
      "image_prompt": "Wide low-horizon establishing shot of a vast cracked salt-flat …"
    }
    // … 24-30 scenes
  ]
}
```

Rules that keep it good:
- **Strict second person** throughout ("You were born…", "You learn…"). The viewer *is* the warrior.
- **~1500–1900 narration words total** ⇒ ~10–13 min at the narrator's ~140 wpm (target is loose;
  8–12 min is the ask). Word count drives runtime — trim/add narration to retune length.
- **`image_prompt` is scene-specific only** (55–90 words): subject, composition, focal object,
  lighting, mood. Do **not** restate the global art style or a negative prompt — `gen_scene_images.py`
  wraps every prompt with `../style_guide.json`'s `styleString` + `negativePrompt` automatically.
  Never ask for readable text/letters/logos or modern objects.
- Vary shots (wide establish / intimate crystal-or-face close / ritual symmetry / action diagonal).
- The **ending should rhyme with the opening** (a keepsake, a loss, an image).

## Making a NEW faction video

The factions are Mnemarchs (done), Ash Iconoclasts, Brine-Factors, Sediment. For each:

1. **Flesh out the lore, then write the storyboard.** This was done with a multi-agent
   **Workflow** (see "the workflow" below). The grounding source pack lives in `_source/`
   (`reference_format.md` = the genre rules; `mnemarch_lore.md` = the canon brief; swap in the
   target faction's canon from `../sixes_content.json`). Output → `storyboards/<faction>.json`.
2. **Pick/keep a narrator.** Default is ElevenLabs premade **"Daniel"** (deep, grave, British),
   voice id in `common.py` (`DEFAULT_VOICE_ID`). Override per-run with `ELEVEN_VOICE_ID` in `../.env`.
   Match the voice to the faction's mood if you like (e.g. an Iconoclast film might want a harsher read).
3. `uv run render.py <faction>`. Watch `<faction>.mp4`.

### the workflow (how the Mnemarch storyboard was authored)

A background `Workflow` fanned out four lore-expansion agents (people / ritual / war / cosmic-truth),
then an architect (cradle-to-grave beat sheet), a scriptwriter (storyboard JSON via a strict schema),
and an editor that verified canon + tone + length and wrote `storyboard.json`. To author the next
faction, re-run that pattern with the new faction's canon brief in `_source/`. The Mnemarch storyboard
is also copied verbatim to `storyboards/mnemarchs.json` (the canonical path the pipeline reads).

## Tuning knobs

- **Re-roll one plate:** delete `build/<f>/scenes/<id>.png` and rerun `gen_scene_images.py` (others
  skip). To change *what* it shows, edit that scene's `image_prompt` first.
- **Re-do one line of narration:** delete `build/<f>/audio/<id>.mp3`, edit the `narration`, rerun
  `gen_narration.py`, then `build_video.py`.
- **Re-assemble only** (after tweaking transitions/captions, assets unchanged):
  `uv run build_video.py <f> --skip nothing` — or just `build_video.py <f>` (clips are cached by
  image mtime; pass `--force` to re-render all Ken Burns clips).
- **Quick preview:** `uv run build_video.py <f> --limit 4` renders just the first 4 scenes.
- Knobs live at the top of `build_video.py` (`XFADE`, `FPS`, `KB` pan/zoom presets) and
  `common.py` (caption font/size/style in `ASS_HEADER`, `split_captions`), and `gen_music.py`
  (drone notes, bell period). Narrator settings: `gen_narration.py` `VOICE_SETTINGS`.

## File map

| File | Purpose |
|---|---|
| `storyboards/<faction>.json` | **The content** — scenes (narration + image prompts + chapters). Edit this most. |
| `storyboard.json` | Raw workflow output for the latest faction (mirror of the canonical storyboards/ copy). |
| `render.py` | One-command orchestrator: runs the four stages in order. |
| `gen_narration.py` | ElevenLabs TTS per scene → `audio/*.mp3`; probes durations → `timeline.json`. stdlib only. |
| `gen_scene_images.py` | gpt-image-2 plate per scene → `scenes/*.png`, wrapped in `../style_guide.json`. |
| `gen_music.py` | Procedural dark-ambient bed (drone + brine-wind + bell tolls) → `music/bed.wav`. numpy. |
| `build_video.py` | Ken Burns + xfade + burned captions + ducked music → `<faction>.mp4`. ffmpeg. |
| `common.py` | Shared stdlib helpers: paths, .env, ffprobe, caption splitting, ASS subtitle builder. |
| `_source/` | Grounding for the lore workflow (reference-format notes, faction canon brief, ref transcript). |
| `_reference/` | The studied reference video, its transcript, and sampled frames. (gitignored) |
| `build/<faction>/` | All generated intermediates (audio, scenes, clips, music, timeline, captions). (gitignored) |
| `<faction>.mp4` | **The deliverable.** (gitignored — regenerate it) |

## Gotchas

- **Cost/time:** `gen_scene_images.py` makes ~25–30 high-quality gpt-image-2 calls (the slow,
  paid step); `gen_narration.py` makes ~25–30 ElevenLabs calls. Both skip existing files, so
  iterate cheaply. `build_video.py`'s Pass B is a single long ffmpeg render (minutes).
- **ffmpeg 4.4 quirk:** `sidechaincompress` can't auto-negotiate formats and errors if its two
  inputs differ in length/format — both are forced to `fltp/stereo/44100` and padded/trimmed to
  equal length in `build_video.py`. Don't remove the `aformat`/`apad`/`atrim`.
- **Captions:** the ASS `[Events]` Format line **must** include `MarginV` (10 fields) or every
  caption renders with a stray leading comma. Keep `EB Garamond` (present on this machine) or
  pick another installed font (`fc-list`).
- **Runtime = words / ~140 wpm.** If a video runs long/short, edit narration length, not the code.
- **Plate aspect:** gpt-image-2 plates are 1536×1024 (3:2); Ken Burns pans/crops them to 16:9,
  so keep important subjects off the extreme top/bottom edges in `image_prompt`s.
- `../.env` holds the keys and is gitignored — never commit or print them.
