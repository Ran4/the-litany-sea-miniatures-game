"""
Shared helpers for the Litany Sea lore-video pipeline (stdlib only — safe to import
from any of the uv inline-script stages).

Layout (per faction, e.g. "mnemarchs"):
  lore_videos/storyboards/<faction>.json   <- the creative content (scenes)
  lore_videos/build/<faction>/audio/*.mp3  <- per-scene narration (gen_narration.py)
  lore_videos/build/<faction>/scenes/*.png <- per-scene art      (gen_scene_images.py)
  lore_videos/build/<faction>/music/bed.wav<- ambient bed        (gen_music.py)
  lore_videos/build/<faction>/timeline.json<- per-scene audio durations
  lore_videos/build/<faction>/captions.ass <- burned-in captions
  lore_videos/<faction>.mp4                 <- final deliverable  (build_video.py)
"""
import os, re, json, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent      # lore_videos/
ROOT = HERE.parent                                   # project root

# The grave, measured British narrator (ElevenLabs premade "Daniel"); ~157 wpm.
DEFAULT_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"
DEFAULT_TTS_MODEL = "eleven_multilingual_v2"

CAPTION_FONT = "EB Garamond"   # classical serif, present on this machine


def env(key):
    """Read a key from the project-root .env (falling back to the environment)."""
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key)


def paths(faction):
    b = HERE / "build" / faction
    return {
        "storyboard": HERE / "storyboards" / f"{faction}.json",
        "build": b,
        "audio": b / "audio",
        "scenes": b / "scenes",
        "clips": b / "clips",
        "music": b / "music" / "bed.wav",
        "timeline": b / "timeline.json",
        "ass": b / "captions.ass",
        "narration": b / "narration.wav",
        "out": HERE / f"{faction}.mp4",
    }


def load_storyboard(faction):
    p = paths(faction)["storyboard"]
    if not p.exists():
        raise SystemExit(f"storyboard not found: {p}\n(run the lore workflow first, or check the faction name)")
    sb = json.loads(p.read_text(encoding="utf-8"))
    scenes = sb.get("scenes", [])
    if not scenes:
        raise SystemExit(f"storyboard {p} has no scenes")
    return sb


def load_timeline(faction):
    p = paths(faction)["timeline"]
    if not p.exists():
        raise SystemExit(f"timeline not found: {p}\n(run gen_narration.py first)")
    return json.loads(p.read_text(encoding="utf-8"))


def ffprobe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)])
    return float(out.decode().strip())


def run(cmd, quiet=False):
    if not quiet:
        printable = " ".join(str(c) for c in cmd)
        print("  $ " + (printable[:240] + (" …" if len(printable) > 240 else "")))
    subprocess.run([str(c) for c in cmd], check=True)


def word_count(text):
    return len(text.split())


# ---- captions ---------------------------------------------------------------

_SENT_RE = re.compile(r"[^.!?…]+[.!?…]+|\S+\s*$")


def split_sentences(text):
    text = " ".join(text.split())
    parts = [s.strip() for s in _SENT_RE.findall(text) if s.strip()]
    return parts or [text]


def split_captions(text, max_words=9, max_chars=48):
    """Break narration into short on-screen caption lines at sentence/word boundaries."""
    caps = []
    for sent in split_sentences(text):
        words = sent.split()
        cur = []
        for w in words:
            trial = cur + [w]
            if cur and (len(trial) > max_words or len(" ".join(trial)) > max_chars):
                caps.append(" ".join(cur))
                cur = [w]
            else:
                cur = trial
        if cur:
            caps.append(" ".join(cur))
    return caps


def _ass_time(t):
    if t < 0:
        t = 0
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, c = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{c:02d}"


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00F2F2F2,&H00FFFFFF,&H00141008,&H64000000,0,0,0,0,100,100,0.6,0,1,3,2,2,140,140,82,1
Style: Chapter,{font},58,&H00DFEFE9,&H00FFFFFF,&H00141008,&H64000000,0,1,0,0,100,100,1.5,0,1,2,3,8,80,80,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass(scene_times, ass_path, font=CAPTION_FONT, fontsize=46, chapter_marks=True):
    """
    scene_times: list of {start, dur, narration, chapter, first_in_chapter}
    Captions are timed within each scene proportionally to caption character length.
    Chapter titles fade in briefly at the start of each new chapter (top-center).
    """
    lines = [ASS_HEADER.format(font=font, size=fontsize)]
    for sc in scene_times:
        caps = split_captions(sc["narration"])
        if not caps:
            continue
        weights = [max(6, len(c)) for c in caps]
        total = sum(weights)
        t = sc["start"]
        gap = 0.04  # tiny breath between caption lines
        for c, w in zip(caps, weights):
            seg = max(0.7, sc["dur"] * w / total)
            start, end = t, t + seg - gap
            t += seg
            txt = c.replace("{", "(").replace("}", ")").strip()
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{txt}")
        if chapter_marks and sc.get("first_in_chapter") and sc.get("chapter"):
            cs = sc["start"]
            ce = sc["start"] + min(3.2, max(2.0, sc["dur"] * 0.6))
            title = sc["chapter"].upper().replace("{", "(").replace("}", ")")
            fade = r"{\fad(600,600)}"
            lines.append(f"Dialogue: 1,{_ass_time(cs)},{_ass_time(ce)},Chapter,,0,0,0,,{fade}{title}")
    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ass_path
