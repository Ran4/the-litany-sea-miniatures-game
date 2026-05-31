# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Generate gpt-image-2 renders of the *miniatures* (bare unpainted plastic, one shade
per faction) -> minis/renders/<id>.png

Each full prompt is composed from three pieces so every model stays consistent:
    minis_style.json  plasticStyle   (studio / unpainted-plastic look, shared)
  + minis_prompts.json[i].body       (this model's silhouette / pose / gear)
  + minis_style.json  factionShades[factionIndex]   (the faction's plastic colour)

Threaded, with retries. Skips renders that already exist (so reruns are cheap).
Usage:  uv run minis/gen_minis.py            # all 40
        uv run minis/gen_minis.py f3_u6 f0_c1  # only these ids (optional filter)
Needs OPENAI_API_KEY in ../.env (same key as the book's gen_images.py).
"""
import os, sys, json, base64, pathlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "renders"
OUT.mkdir(exist_ok=True)


def load_key():
    # .env lives at the project root, next to the book pipeline (gitignored).
    for line in open(ROOT / ".env"):
        if line.strip().startswith("OPENAI_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no OPENAI_API_KEY in ../.env")


from openai import OpenAI
client = OpenAI(api_key=load_key())

STYLE = json.load(open(HERE / "minis_style.json", encoding="utf-8"))
MINIS = json.load(open(HERE / "minis_prompts.json", encoding="utf-8"))
PLASTIC = STYLE["plasticStyle"]
SHADES = STYLE["factionShades"]


def full_prompt(m):
    shade = SHADES[str(m["factionIndex"])]
    return f"{PLASTIC}\n\nThe miniature depicts: {m['body']}\n\n{shade}"


def gen(m):
    iid = m["id"]
    out = OUT / f"{iid}.png"
    if out.exists() and out.stat().st_size > 5000:
        return (iid, "skip", out.stat().st_size)
    size = m.get("size", "1024x1536")
    quality = m.get("quality", "medium")
    prompt = full_prompt(m)
    last = None
    for attempt in range(3):
        try:
            r = client.images.generate(model="gpt-image-2", prompt=prompt,
                                       size=size, quality=quality, n=1)
            out.write_bytes(base64.b64decode(r.data[0].b64_json))
            return (iid, "ok", out.stat().st_size)
        except Exception as e:
            last = str(e)[:160]
            time.sleep(3 * (attempt + 1))
    return (iid, "ERR:" + (last or "?"), 0)


def main():
    wanted = set(sys.argv[1:])
    todo = [m for m in MINIS if not wanted or m["id"] in wanted]
    print(f"generating {len(todo)} mini renders (skipping existing) -> {OUT}/ ...")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gen, m): m["id"] for m in todo}
        for f in as_completed(futs):
            iid, status, sz = f.result()
            print(f"  {iid:8s} {status:14s} {sz}")
            results.append((iid, status))
    ok = sum(1 for _, s in results if s in ("ok", "skip"))
    print(f"done: {ok}/{len(results)} present")
    bad = [iid for iid, s in results if s.startswith("ERR")]
    if bad:
        print("FAILED:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
