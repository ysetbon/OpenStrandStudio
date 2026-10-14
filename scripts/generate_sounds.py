"""Generate OpenStrand Studio UI sound effects with the ElevenLabs Sound Effects API.

Three steps:

    python scripts/generate_sounds.py generate --raw sounds_raw --takes 4
    python scripts/generate_sounds.py process  --raw sounds_raw --out sounds_takes
    python scripts/generate_sounds.py pick     --takes-dir sounds_takes ui_click=2 drag_drop=1 ...

`generate` calls the API (skips takes that already exist), `process` trims each take
to its target length and writes 44.1 kHz 16-bit mono WAVs, and `pick` copies the chosen
take of each cue into src/sounds/<cue>.wav.

The API key is read from ELEVENLABS_API_KEY. When that variable is unset no key header is
sent, which is what you want behind a proxy that injects the key itself.

Requires ffmpeg on PATH and numpy.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

import numpy as np

API_URL = "https://api.elevenlabs.io/v1/sound-generation"
SAMPLE_RATE = 44100
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(REPO_ROOT, "src", "sounds")

# Every prompt shares one sound world so the cues feel like a family: the app is a dark
# graphite grid with flat candy-coloured pill buttons and strands drawn like plastic lacing
# cord (box stitch, braids). So: soft rounded plastic, cord and small craft parts, friendly
# and toy-like, close and dry. No metal, no electronic beeps, nothing harsh or sci-fi.
STYLE = "soft rounded plastic, playful and friendly, close-up, dry, no reverb, no music, no voice"

# id, target length (ms), target peak (dBFS), prompt (STYLE is appended)
CUES = [
    # Buttons: the flat coloured pill buttons
    ("ui_click", 50, -14, "One tiny click of a fingertip pressing a small smooth plastic toy button, short crisp tap with no tail"),
    ("ui_toggle_on", 80, -15, "A small plastic toggle switch flicked on, two quick light clicks going up in pitch, bright and tidy"),
    ("ui_toggle_off", 80, -15, "A small plastic toggle switch flicked off, two quick light clicks going down in pitch, a little softer and duller"),
    ("layer_select", 45, -16, "One tiny tick of a plastic bead tapped on a plastic tray, high and light, very short"),
    # Hover: barely there
    ("ui_hover", 30, -26, "An extremely faint tiny tick, a fingernail lightly brushing a plastic button, airy, almost silent, very short"),
    ("canvas_hover_point", 35, -24, "A very faint tiny bubbly blip, a small soft plastic bead touching another, gentle and high, very short"),
    # Modes: changing tool feels like turning a chunky toy selector
    ("mode_select", 110, -14, "A chunky plastic toy selector dial clicking into its next notch, one solid rounded click, satisfying and tight"),
    ("mode_move", 130, -19, "Sliding a small plastic game piece across a smooth board, a soft low gliding move that settles gently, warm and muffled, no high frequencies, no click"),
    ("mode_attach", 120, -14, "A small plastic buckle clip snapping shut, one crisp rounded snap"),
    # Drag and move: picking up and placing a strand end
    ("drag_pickup", 70, -15, "Lifting a small plastic game piece off a board, a soft short pluck with a slight upward lift"),
    ("drag_drop", 85, -14, "Placing a small plastic game piece down on a board, one soft muted thock, no bounce"),
    ("snap_grid", 25, -26, "An extremely short tiny dry tick, a single plastic ratchet tooth, very quiet"),
    # Attaching: a new strand pulled from an end and fixed on, the signature moment
    ("attach_start", 120, -15, "Pulling a plastic lacing cord through the hole of a bead, a quick stretchy rubbery pull that rises in pitch, like a cord being drawn out to attach it"),
    ("attach_complete", 150, -12, "Two plastic connector pieces pressed together until they lock, a firm satisfying snap with a tiny bright plink after it"),
    ("new_strand", 150, -14, "A fresh strand of plastic lacing cord flicked out from a spool, a springy bouncy boing with a cheerful rising twang, a new string appearing"),
    # Feedback
    ("delete", 150, -18, "A small crumpled plastic wrapper dropped into a small empty plastic trash bin, one soft hollow plunk at the bottom, muffled, no hiss"),
    ("undo", 90, -15, "Two quick round plastic boops stepping down in pitch, like a toy taking one step backwards, bouncy and clear"),
    ("redo", 90, -15, "Two quick round plastic boops stepping up in pitch, like a toy taking one step forwards, bouncy and clear"),
    ("save_done", 200, -14, "Two gentle wooden toy xylophone notes going up, warm and clear, a calm job-done confirmation"),
    ("denied", 100, -16, "A soft hollow bonk of a rubber toy mallet tapping a hollow plastic block, low and short, gentle, not alarming"),
]
CUE_BY_ID = {cue[0]: cue for cue in CUES}

# Low-pass cutoff (Hz) for cues whose takes come back too bright or hissy
LOWPASS = {"mode_move": 2500, "delete": 4500}



def generate(raw_dir, takes, only, prompt_influence):
    headers = {"Content-Type": "application/json", "Accept": "audio/mpeg"}
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if api_key:
        headers["xi-api-key"] = api_key

    for cue_id, _ms, _peak, prompt in CUES:
        if only and cue_id not in only:
            continue
        cue_dir = os.path.join(raw_dir, cue_id)
        os.makedirs(cue_dir, exist_ok=True)
        for take in range(1, takes + 1):
            path = os.path.join(cue_dir, f"take{take}.mp3")
            if os.path.exists(path):
                continue
            body = json.dumps({
                "text": f"{prompt}. {STYLE}",
                "duration_seconds": 0.5,  # API minimum; trimmed to the target length later
                "prompt_influence": prompt_influence,
            }).encode("utf-8")
            request = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    audio = response.read()
            except urllib.error.HTTPError as e:
                sys.exit(f"{cue_id} take {take}: HTTP {e.code} {e.read().decode('utf-8', 'replace')}")
            with open(path, "wb") as f:
                f.write(audio)
            print(f"generated {cue_id} take {take}")
            time.sleep(0.3)


def decode(path, lowpass=None):
    """Decode any audio file to mono float32 at SAMPLE_RATE, optionally low-passed."""
    filters = ["-af", f"lowpass=f={lowpass}:poles=2,lowpass=f={lowpass}:poles=2"] if lowpass else []
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, *filters, "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(pcm, dtype=np.float32).copy()


def shape(samples, target_ms, peak_db):
    """Trim leading silence, cut to target length with a smooth fade-out and normalize the peak."""
    if not samples.size or np.max(np.abs(samples)) == 0:
        return samples
    level = np.abs(samples)
    onset = int(np.argmax(level > 0.1 * level.max()))
    start = max(0, onset - int(0.002 * SAMPLE_RATE))
    length = int(target_ms / 1000 * SAMPLE_RATE)
    out = samples[start:start + length].astype(np.float64)

    fade_in = min(int(0.001 * SAMPLE_RATE), out.size)
    out[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    fade_out = min(max(int(0.005 * SAMPLE_RATE), out.size // 4), out.size)
    out[-fade_out:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, fade_out)))

    peak = np.max(np.abs(out))
    if peak > 0:
        out *= (10 ** (peak_db / 20)) / peak
    return out


def write_wav(path, samples):
    data = np.clip(np.round(samples * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(data.tobytes())


def process(raw_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for cue_id, ms, peak_db, _prompt in CUES:
        cue_dir = os.path.join(raw_dir, cue_id)
        if not os.path.isdir(cue_dir):
            continue
        for name in sorted(os.listdir(cue_dir)):
            if not name.endswith(".mp3"):
                continue
            take = name[len("take"):-len(".mp3")]
            shaped = shape(decode(os.path.join(cue_dir, name), LOWPASS.get(cue_id)), ms, peak_db)
            write_wav(os.path.join(out_dir, f"{cue_id}_{take}.wav"), shaped)
            print(f"processed {cue_id} take {take}")


def pick(takes_dir, choices):
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    for choice in choices:
        cue_id, _, take = choice.partition("=")
        if cue_id not in CUE_BY_ID or not take:
            sys.exit(f"bad choice {choice!r}, expected cue_id=take")
        src = os.path.join(takes_dir, f"{cue_id}_{take}.wav")
        shutil.copyfile(src, os.path.join(SOUNDS_DIR, f"{cue_id}.wav"))
        print(f"{cue_id}.wav <- take {take}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="call the ElevenLabs API")
    g.add_argument("--raw", default="sounds_raw")
    g.add_argument("--takes", type=int, default=4)
    g.add_argument("--only", nargs="*", help="cue ids to generate (default: all)")
    g.add_argument("--prompt-influence", type=float, default=0.7)

    p = sub.add_parser("process", help="trim raw takes into WAVs")
    p.add_argument("--raw", default="sounds_raw")
    p.add_argument("--out", default="sounds_takes")

    k = sub.add_parser("pick", help="copy chosen takes into src/sounds")
    k.add_argument("--takes-dir", default="sounds_takes")
    k.add_argument("choices", nargs="+", help="cue_id=take, e.g. ui_click=2")

    args = parser.parse_args()
    if args.command == "generate":
        generate(args.raw, args.takes, set(args.only or []), args.prompt_influence)
    elif args.command == "process":
        process(args.raw, args.out)
    else:
        pick(args.takes_dir, args.choices)


if __name__ == "__main__":
    main()
