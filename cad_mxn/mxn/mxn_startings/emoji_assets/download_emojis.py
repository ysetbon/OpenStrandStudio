"""Download 50 animal emoji PNGs at high resolution for all 4 emoji sets.

Sources and resolutions:
  - OpenMoji:      618x618 from GitHub (resized to 512)
  - Twemoji:       72x72 SVG rendered to 512 via cairosvg
  - Noto Emoji:    512x512 from Google GitHub (replaces JoyPixels)
  - Fluent Emoji:  256x256 from Microsoft GitHub
"""
import os
import sys
import urllib.request
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow..."); os.system(f'"{sys.executable}" -m pip install Pillow --quiet')
    from PIL import Image

CODES = [
    "1f436", "1f431", "1f42d", "1f430", "1f994",
    "1f98a", "1f43b", "1f43c", "1f428", "1f42f",
    "1f981", "1f42e", "1f437", "1f438", "1f435",
    "1f414", "1f427", "1f426", "1f424", "1f986",
    "1f989", "1f987", "1f43a", "1f417", "1f434",
    "1f984", "1f41d", "1f41b", "1f98b", "1f40c",
    "1f41e", "1f422", "1f40d", "1f98e", "1f996",
    "1f995", "1f419", "1f991", "1f990", "1f99e",
    "1f980", "1f421", "1f420", "1f41f", "1f42c",
    "1f433", "1f40a", "1f993", "1f992", "1f9ac",
]

