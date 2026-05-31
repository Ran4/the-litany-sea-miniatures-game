# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Generate one painterly plate per storyboard scene with gpt-image-2
-> build/<faction>/scenes/<id>.png  (landscape 1536x1024, high quality).

Each scene's scene-specific `image_prompt` is wrapped with the project's shared visual
identity from ../style_guide.json (styleString + negativePrompt), so every plate matches
the rulebook art. Threaded, with retries; skips images that already exist (delete one to
re-roll it; edit its image_prompt in the storyboard first to change what it depicts).

Usage:  uv run gen_scene_images.py [faction]   (default: mnemarchs)
Needs OPENAI_API_KEY in ../.env.
"""
import sys, json, base64, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import common

FACTION = sys.argv[1] if len(sys.argv) > 1 else "mnemarchs"
SIZE = "1536x1024"     # widest gpt-image-2 ratio; the renderer pans/crops to 16:9
QUALITY = "high"

from openai import OpenAI
client = OpenAI(api_key=common.env("OPENAI_API_KEY"))

_style = json.loads((common.ROOT / "style_guide.json").read_text(encoding="utf-8"))
STYLE_STRING = _style["styleString"]
NEGATIVE = _style["negativePrompt"]


def full_prompt(scene_prompt):
    return (
        f"{scene_prompt.strip()}\n\n"
        f"ART STYLE (apply consistently): {STYLE_STRING}\n\n"
        f"STRICTLY AVOID: {NEGATIVE}\n\n"
        f"This is a single illustrated plate in a dark painterly fantasy art-book. "
        f"Absolutely no text, letters, numbers, captions, logos or watermarks anywhere."
    )


def gen(scene, scenes_dir):
    sid = scene["id"]
    out = scenes_dir / f"{sid}.png"
    if out.exists() and out.stat().st_size > 5000:
        return (sid, "skip", out.stat().st_size)
    prompt = full_prompt(scene["image_prompt"])
    last = None
    for attempt in range(3):
        try:
            r = client.images.generate(model="gpt-image-2", prompt=prompt,
                                       size=SIZE, quality=QUALITY, n=1)
            out.write_bytes(base64.b64decode(r.data[0].b64_json))
            return (sid, "ok", out.stat().st_size)
        except Exception as e:
            last = str(e)[:160]
            time.sleep(4 * (attempt + 1))
    return (sid, "ERR:" + (last or "?"), 0)


def main():
    sb = common.load_storyboard(FACTION)
    p = common.paths(FACTION)
    p["scenes"].mkdir(parents=True, exist_ok=True)
    scenes = sb["scenes"]
    print(f"[{FACTION}] generating {len(scenes)} scene plates ({SIZE}, {QUALITY}); skipping existing")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gen, s, p["scenes"]): s["id"] for s in scenes}
        for f in as_completed(futs):
            sid, status, sz = f.result()
            print(f"  {sid:20s} {status:14s} {sz}")
            results.append((sid, status))
    ok = sum(1 for _, s in results if s in ("ok", "skip"))
    print(f"[{FACTION}] done: {ok}/{len(results)} plates present")
    bad = [sid for sid, s in results if s.startswith("ERR")]
    if bad:
        print("FAILED:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
