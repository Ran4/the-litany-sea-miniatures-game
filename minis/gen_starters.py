# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Generate gpt-image-2 *starter-set* product shots. For each set in starters.json it makes
three images into minis/starters/:
    <id>_box       closed box hero shot (painterly dual-faction cover, blank title)
    <id>_contents  top-down 'what's in the box' flat-lay (plastic minis in BOTH faction
                   shades, rulebook, dice, tokens, cardboard terrain)
    <id>_terrain   the press-out paper/cardboard terrain, assembled, minis for scale

Each starter pairs a DIFFERENT 2 factions at a different size (small / medium / large).
Faction branding colours, one-line blurbs and plastic shades come from boxes_style.json.

Threaded, retries, skips existing. Usage:
    uv run minis/gen_starters.py                       # all sets, all 3 shots each
    uv run minis/gen_starters.py starter_small         # one set (all 3 shots)
    uv run minis/gen_starters.py starter_large_terrain # one exact shot
Needs OPENAI_API_KEY in ../.env.
"""
import sys, json, base64, pathlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "starters"
OUT.mkdir(exist_ok=True)


def load_key():
    for line in open(ROOT / ".env"):
        if line.strip().startswith("OPENAI_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no OPENAI_API_KEY in ../.env")


from openai import OpenAI
client = OpenAI(api_key=load_key())

BOX = json.load(open(HERE / "boxes_style.json", encoding="utf-8"))
SETS = json.load(open(HERE / "starters.json", encoding="utf-8"))
BRAND, PLASTIC = BOX["factionBranding"], BOX["plasticShort"]

NOTEXT = ("Absolutely no readable text, letters, numbers, logos or watermarks anywhere — "
          "all title, label, booklet and token surfaces are blank embossed plates, "
          "painterly art, or abstract marks where words would be.")


def fields(s):
    a, b = str(s["factions"][0]), str(s["factions"][1])
    return dict(brandA=BRAND[a], brandB=BRAND[b], plastA=PLASTIC[a], plastB=PLASTIC[b])


def prompt_box(s):
    f = fields(s)
    return (
        f"Studio product photograph of a collectible two-player miniatures-wargame STARTER "
        f"boxed set — {s['boxShape']} — shot at a three-quarter hero angle on a clean "
        f"seamless neutral light-grey studio backdrop with a soft contact shadow. The lid is "
        f"a dramatic dark painterly oil illustration in a grief-soaked mythic fantasy style "
        f"(visible brushwork, muted salt-and-brine palette, a low rust-red never-setting sun "
        f"over a cracked drying salt-flat, glowing salt-glass crystals) depicting {s['clashArt']}. "
        f"The box carries a split faction-coloured border — {f['brandA']} on one side versus "
        f"{f['brandB']} on the other — with a large blank embossed central title cartouche and "
        f"two faction sigil panels bearing NO readable letters. Glossy printed cardboard, real "
        f"3D box depth, premium packaging photography, soft even studio light. {NOTEXT}"
    )


def prompt_contents(s):
    f = fields(s)
    return (
        f"Studio top-down flat-lay product photograph showing EVERYTHING inside a two-player "
        f"miniatures-wargame starter set, neatly arranged on a clean neutral light-grey "
        f"surface: the open {s['boxShape']} with its painterly lid, and {s['contents']}. The "
        f"miniatures are bare unpainted plastic arranged in two armies — one moulded in "
        f"{f['plastA']}, the other in {f['plastB']}; a rules booklet with a painterly cover; "
        f"a scatter of six-sided dice; punch-out cardboard tokens of glowing salt-glass "
        f"crystals and tide markers; and {s['terrain']}. Crisp catalogue 'what's in the box' "
        f"photography, soft even lighting, every component laid out and clearly visible. {NOTEXT}"
    )


def prompt_terrain(s):
    f = fields(s)
    return (
        f"Studio product photograph of the press-out paper-and-cardboard scenery from a "
        f"miniatures-wargame starter set, assembled and arranged as a small tabletop scene on "
        f"a clean neutral light-grey backdrop: {s['terrain']} — flat-pack die-cut cardboard "
        f"terrain with tab-and-slot construction and visible printed cardstock thickness, "
        f"printed with dark painterly salt-flat art (cracked crust, verdigris bronze, "
        f"brine-teal, rust-red light). A few bare unpainted plastic miniatures — some in "
        f"{f['plastA']}, some in {f['plastB']} — stand among the terrain for scale. Crisp "
        f"hobby catalogue photography, soft even light. {NOTEXT}"
    )


SHOTS = {"box": prompt_box, "contents": prompt_contents, "terrain": prompt_terrain}
SIZE = {"box": "1024x1024", "contents": "1536x1024", "terrain": "1536x1024"}


def gen(job):
    s, shot = job
    iid = f"{s['id']}_{shot}"
    out = OUT / f"{iid}.png"
    if out.exists() and out.stat().st_size > 5000:
        return (iid, "skip", out.stat().st_size)
    last = None
    for attempt in range(3):
        try:
            r = client.images.generate(model="gpt-image-2", prompt=SHOTS[shot](s),
                                       size=SIZE[shot], quality="medium", n=1)
            out.write_bytes(base64.b64decode(r.data[0].b64_json))
            return (iid, "ok", out.stat().st_size)
        except Exception as e:
            last = str(e)[:160]
            time.sleep(3 * (attempt + 1))
    return (iid, "ERR:" + (last or "?"), 0)


def main():
    wanted = set(sys.argv[1:])  # match set id (all 3 shots) or exact "<id>_<shot>"
    jobs = []
    for s in SETS:
        for shot in SHOTS:
            iid = f"{s['id']}_{shot}"
            if not wanted or s["id"] in wanted or iid in wanted:
                jobs.append((s, shot))
    print(f"generating {len(jobs)} starter-set shots (skipping existing) -> {OUT}/ ...")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gen, j): j for j in jobs}
        for fut in as_completed(futs):
            iid, status, sz = fut.result()
            print(f"  {iid:24s} {status:14s} {sz}")
            results.append((iid, status))
    ok = sum(1 for _, st in results if st in ("ok", "skip"))
    print(f"done: {ok}/{len(results)} present")
    bad = [iid for iid, st in results if st.startswith("ERR")]
    if bad:
        print("FAILED:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
