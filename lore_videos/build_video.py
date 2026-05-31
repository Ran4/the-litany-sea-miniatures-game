# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Assemble the final lore video from the generated assets.

Inputs (per faction):
  storyboards/<faction>.json        scenes (narration, image_prompt, chapter)
  build/<faction>/audio/<id>.mp3     narration  (gen_narration.py)
  build/<faction>/scenes/<id>.png    plates     (gen_scene_images.py)
  build/<faction>/music/bed.wav      ambient    (gen_music.py)  [optional]
Output:
  lore_videos/<faction>.mp4

Pipeline:
  Pass A  per-scene Ken Burns clip (slow zoom/pan), 1920x1080@30, cached by image mtime.
  Pass B  one ffmpeg graph: xfade cross-dissolves between clips + burned-in EB Garamond
          captions (+ chapter titles) + narration over a ducked ambient bed.

Audio/video stay in lock-step: each scene's video length is its (freshly probed) narration
length + one crossfade, and the xfade offsets are chosen so scene i's narration begins exactly
as its plate dissolves in.

Usage:  uv run build_video.py [faction] [--limit N] [--force]
"""
import sys, json, subprocess, shutil
import common

FACTION = sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].startswith("--")) else "mnemarchs"
LIMIT = None
FORCE = "--force" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--limit" and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

FPS = 30
XFADE = 0.8          # crossfade seconds between scenes
W, H = 1920, 1080

# Ken Burns presets: (zoom0, zoom1, cx0, cy0, cx1, cy1); centers are fractions [0,1].
KB = [
    (1.00, 1.10, 0.50, 0.55, 0.50, 0.42),   # push in, drift up
    (1.11, 1.00, 0.38, 0.45, 0.60, 0.50),   # pull out, drift right
    (1.03, 1.13, 0.62, 0.50, 0.42, 0.56),   # push in, drift left
    (1.12, 1.02, 0.50, 0.60, 0.50, 0.40),   # pull out, rise
    (1.00, 1.09, 0.35, 0.52, 0.55, 0.48),   # push in, drift right
    (1.06, 1.14, 0.50, 0.36, 0.50, 0.58),   # push in, sink down
]


def ken_burns_clip(img, out, length, idx):
    if out.exists() and not FORCE and out.stat().st_mtime >= img.stat().st_mtime:
        return "skip"
    frames = max(2, round(length * FPS))
    z0, z1, cx0, cy0, cx1, cy1 = KB[idx % len(KB)]
    z = f"{z0:.4f}+({z1 - z0:.4f})*on/{frames}"
    x = f"(iw-iw/zoom)*({cx0:.4f}+({cx1 - cx0:.4f})*on/{frames})"
    y = f"(ih-ih/zoom)*({cy0:.4f}+({cy1 - cy0:.4f})*on/{frames})"
    vf = (f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    common.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", img,
                "-filter_complex", vf, "-c:v", "libx264", "-preset", "fast",
                "-crf", "19", "-r", str(FPS), "-t", f"{length:.3f}", out], quiet=True)
    return "ok"


def decode_narration(mp3, wav):
    if not (wav.exists() and not FORCE and wav.stat().st_mtime >= mp3.stat().st_mtime):
        common.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp3,
                    "-ar", "44100", "-ac", "2", wav], quiet=True)
    return common.ffprobe_duration(wav)


def main():
    sb = common.load_storyboard(FACTION)
    p = common.paths(FACTION)
    scenes = sb["scenes"][:LIMIT] if LIMIT else sb["scenes"]
    n = len(scenes)
    for d in ("clips", "audio", "scenes"):
        (p["build"] / d).mkdir(parents=True, exist_ok=True)

    # ---- check assets ----
    missing = []
    for s in scenes:
        if not (p["scenes"] / f"{s['id']}.png").exists():
            missing.append(f"image {s['id']}")
        if not (p["audio"] / f"{s['id']}.mp3").exists():
            missing.append(f"audio {s['id']}")
    if missing:
        raise SystemExit("missing assets (run gen_scene_images.py / gen_narration.py):\n  "
                         + "\n  ".join(missing))

    # ---- Pass 0: decode narration to wav, get authoritative durations ----
    print(f"[{FACTION}] preparing {n} scenes …")
    durs, wavs, clips = [], [], []
    for i, s in enumerate(scenes):
        sid = s["id"]
        wav = p["clips"] / f"{sid}.nar.wav"
        a = decode_narration(p["audio"] / f"{sid}.mp3", wav)
        durs.append(a)
        wavs.append(wav)

    # ---- Pass A: Ken Burns clips ----
    for i, s in enumerate(scenes):
        sid = s["id"]
        clip = p["clips"] / f"{sid}.mp4"
        st = ken_burns_clip(p["scenes"] / f"{sid}.png", clip, durs[i] + XFADE, i)
        clips.append(clip)
        print(f"  KB {i+1:2d}/{n}  {sid:20s} {durs[i]:5.2f}s  [{st}]")

    # ---- narration concat (PCM, no drift) ----
    listfile = p["build"] / "narration_list.txt"
    listfile.write_text("".join(f"file '{w.as_posix()}'\n" for w in wavs), encoding="utf-8")
    common.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
                "-safe", "0", "-i", listfile, "-ar", "44100", "-ac", "2", p["narration"]], quiet=True)

    # ---- captions (timeline = cumulative narration durations) ----
    scene_times, t = [], 0.0
    seen_ch = set()
    for i, s in enumerate(scenes):
        ch = s.get("chapter", "")
        scene_times.append({"start": t, "dur": durs[i], "narration": s["narration"],
                            "chapter": ch, "first_in_chapter": ch not in seen_ch})
        seen_ch.add(ch)
        t += durs[i]
    common.build_ass(scene_times, p["ass"])

    # ---- total video length (xfade chain) ----
    total_v = sum(d + XFADE for d in durs) - (n - 1) * XFADE   # = sum(durs) + XFADE
    print(f"[{FACTION}] narration {t/60:.1f} min; video {total_v/60:.1f} min ({n} scenes)")

    have_music = p["music"].exists()
    if not have_music:
        print("  ! no music bed (run gen_music.py); building without music")

    # ---- Pass B: one big ffmpeg graph ----
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-i", str(p["narration"])]                       # input n
    nar_idx = n
    if have_music:
        cmd += ["-i", str(p["music"])]                       # input n+1
    fc = []
    # normalize each clip stream
    for i in range(n):
        fc.append(f"[{i}:v]fps={FPS},settb=AVTB,setsar=1,format=yuv420p[c{i}]")
    # xfade chain
    if n == 1:
        fc.append("[c0]null[vx]")
    else:
        cum = durs[0] + XFADE
        prev = "c0"
        for i in range(1, n):
            off = cum - XFADE
            out = "vx" if i == n - 1 else f"x{i}"
            fc.append(f"[{prev}][c{i}]xfade=transition=fade:duration={XFADE}:offset={off:.3f}[{out}]")
            cum += (durs[i] + XFADE) - XFADE
            prev = out
    # global fades + burn captions
    ass_path = p["ass"].as_posix().replace(":", r"\:").replace("'", r"\'")
    fc.append(f"[vx]fade=t=in:st=0:d=1.0,fade=t=out:st={total_v-1.6:.3f}:d=1.6,"
              f"ass='{ass_path}'[vout]")
    # audio: narration + ducked music.
    # Pad narration and trim music to the SAME length (total_v) so sidechaincompress
    # never sees one input EOF before the other (ffmpeg 4.4 errors otherwise).
    afmt = "aformat=sample_fmts=fltp:channel_layouts=stereo:sample_rates=44100"
    if have_music:
        fc.append(f"[{nar_idx}:a]aresample=44100,apad=pad_dur=4,atrim=0:{total_v:.3f},"
                  f"asetpts=PTS-STARTPTS,{afmt},asplit=2[nar][narsc]")
        fc.append(f"[{n+1}:a]aresample=44100,atrim=0:{total_v:.3f},asetpts=PTS-STARTPTS,"
                  f"volume=0.42,{afmt}[mus]")
        fc.append("[mus][narsc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=500[musd]")
        fc.append("[nar][musd]amix=inputs=2:normalize=0:dropout_transition=0[amx]")
        fc.append(f"[amx]afade=t=in:st=0:d=1.0,afade=t=out:st={total_v-2.0:.3f}:d=2.0,"
                  f"alimiter=limit=0.95[aout]")
    else:
        fc.append(f"[{nar_idx}:a]aresample=44100,apad=pad_dur=4,atrim=0:{total_v:.3f},"
                  f"asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,"
                  f"afade=t=out:st={total_v-2.0:.3f}:d=2.0[aout]")

    cmd += ["-filter_complex", ";".join(fc),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-r", str(FPS),
            "-t", f"{total_v:.3f}", "-movflags", "+faststart", str(p["out"])]
    print(f"[{FACTION}] assembling -> {p['out'].name}  (this is the long render)")
    common.run(cmd)

    dur = common.ffprobe_duration(p["out"])
    size = p["out"].stat().st_size / 1e6
    print(f"[{FACTION}] DONE  {p['out']}  {dur/60:.1f} min  {size:.1f} MB")


if __name__ == "__main__":
    main()
