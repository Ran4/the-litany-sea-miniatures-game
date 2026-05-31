# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Generate gpt-image-2 *unit-box* product shots — one boxed-set box per model
(painterly box-front art + faction border + an inset strip of the unpainted plastic).
-> minis/boxes/<id>.png

Reuses minis_prompts.json as the single source of truth for which models exist and their
pose/gear (body); boxes_style.json supplies the shared packaging look and per-faction
branding. So a box stays in sync with its mini — edit the body once.

    boxes_style.boxStyle  (packaging / studio look, shared)
  + "box-front illustration depicts: " + minis_prompts[i].body   (reframed as a scene)
  + boxes_style.factionBranding[fi]  (border colour) + plasticShort[fi]  (inset strip)

Threaded, retries, skips existing. Usage:
    uv run minis/gen_boxes.py            # one box for every model
    uv run minis/gen_boxes.py f0_c1 f1_u3   # only these ids
Needs OPENAI_API_KEY in ../.env.
"""
import sys, json, base64, pathlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "boxes"
OUT.mkdir(exist_ok=True)


def load_key():
    for line in open(ROOT / ".env"):
        if line.strip().startswith("OPENAI_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no OPENAI_API_KEY in ../.env")


from openai import OpenAI
client = OpenAI(api_key=load_key())

BOX = json.load(open(HERE / "boxes_style.json", encoding="utf-8"))
MINIS = json.load(open(HERE / "minis_prompts.json", encoding="utf-8"))


def full_prompt(m):
    fi = str(m["factionIndex"])
    return (
        f"{BOX['boxStyle']}\n\n"
        f"The box-front illustration depicts: {m['body']} — rendered as a dramatic "
        f"painterly action scene on the cracked salt-flat under the rust-red sun, "
        f"featuring {BOX['factionBlurb'][fi]}.\n\n"
        f"The faction border, sigil and branding colours are {BOX['factionBranding'][fi]}; "
        f"the inset product strip along the bottom shows this model's miniatures moulded in "
        f"{BOX['plasticShort'][fi]}."
    )


def gen(m):
    iid = m["id"]
    out = OUT / f"{iid}.png"
    if out.exists() and out.stat().st_size > 5000:
        return (iid, "skip", out.stat().st_size)
    last = None
    for attempt in range(3):
        try:
            r = client.images.generate(model="gpt-image-2", prompt=full_prompt(m),
                                       size="1024x1024", quality="medium", n=1)
            out.write_bytes(base64.b64decode(r.data[0].b64_json))
            return (iid, "ok", out.stat().st_size)
        except Exception as e:
            last = str(e)[:160]
            time.sleep(3 * (attempt + 1))
    return (iid, "ERR:" + (last or "?"), 0)


def main():
    wanted = set(sys.argv[1:])
    todo = [m for m in MINIS if not wanted or m["id"] in wanted]
    print(f"generating {len(todo)} unit boxes (skipping existing) -> {OUT}/ ...")
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
