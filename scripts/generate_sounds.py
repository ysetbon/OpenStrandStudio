"""Generate OpenStrand Studio UI sound effects with the ElevenLabs Sound Effects API.

Three steps:

    python scripts/generate_sounds.py generate --raw sounds_raw --takes 4
    python scripts/generate_sounds.py process  --raw sounds_raw --out sounds_takes
    python scripts/generate_sounds.py pick     --takes-dir sounds_takes ui_click=2 drag_drop=1 ...
    python scripts/generate_sounds.py variants

`generate` calls the API (skips takes that already exist), `process` trims each take
to its target length and writes 44.1 kHz 16-bit mono WAVs, and `pick` copies the chosen
take of each cue into src/sounds/<cue>.wav. `variants` derives the blue and green toggle
sounds from the approved ui_toggle sounds. `soften` takes the edge off one take
without changing its pitch.

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
    ("attach_start", 160, -17, "One quick soft paintbrush stroke across paper, a gentle bristly swish of a wide soft brush, smooth and light"),
    ("attach_complete", 150, -12, "Two plastic connector pieces pressed together until they lock, a firm satisfying snap with a tiny bright plink after it"),
    ("new_strand", 200, -14, "A tiny cheerful magical sparkle, a quick bright glint of something brand new appearing, a soft pop followed by a short shimmering rising chime"),
    # Feedback
    ("delete", 150, -18, "A small crumpled plastic wrapper dropped into a small empty plastic trash bin, one soft hollow plunk at the bottom, muffled, no hiss"),
    # undo and redo are built from bell_note retuned to exact notes (see TWO_NOTE)
    ("bell_note", 400, -15, "One single soft clear bell strike, a small toy glockenspiel bell struck once with a soft mallet, pure tone, short ring, one note only"),
    ("undo", 260, -15, "bell: C then E"),
    ("redo", 260, -15, "bell: E then C"),
    ("save_done", 200, -14, "Two gentle wooden toy xylophone notes going up, warm and clear, a calm job-done confirmation"),
    ("denied", 100, -16, "A soft hollow bonk of a rubber toy mallet tapping a hollow plastic block, low and short, gentle, not alarming"),
    # Sub-windows, menus and small controls
    ("dialog_open", 120, -18, "A small soft plastic lid flipping open, a gentle quick upward pop with a light airy lift"),
    ("dialog_close", 100, -19, "A small soft plastic lid gently closing, a quick soft downward tap shut"),
    ("menu_open", 60, -20, "A tiny soft flick of a small plastic card being fanned out, very quick and light"),
    ("stepper_tick", 45, -17, "A small firm tick of a plastic toy counter clicking forward one step, short and precise"),
    ("tab_switch", 80, -17, "A quick soft flip of a thick cardboard page in a children's board book, light and short"),
]
CUE_BY_ID = {cue[0]: cue for cue in CUES}

# Low-pass cutoff (Hz) for cues whose takes come back too bright or hissy
LOWPASS = {"mode_move": 2500, "delete": 4500, "attach_start": 4500}

# Cues that should not sound like plastic get their own style line
STYLE_OVERRIDE = {
    "new_strand": "playful and friendly, close-up, short, no music, no voice",
    "attach_start": "soft, gentle and warm, close-up, dry, no reverb, no music, no voice",
    "bell_note": "clean, close-up, dry, no reverb, no music, no voice",
    "tab_switch": "playful and friendly, close-up, dry, no reverb, no music, no voice",
}

# Pitch variants written next to each processed take: one recording, mirrored up and down
PITCH_VARIANTS = {"stepper_tick": [("stepper_plus", 2), ("stepper_minus", -2)]}

# Colour variants derived from approved sounds in src/sounds by the `variants` command,
# so every toggle of one colour plays the same file and colours differ only slightly
COLOR_VARIANTS = {
    "toggle_blue_on": ("ui_toggle_on", -2),
    "toggle_blue_off": ("ui_toggle_off", -2),
    "toggle_green_on": ("ui_toggle_on", 2),
    "toggle_green_off": ("ui_toggle_off", 2),
}

# Two-note cues built from one generated bell strike, retuned to exact pitches.
# A synthesized bell is added as an extra take so there is always a clean option.
NOTE_HZ = {"C6": 1046.50, "E6": 1318.51}
TWO_NOTE_SOURCE = "bell_note"
TWO_NOTE = {"undo": ("C6", "E6"), "redo": ("E6", "C6")}
NOTE_GAP_MS = 90



def generate(raw_dir, takes, only, prompt_influence):
    headers = {"Content-Type": "application/json", "Accept": "audio/mpeg"}
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if api_key:
        headers["xi-api-key"] = api_key

    for cue_id, _ms, _peak, prompt in CUES:
        if cue_id in TWO_NOTE or (only and cue_id not in only):
            continue
        cue_dir = os.path.join(raw_dir, cue_id)
        os.makedirs(cue_dir, exist_ok=True)
        for take in range(1, takes + 1):
            path = os.path.join(cue_dir, f"take{take}.mp3")
            if os.path.exists(path):
                continue
            body = json.dumps({
                "text": f"{prompt}. {STYLE_OVERRIDE.get(cue_id, STYLE)}",
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


def soften(samples, lowpass_hz, treble_db, attack_ms):
    """Take the edge off a sound without changing its pitch: a high-frequency cut
    plus a slower attack. Runs before shape(), which trims and normalizes."""
    filters = [f"treble=g={treble_db}:f=4000"] if treble_db else []
    if lowpass_hz:
        filters.append(f"lowpass=f={lowpass_hz}:poles=2")
    if filters:
        pcm = subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-",
             "-af", ",".join(filters), "-f", "f32le", "-"],
            input=samples.astype(np.float32).tobytes(), check=True, capture_output=True,
        ).stdout
        samples = np.frombuffer(pcm, dtype=np.float32).astype(np.float64)
    onset = int(np.argmax(np.abs(samples) > 0.1 * np.max(np.abs(samples))))
    ramp = int(attack_ms / 1000 * SAMPLE_RATE)
    if ramp:
        start = max(0, onset - int(0.002 * SAMPLE_RATE))
        end = min(samples.size, start + ramp)
        samples = samples.copy()
        samples[start:end] *= np.sin(np.linspace(0, np.pi / 2, end - start)) ** 2
    return samples


def write_wav(path, samples):
    data = np.clip(np.round(samples * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(data.tobytes())


def pitch_shift(samples, semitones):
    """Resample to shift pitch (and length) by the given number of semitones."""
    return retune(samples, 1.0, 2 ** (semitones / 12))


def strongest_pitch(samples):
    """Frequency of the loudest partial in the first 200 ms after the attack."""
    onset = int(np.argmax(np.abs(samples) > 0.1 * np.max(np.abs(samples))))
    window = samples[onset:onset + int(0.2 * SAMPLE_RATE)]
    window = window * np.hanning(window.size)
    spectrum = np.abs(np.fft.rfft(window, n=1 << 16))
    freqs = np.fft.rfftfreq(1 << 16, 1 / SAMPLE_RATE)
    band = (freqs > 300) & (freqs < 5000)
    return float(freqs[band][np.argmax(spectrum[band])])


def retune(samples, from_hz, to_hz):
    """Resample so the from_hz partial lands on to_hz."""
    factor = to_hz / from_hz
    positions = np.arange(0, samples.size - 1, factor)
    return np.interp(positions, np.arange(samples.size), samples)


def synth_bell(hz, seconds=0.35):
    """A soft glockenspiel-like strike: a few slightly inharmonic partials with fast decay."""
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    partials = [(1.0, 1.0, 9), (2.76, 0.35, 16), (5.40, 0.15, 24), (8.93, 0.06, 32)]
    tone = sum(a * np.sin(2 * np.pi * hz * r * t) * np.exp(-d * t) for r, a, d in partials)
    return tone * np.minimum(1.0, t / 0.002)


def two_notes(note_a, note_b, gap_ms):
    """Mix two strikes, the second starting gap_ms after the first."""
    gap = int(gap_ms / 1000 * SAMPLE_RATE)
    out = np.zeros(max(note_a.size, gap + note_b.size))
    out[:note_a.size] += note_a
    out[gap:gap + note_b.size] += note_b
    return out


def process_two_note(raw_dir, out_dir):
    src_dir = os.path.join(raw_dir, TWO_NOTE_SOURCE)
    takes = []
    for name in sorted(os.listdir(src_dir)):
        if name.endswith(".mp3"):
            strike = decode(os.path.join(src_dir, name)).astype(np.float64)
            onset = int(np.argmax(np.abs(strike) > 0.1 * np.max(np.abs(strike))))
            takes.append((name[len("take"):-len(".mp3")], strike[onset:], strongest_pitch(strike)))
    synth_take = str(len(takes) + 1)
    for cue_id, (first, second) in TWO_NOTE.items():
        _, ms, peak_db, _ = CUE_BY_ID[cue_id]
        for take, strike, hz in takes:
            mixed = two_notes(retune(strike, hz, NOTE_HZ[first]), retune(strike, hz, NOTE_HZ[second]), NOTE_GAP_MS)
            write_wav(os.path.join(out_dir, f"{cue_id}_{take}.wav"), shape(mixed, ms, peak_db))
            print(f"processed {cue_id} take {take} (bell at {hz:.0f} Hz -> {first} {second})")
        mixed = two_notes(synth_bell(NOTE_HZ[first]), synth_bell(NOTE_HZ[second]), NOTE_GAP_MS)
        write_wav(os.path.join(out_dir, f"{cue_id}_{synth_take}.wav"), shape(mixed, ms, peak_db))
        print(f"processed {cue_id} take {synth_take} (synthesized bell {first} {second})")


def process(raw_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for cue_id, ms, peak_db, _prompt in CUES:
        cue_dir = os.path.join(raw_dir, cue_id)
        if cue_id in TWO_NOTE or not os.path.isdir(cue_dir):
            continue
        for name in sorted(os.listdir(cue_dir)):
            if not name.endswith(".mp3"):
                continue
            take = name[len("take"):-len(".mp3")]
            shaped = shape(decode(os.path.join(cue_dir, name), LOWPASS.get(cue_id)), ms, peak_db)
            write_wav(os.path.join(out_dir, f"{cue_id}_{take}.wav"), shaped)
            print(f"processed {cue_id} take {take}")
            for name, semitones in PITCH_VARIANTS.get(cue_id, []):
                write_wav(os.path.join(out_dir, f"{name}_{take}.wav"), pitch_shift(shaped, semitones))
    if os.path.isdir(os.path.join(raw_dir, TWO_NOTE_SOURCE)):
        process_two_note(raw_dir, out_dir)


def pick(takes_dir, choices):
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    for choice in choices:
        cue_id, _, take = choice.partition("=")
        variant_names = {name for variants in PITCH_VARIANTS.values() for name, _ in variants}
        if (cue_id not in CUE_BY_ID and cue_id not in variant_names) or not take:
            sys.exit(f"bad choice {choice!r}, expected cue_id=take")
        # a cue with pitch variants ships as its variants, e.g. stepper_tick -> stepper_plus, stepper_minus
        names = [name for name, _ in PITCH_VARIANTS.get(cue_id, [])] or [cue_id]
        for name in names:
            shutil.copyfile(os.path.join(takes_dir, f"{name}_{take}.wav"), os.path.join(SOUNDS_DIR, f"{name}.wav"))
            print(f"{name}.wav <- take {take}")


def soften_take(raw_mp3, cue_id, out_path, lowpass_hz, treble_db, attack_ms, peak_db=None):
    """Write a softened version of one raw take, trimmed and normalized like process()."""
    _, ms, cue_peak, _ = CUE_BY_ID[cue_id]
    samples = soften(decode(raw_mp3).astype(np.float64), lowpass_hz, treble_db, attack_ms)
    write_wav(out_path, shape(samples, ms, cue_peak if peak_db is None else peak_db))


def variants():
    for name, (source, semitones) in COLOR_VARIANTS.items():
        samples = decode(os.path.join(SOUNDS_DIR, f"{source}.wav")).astype(np.float64)
        write_wav(os.path.join(SOUNDS_DIR, f"{name}.wav"), pitch_shift(samples, semitones))
        print(f"{name}.wav <- {source}.wav ({semitones:+d} semitones)")


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

    sub.add_parser("variants", help="derive colour variants from approved sounds in src/sounds")

    f = sub.add_parser("soften", help="soften one raw take: high cut and slower attack, same pitch")
    f.add_argument("raw_mp3")
    f.add_argument("cue_id")
    f.add_argument("out")
    f.add_argument("--lowpass", type=int, default=0, help="low-pass cutoff in Hz (0 = none)")
    f.add_argument("--treble", type=float, default=0, help="high-shelf gain in dB above 4 kHz, e.g. -6")
    f.add_argument("--attack-ms", type=float, default=0)
    f.add_argument("--peak", type=float, default=None, help="peak in dBFS (default: the cue's)")

    args = parser.parse_args()
    if args.command == "generate":
        generate(args.raw, args.takes, set(args.only or []), args.prompt_influence)
    elif args.command == "process":
        process(args.raw, args.out)
    elif args.command == "soften":
        soften_take(args.raw_mp3, args.cue_id, args.out, args.lowpass, args.treble, args.attack_ms, args.peak)
    elif args.command == "pick":
        pick(args.takes_dir, args.choices)
    else:
        variants()


if __name__ == "__main__":
    main()
