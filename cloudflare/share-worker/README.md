# OpenStrand Studio share inbox

A Cloudflare Worker that receives what people **choose** to share with you from OpenStrand
Studio's agent panel, whichever model they use there: the design the model made (all of it,
their own canvas too when the model changed it), its picture, and the model's answer, with
the model used, the app's version and language, whether the request worked, and whether the
design was made from nothing of theirs.

This inbox is private: only you read it. The public gallery is a separate thing
(`gallery/README.md`): a second yes from the person, and a cleaned copy that you publish by
hand. Nothing in the inbox is ever public.

Nobody shares anything until they say yes. The panel asks once, on a card under the agent's
first answer, and *Settings > Models* turns sharing on or off at any time. A yes holds for
every request after it, until it is turned off. Until you finish
the setup below, the app shows no card and no setting.

## How it stays private

| Step | What protects it |
|---|---|
| On the person's computer | The app encrypts each share with **your public key** before it leaves (HPKE, RFC 9180: ML-KEM-768 + X25519, so it holds against future quantum computers too, with HKDF-SHA256 and ChaCha20-Poly1305). File paths, API keys (the person's own, and any `sk-...` or `xai-...` key) and the home folder are cut out of every text first. |
| On the way | HTTPS only, certificate checked, TLS 1.2 or newer, and no redirects followed. |
| At Cloudflare | The Worker and its R2 bucket only ever hold sealed bytes. Without your private key, nobody can read them: not Cloudflare, not someone who breaks into your Cloudflare account, and not a leaked bucket. |
| Kept about the sender | No IP address or header is saved, with a share or in a log: request logs are off. Cloudflare's rate limiter counts each IP address's shares for its 60-second window. Each share's name holds the day it came, and R2 notes when it was stored (the inbox shows that as `received`). |
| Who can add | Anyone with the app, at most 10 shares a minute per IP address and 8 MB each. Anything that is not a sealed share is refused. |
| Who can read | Only someone with the `INBOX_TOKEN` secret, and what they get is still sealed. Only your **private key**, kept off line, opens it. |

Never sent: the request the person typed, pictures they gave the agent, their own canvas (or a
tab) that the agent only read, API keys (one an answer repeats is cut out too), their files,
folders (every path is cut out), an error's text, the time, anything about the computer or the person. The agent's answer may still
repeat words or bare file names from the request or the canvas: the consent text tells
people so. Nothing is sent at all while the person has *Connect to AI models* turned off in
*Settings > Models*.

> Anyone can send a share (your public key is inside the app). A share is sealed, not
> signed, so open one the way you would open a file from a stranger.

## Set it up (once)

You need Node.js 20+, a Cloudflare account (the free plan is enough) with two-factor
sign-in turned on, and Python with `cryptography>=47` (`pip install -r requirements.txt`).

**1. Make your key pair** (from the repository root):

```bash
python scripts/share_inbox.py keygen
```

This writes your **private key** to `~/.openstrand-share.key` (readable by you alone) and
prints your **public key**. Back up the private key somewhere off line, such as a password
manager or a USB stick. If you lose it, no share sent to you can ever be opened. Never
commit it or upload it anywhere.

**2. Create the bucket and deploy the Worker:**

```bash
cd cloudflare/share-worker
```

```bash
npm install
```

```bash
npx wrangler login
```

The shares go in your R2 bucket `openstrandstudio`, under `shares/` (`wrangler.toml` names
it; the Worker touches nothing else in the bucket). Keep that bucket private: no public
access, no custom domain and no `r2.dev` address. Its S3 address
(`https://<account>.r2.cloudflarestorage.com/openstrandstudio`) and any R2 access key never
go in the app or in this repository: the app only ever knows the Worker's address.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the token that last command prints, and keep it in your password manager. It is your
inbox token. Set it on the Worker (paste it when asked):

```bash
npx wrangler secret put INBOX_TOKEN
```

```bash
npx wrangler deploy
```

`deploy` prints your Worker's address, such as `https://openstrand-share.<account>.workers.dev`.

**3. Put both in the app.** In `src/agent_sharing.py`:

```python
SHARE_URL = 'https://openstrand-share.<account>.workers.dev/v1/share'
SHARE_PUBLIC_KEY = '<the public key from step 1>'
```

Commit that change. The public key is meant to be public; the private key never goes in
the repository.

**4. Delete old shares automatically**, after 90 days. The rule covers `shares/` only, so
anything else in the bucket is left alone:

```bash
npx wrangler r2 bucket lifecycle add openstrandstudio expire-shares-90-days shares/ --expire-days 90
```

**5. Optional: the public gallery.** See `gallery/README.md`.

## Read what people shared

From the repository root:

```bash
OPENSTRAND_INBOX_TOKEN='<your inbox token>' python scripts/share_inbox.py fetch --url https://openstrand-share.<account>.workers.dev
```

Each share is saved in its own folder under `shared/`:

- `design.json` opens in OpenStrand Studio
- `design.png` is the design's picture
- `answer.md` is the agent's answer
- `about.json` holds the model, the app's version and language, whether the request worked, whether the design is new (made from nothing of the person's), whether they allowed it in the gallery, and when the Worker received it

Add `--delete` to remove shares from Cloudflare once they are saved on your computer. Leave
out `OPENSTRAND_INBOX_TOKEN=…` and the tool asks for the token instead, which keeps it out
of your shell history.

## Test it

```bash
npm test
```

To run the Worker on your own computer, put `INBOX_TOKEN=<any 32+ characters>` in a
`.dev.vars` file next to this README (it is git-ignored), then:

```bash
npx wrangler dev
```

## For your privacy policy

What you collect, only with the person's consent and revocable at any time in
*Settings > Models*:

- the designs the agent makes in the app, with their pictures (a person's own design too,
  in full, when the agent changed it)
- the answers of whichever model they use (which may repeat words or file names from their
  request)
- the model used, the app's version and language, and whether each request worked
- when each share arrived

It is encrypted on the person's computer and stored with Cloudflare (R2) until you delete
it. With a second, separate consent, a design the model made from scratch may be shown in
the public gallery, with the model and the app's version: shares carry no name, so one that
is shown cannot be found again and taken down for the person who sent it. You do not collect the person's requests, their own pictures or files, their API keys,
or their IP address (Cloudflare's rate limiter only counts shares per IP address, for a
minute at a time).
