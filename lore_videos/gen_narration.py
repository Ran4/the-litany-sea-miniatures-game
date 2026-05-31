# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Synthesize per-scene narration with ElevenLabs -> build/<faction>/audio/<id>.mp3,
then probe durations into build/<faction>/timeline.json.

Skips scenes whose mp3 already exists (so reruns are cheap; delete a file to redo it).
Scenes are stitched with previous_text / next_text so the narrator's prosody flows
across scene cuts.

Usage:  uv run gen_narration.py [faction]   (default: mnemarchs)
Needs ELEVENLABS_API_KEY in ../.env (text-to-speech permission).
"""
import sys, json, time, urllib.request, urllib.error
import common

FACTION = sys.argv[1] if len(sys.argv) > 1 else "mnemarchs"

VOICE_ID = common.env("ELEVEN_VOICE_ID") or common.DEFAULT_VOICE_ID
MODEL_ID = common.env("ELEVEN_MODEL_ID") or common.DEFAULT_TTS_MODEL
VOICE_SETTINGS = {
    "stability": 0.50,        # measured, consistent — not theatrical
    "similarity_boost": 0.80,
    "style": 0.0,             # grave, neutral read
    "use_speaker_boost": True,
}


def synth(text, prev_text, next_text, out_path):
    key = common.env("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("no ELEVENLABS_API_KEY in ../.env")
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
           f"?output_format=mp3_44100_128")
    body = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
        "previous_text": prev_text or None,
        "next_text": next_text or None,
    }
    data = json.dumps(body).encode("utf-8")
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                audio = r.read()
            if len(audio) < 1000:
                raise RuntimeError(f"suspiciously small audio ({len(audio)} bytes)")
            out_path.write_bytes(audio)
            return len(audio)
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore")[:200]
            if e.code == 429:  # rate limited
                time.sleep(5 * (attempt + 1)); continue
            raise SystemExit(f"ElevenLabs HTTP {e.code}: {msg}")
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def main():
    sb = common.load_storyboard(FACTION)
    p = common.paths(FACTION)
    p["audio"].mkdir(parents=True, exist_ok=True)
    scenes = sb["scenes"]
    print(f"[{FACTION}] narrating {len(scenes)} scenes  voice={VOICE_ID} model={MODEL_ID}")

    timeline = {"faction": FACTION, "voice_id": VOICE_ID, "model": MODEL_ID, "scenes": []}
    total = 0.0
    for i, sc in enumerate(scenes):
        sid = sc["id"]
        out = p["audio"] / f"{sid}.mp3"
        text = " ".join(sc["narration"].split())
        if not (out.exists() and out.stat().st_size > 1000):
            prev_t = scenes[i - 1]["narration"] if i > 0 else ""
            next_t = scenes[i + 1]["narration"] if i + 1 < len(scenes) else ""
            n = synth(text, prev_t, next_t, out)
            tag = f"ok {n} bytes"
        else:
            tag = "skip"
        dur = common.ffprobe_duration(out)
        total += dur
        wc = common.word_count(text)
        timeline["scenes"].append({"id": sid, "words": wc, "dur": round(dur, 3)})
        print(f"  {i+1:2d}/{len(scenes)}  {sid:20s} {dur:6.2f}s  {wc:3d}w  {tag}")

    timeline["total_audio"] = round(total, 3)
    timeline["total_words"] = sum(s["words"] for s in timeline["scenes"])
    p["timeline"].parent.mkdir(parents=True, exist_ok=True)
    p["timeline"].write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    wpm = timeline["total_words"] / (total / 60) if total else 0
    print(f"[{FACTION}] total narration {total/60:.1f} min  "
          f"({timeline['total_words']} words, {wpm:.0f} wpm) -> {p['timeline'].name}")


if __name__ == "__main__":
    main()
