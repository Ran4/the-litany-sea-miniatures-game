# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Generate gpt-image-2 illustrations from images_prompts.json -> assets/<id>.png
Threaded, with retries. Skips images that already exist (so reruns are cheap).
Usage: uv run gen_images.py
"""
import os, json, base64, pathlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ASSETS.mkdir(exist_ok=True)


def load_key():
    for line in open(HERE / ".env"):
        if line.strip().startswith("OPENAI_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no OPENAI_API_KEY in .env")


from openai import OpenAI
client = OpenAI(api_key=load_key())

with open(HERE / "images_prompts.json", encoding="utf-8") as fh:
    IMAGES = json.load(fh)


def gen(img):
    iid = img["id"]
    out = ASSETS / f"{iid}.png"
    if out.exists() and out.stat().st_size > 5000:
        return (iid, "skip", out.stat().st_size)
    size = img.get("size", "1024x1024")
    quality = img.get("quality", "medium")
    prompt = img["prompt"]
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
    todo = [i for i in IMAGES]
    print(f"generating {len(todo)} images (skipping existing)...")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gen, i): i["id"] for i in todo}
        for f in as_completed(futs):
            iid, status, sz = f.result()
            print(f"  {iid:14s} {status:12s} {sz}")
            results.append((iid, status))
    ok = sum(1 for _, s in results if s in ("ok", "skip"))
    print(f"done: {ok}/{len(results)} present")
    bad = [iid for iid, s in results if s.startswith("ERR")]
    if bad:
        print("FAILED:", bad)


if __name__ == "__main__":
    main()
