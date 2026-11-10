# OpenStrand Studio gallery

A public page of designs that AI models made in OpenStrand Studio, on GitHub Pages. It is
separate from the share inbox (`cloudflare/share-worker`), which stays private.

## What can be shown, and what never is

A design reaches this folder only when all of these hold:

1. The person said yes to sharing with you, and then yes again to the gallery (a second
   question in the app, and its own box in *Settings > Models*).
2. The model made the design from nothing of theirs: the request read no canvas, tab or
   past step of the person's.
3. The request worked.
4. You looked at it and ran `publish` for it yourself.

What goes up is a cleaned copy, never the share itself:

| Shown | Never shown |
|---|---|
| The design, with its groups renamed `Group 1`, `Group 2`… | The model's answer |
| A picture drawn again from that cleaned design | The picture that came with the share |
| The model's name and the app's version | The request, the language, the time, anything about the person |

`publish` refuses a design that holds any text besides layer names (`1_2`) and the format's
own words (`Strand`, `stripes`…), so nothing can ride along inside the file.

Shares carry no name. Once a design is here you cannot tell whose it was, so you cannot take
it down for the person who sent it. The app tells people that before they say yes.

## Set it up (once)

1. On GitHub: **Settings > Pages > Build and deployment > Source: GitHub Actions**.
2. Push this folder to `main`. The *Gallery* workflow (`.github/workflows/gallery.yml`)
   puts it online; its run shows the address, such as
   `https://ysetbon.github.io/OpenStrandStudio/`.
3. Put that address in `src/agent_sharing.py`:

   ```python
   GALLERY_URL = 'https://ysetbon.github.io/OpenStrandStudio/'
   ```

   Until it is set, the app never asks about the gallery. Sharing itself must be set up
   too (`cloudflare/share-worker/README.md`).

## Publish a design

Fetch your shares as usual, then name the ones you want to show:

```bash
python scripts/share_inbox.py publish shared/2026-11-10_1a2b3c4d
```

It says where the picture is (`gallery/designs/<id>.png`). Look at it, then commit and push
`gallery/` to show it:

```bash
git add gallery
```

```bash
git commit -m "Gallery: add a design"
```

```bash
git push
```

To take one out again (its id is its file's name in `gallery/designs/`), then commit and
push the same way:

```bash
python scripts/share_inbox.py unpublish 1a2b3c4d5e6f
```

## The files

- `index.html`, `gallery.css`, `gallery.js`: the page. It loads nothing from anywhere else.
- `designs.json`: the list `publish` keeps (`id`, `model`, `version`), oldest first.
- `designs/<id>.json` and `designs/<id>.png`: each design and its picture.
