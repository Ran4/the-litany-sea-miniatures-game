# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""
Synthesize a self-contained dark-ambient music bed -> build/<faction>/music/bed.wav.
No external/copyrighted audio: a low detuned drone cluster, a slow brine-wind rumble,
and sparse church-bell tolls (the Long Toll). Deterministic.

Length defaults to the narration total (from timeline.json) + tail, or pass seconds.

Usage:  uv run gen_music.py [faction] [seconds]
"""
import sys, json, wave, struct
import numpy as np
import common

FACTION = sys.argv[1] if len(sys.argv) > 1 else "mnemarchs"
SR = 44100


def seconds_for(faction):
    if len(sys.argv) > 2:
        return float(sys.argv[2])
    tl = common.paths(faction)["timeline"]
    if tl.exists():
        return json.loads(tl.read_text())["total_audio"] + 10.0
    return 660.0


def bell(fundamental, dur, rng):
    """One inharmonic church-bell strike (mono float32)."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    # church-bell partial ratios (hum, prime, tierce, quint, nominal, + upper)
    ratios = [0.5, 1.0, 1.19, 1.5, 2.0, 2.5, 2.66, 3.01, 4.0]
    amps   = [0.6, 1.0, 0.8, 0.5, 0.7, 0.3, 0.25, 0.2, 0.12]
    decays = [5.5, 6.0, 4.0, 3.0, 2.4, 1.6, 1.4, 1.1, 0.7]
    out = np.zeros(n, dtype=np.float32)
    for r, a, d in zip(ratios, amps, decays):
        f = fundamental * r * (1.0 + rng.uniform(-0.0015, 0.0015))
        env = np.exp(-t / d).astype(np.float32)
        out += (a * env * np.sin(2 * np.pi * f * t)).astype(np.float32)
    # soft strike attack
    atk = np.clip(t / 0.006, 0, 1).astype(np.float32)
    return out * atk


def main():
    secs = seconds_for(FACTION)
    n = int(secs * SR)
    t = np.arange(n, dtype=np.float32) / SR
    rng = np.random.default_rng(1701)
    L = np.zeros(n, dtype=np.float32)
    R = np.zeros(n, dtype=np.float32)

    # --- drone cluster (A minor-ish, very low), slightly different per channel ---
    drone_freqs = [55.0, 82.41, 110.0, 164.81]   # A1, E2, A2, E3
    drone_amps  = [0.30, 0.20, 0.16, 0.08]
    swell = (0.7 + 0.3 * np.sin(2 * np.pi * 0.018 * t + 0.4)).astype(np.float32)
    for f, a in zip(drone_freqs, drone_amps):
        L += a * swell * np.sin(2 * np.pi * (f * 0.9997) * t).astype(np.float32)
        R += a * swell * np.sin(2 * np.pi * (f * 1.0003) * t + 0.6).astype(np.float32)

    # --- brine-wind rumble: brown noise (integrated white), slow amplitude swell ---
    def wind(seed):
        w = np.random.default_rng(seed).standard_normal(n).astype(np.float32)
        b = np.cumsum(w).astype(np.float32)
        b -= np.cumsum(b) / np.arange(1, n + 1)        # remove slow DC drift
        b /= (np.max(np.abs(b)) + 1e-6)
        lfo = (0.5 + 0.5 * np.sin(2 * np.pi * 0.012 * t + 1.1)).astype(np.float32)
        return (b * lfo).astype(np.float32)
    L += 0.10 * wind(11)
    R += 0.10 * wind(23)

    # --- the Long Toll: sparse bells, alternating two grave notes ---
    notes = [98.0, 130.81]    # G2, C3
    period, jitter = 21.0, 2.5
    pos, k = 6.0, 0
    while pos < secs - 7:
        strike = bell(notes[k % 2] * (0.5 if k % 5 == 4 else 1.0), 7.5, rng)
        i0 = int(pos * SR)
        i1 = min(n, i0 + strike.size)
        seg = strike[: i1 - i0] * 0.5
        L[i0:i1] += seg * 0.95
        R[i0:i1] += seg * 0.95
        pos += period + rng.uniform(-jitter, jitter)
        k += 1

    # --- mix: soft-saturate, fades, normalize low (build_video ducks it further) ---
    def shape(x):
        x = np.tanh(x * 0.8).astype(np.float32)
        fin = np.clip(t / 4.0, 0, 1).astype(np.float32)
        fout = np.clip((secs - t) / 6.0, 0, 1).astype(np.float32)
        return x * fin * fout
    L, R = shape(L), shape(R)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-6)
    g = 0.72 / peak
    stereo = np.stack([L * g, R * g], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")

    out = common.paths(FACTION)["music"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"[{FACTION}] wrote {out.name}  {secs:.1f}s ambient bed (drone + brine-wind + {k} bell tolls)")


if __name__ == "__main__":
    main()
