# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Render a whole lore video end to end:  uv run render.py [faction]   (default: mnemarchs)

Runs the four stages in order (each is also runnable on its own):
  1. gen_narration.py     ElevenLabs TTS  -> build/<faction>/audio + timeline.json
  2. gen_scene_images.py  gpt-image-2 art -> build/<faction>/scenes
  3. gen_music.py         ambient bed     -> build/<faction>/music/bed.wav
  4. build_video.py       assemble        -> lore_videos/<faction>.mp4

Stages 1-3 skip work that already exists, so re-running is cheap. Needs OPENAI_API_KEY
and ELEVENLABS_API_KEY in ../.env. Pass --skip-assets to only re-assemble.
"""
import sys, subprocess
import common

FACTION = "mnemarchs"
for a in sys.argv[1:]:
    if not a.startswith("--"):
        FACTION = a
SKIP_ASSETS = "--skip-assets" in sys.argv


def stage(script, *args):
    print(f"\n=== {script} {' '.join(args)} ===")
    subprocess.run(["uv", "run", str(common.HERE / script), FACTION, *args], check=True)


def main():
    common.load_storyboard(FACTION)   # fail early if the storyboard is missing
    if not SKIP_ASSETS:
        stage("gen_narration.py")
        stage("gen_scene_images.py")
        stage("gen_music.py")
    stage("build_video.py")
    print(f"\n✓ {FACTION}.mp4 ready in lore_videos/")


if __name__ == "__main__":
    main()
