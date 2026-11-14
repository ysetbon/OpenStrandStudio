# The OpenStrand Studio site

The public site on GitHub Pages, in the app's own look (the canvas grid, the toolbar's
buttons, the strands' black outlines):

| Address | What | Where it comes from |
|---|---|---|
| `https://ysetbon.github.io/OpenStrandStudio/` | The home page | `site/index.html` |
| `…/release/` | The latest release: downloads and what is new | `site/release/index.html`, filled from `site/release/releases.json` |
| `…/gallery/` | Designs that AI models made | `gallery/` (`gallery/README.md`) |

The pages load nothing from anywhere else: no fonts, trackers or scripts from other sites.

## Set it up (once)

On GitHub: **Settings > Pages > Build and deployment > Source: GitHub Actions**. From then
on the *Site* workflow (`.github/workflows/site.yml`) puts the site online whenever `site/`
or `gallery/` changes on `main`. Its run shows the address.

## For each release

Edit `site/release/releases.json` and push it to `main`. Put the new release first:

```json
{
 "version": "2.2",
 "date": "2026-12-01",
 "downloads": {
  "windows": "https://github.com/ysetbon/OpenStrandStudio/releases/download/v2.2/OpenStrandStudioSetup_01_Dec_2026_2_2.exe",
  "macos": "https://github.com/ysetbon/OpenStrandStudio/releases/download/v2.2/OpenStrandStudio_2_2.pkg"
 },
 "notes": [
  {"title": "A new thing", "text": "What it does, in a sentence or two."}
 ]
}
```

- `version` is numbers and dots (`2.2`, `2.2.1`); `date` is `YYYY-MM-DD`.
- `downloads` are the installers' addresses in a GitHub release of this repository (upload
  them there first). Any other address is ignored. Leave one empty (`""`) and its button
  says there is no installer for this version yet.
- `notes` are the What's New bullets, in English (the ones in `scripts/make_release_files.py`).

The home page shows the first release's version on its button; the release page shows the
first release in full and folds the others under *Earlier versions*. An update check in the
app can read the same file: the first release's `version` is the latest one.

## Look at it before pushing

```bash
bash site/build.sh _site
```

```bash
python -m http.server 8000 --directory _site
```

Then open `http://localhost:8000/`. `build.sh` is what the workflow runs: it copies `site/`
and `gallery/` into one folder, with the README's screenshot and the app's icon.

## The files

- `index.html`, `release/index.html`: the two pages.
- `site.css`, `site.js`: their look, and the script that reads `releases.json`.
- `release/releases.json`: the releases, newest first.
- `img/weave.svg`: the weave on the home page. The screenshot and the icon are copied in by
  `build.sh` from `docs/readme/main_window.png` and `src/box_stitch.png`.