# Fluent Emoji: codepoint -> (folder_name, file_name)
# Pattern: https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/{Folder}/3D/{file}_3d.png
FLUENT_MAP = {
    "1f436": ("Dog face", "dog_face"),
    "1f431": ("Cat face", "cat_face"),
    "1f42d": ("Mouse face", "mouse_face"),
    "1f430": ("Rabbit face", "rabbit_face"),
    "1f994": ("Hedgehog", "hedgehog"),
    "1f98a": ("Fox", "fox"),
    "1f43b": ("Bear", "bear"),
    "1f43c": ("Panda", "panda"),
    "1f428": ("Koala", "koala"),
    "1f42f": ("Tiger face", "tiger_face"),
    "1f981": ("Lion", "lion"),
    "1f42e": ("Cow face", "cow_face"),
    "1f437": ("Pig face", "pig_face"),
    "1f438": ("Frog", "frog"),
    "1f435": ("Monkey face", "monkey_face"),
    "1f414": ("Chicken", "chicken"),
    "1f427": ("Penguin", "penguin"),
    "1f426": ("Bird", "bird"),
    "1f424": ("Baby chick", "baby_chick"),
    "1f986": ("Duck", "duck"),
    "1f989": ("Owl", "owl"),
    "1f987": ("Bat", "bat"),
    "1f43a": ("Wolf", "wolf"),
    "1f417": ("Boar", "boar"),
    "1f434": ("Horse face", "horse_face"),
    "1f984": ("Unicorn", "unicorn"),
    "1f41d": ("Honeybee", "honeybee"),
    "1f41b": ("Bug", "bug"),
    "1f98b": ("Butterfly", "butterfly"),
    "1f40c": ("Snail", "snail"),
    "1f41e": ("Lady beetle", "lady_beetle"),
    "1f422": ("Turtle", "turtle"),
    "1f40d": ("Snake", "snake"),
    "1f98e": ("Lizard", "lizard"),
    "1f996": ("T-Rex", "t-rex"),
    "1f995": ("Sauropod", "sauropod"),
    "1f419": ("Octopus", "octopus"),
    "1f991": ("Squid", "squid"),
    "1f990": ("Shrimp", "shrimp"),
    "1f99e": ("Lobster", "lobster"),
    "1f980": ("Crab", "crab"),
    "1f421": ("Blowfish", "blowfish"),
    "1f420": ("Tropical fish", "tropical_fish"),
    "1f41f": ("Fish", "fish"),
    "1f42c": ("Dolphin", "dolphin"),
    "1f433": ("Spouting whale", "spouting_whale"),
    "1f40a": ("Crocodile", "crocodile"),
    "1f993": ("Zebra", "zebra"),
    "1f992": ("Giraffe", "giraffe"),
    "1f9ac": ("Bison", "bison"),
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_SIZE = 512  # All sets will be saved at this resolution


def download_bytes(url):
    """Download raw bytes from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def save_png(data, dest_path, target_size=TARGET_SIZE):
    """Load PNG from bytes, resize to target_size, save."""
    img = Image.open(BytesIO(data))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if img.width != target_size or img.height != target_size:
        img = img.resize((target_size, target_size), Image.LANCZOS)
    img.save(dest_path, "PNG")


def download_set(name, out_dir, url_fn):
    """Download all 50 emojis for one set using url_fn(code) -> url."""
    os.makedirs(out_dir, exist_ok=True)
    ok = fail = skip = 0
    for code in CODES:
        dest = os.path.join(out_dir, f"{code}.png")
        if os.path.exists(dest) and os.path.getsize(dest) > 2000:
            skip += 1
            continue
        url = url_fn(code)
        if url is None:
            fail += 1
            print(f"  [{name}] {code}.png SKIP (no URL mapping)")
            continue
        try:
            data = download_bytes(url)
            save_png(data, dest)
            ok += 1
            print(f"  [{name}] {code}.png OK")
        except Exception as e:
            fail += 1
            print(f"  [{name}] {code}.png FAILED: {e}")
    print(f"  [{name}] Done: {ok} downloaded, {skip} already existed, {fail} failed")
    return fail


def download_twemoji_svg_set(out_dir):
    """Download Twemoji SVGs and render to high-res PNGs."""
    os.makedirs(out_dir, exist_ok=True)

    try:
        import cairosvg
        # Test that it actually works (cairo native lib must be available)
        cairosvg.svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', output_width=1, output_height=1)
        has_cairo = True
    except Exception:
        has_cairo = False

    if not has_cairo:
        print("  [twemoji] cairosvg not available. Downloading 72px PNGs (best available without cairo).")
        return download_set("twemoji", out_dir,
            lambda code: f"https://raw.githubusercontent.com/jdecked/twemoji/main/assets/72x72/{code}.png")

    ok = fail = skip = 0
    for code in CODES:
        dest = os.path.join(out_dir, f"{code}.png")
        if os.path.exists(dest) and os.path.getsize(dest) > 2000:
            skip += 1
            continue
        url = f"https://raw.githubusercontent.com/jdecked/twemoji/main/assets/svg/{code}.svg"
        try:
            svg_data = download_bytes(url)
            png_data = cairosvg.svg2png(bytestring=svg_data,
                                         output_width=TARGET_SIZE,
                                         output_height=TARGET_SIZE)
            img = Image.open(BytesIO(png_data))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(dest, "PNG")
            ok += 1
            print(f"  [twemoji] {code}.png OK (SVG->{TARGET_SIZE}px)")
        except Exception as e:
            fail += 1
            print(f"  [twemoji] {code}.png FAILED: {e}")
    print(f"  [twemoji] Done: {ok} downloaded, {skip} already existed, {fail} failed")
    return fail


def main():
    total_fail = 0

    # 1. OpenMoji 618x618 (resized to TARGET_SIZE)
    print(f"=== OpenMoji (618->{TARGET_SIZE}px) ===")
    total_fail += download_set("openmoji",
        os.path.join(BASE_DIR, "openmoji_72"),
        lambda code: f"https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/618x618/{code.upper()}.png")

    # 2. Twemoji SVG → high-res PNG
    print(f"\n=== Twemoji (SVG->{TARGET_SIZE}px) ===")
    total_fail += download_twemoji_svg_set(os.path.join(BASE_DIR, "twemoji_72"))

    # 3. Noto Emoji 512x512 (replaces JoyPixels which requires paid license)
    print(f"\n=== Noto Emoji (Google) 512px ===")
    total_fail += download_set("noto/joypixels",
        os.path.join(BASE_DIR, "joypixels_72"),
        lambda code: f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/512/emoji_u{code}.png")

    # 4. Fluent Emoji 256x256 (resized to TARGET_SIZE)
    print(f"\n=== Fluent Emoji (Microsoft) (256->{TARGET_SIZE}px) ===")
    def fluent_url(code):
        entry = FLUENT_MAP.get(code)
        if not entry:
            return None
        folder, fname = entry
        return f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/{folder.replace(' ', '%20')}/3D/{fname}_3d.png"
    total_fail += download_set("fluent",
        os.path.join(BASE_DIR, "fluent_emoji"),
        fluent_url)

    print(f"\n{'='*50}")
    if total_fail > 0:
        print(f"{total_fail} total failures.")
    else:
        print("All 200 emoji assets downloaded successfully!")


if __name__ == "__main__":
    main()
