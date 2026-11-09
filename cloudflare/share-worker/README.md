# OpenStrand Studio share inbox

A Cloudflare Worker that receives what people **choose** to share with you from OpenStrand
Studio's Claude panel: the design Claude made, its picture, and Claude's answer, with the
model used, the app's language and whether the request worked.

Nobody shares anything until they say yes. The panel asks once, on a card under Claude's
first answer, and *Settings > Models* turns sharing on or off at any time. Until you finish
the setup below, the app shows no card and no setting.

## How it stays private

| Step | What protects it |
|---|---|
| On the person's computer | The app encrypts each share with **your public key** before it leaves (HPKE, RFC 9180: ML-KEM-768 + X25519, so it holds against future quantum computers too, with HKDF-SHA256 and ChaCha20-Poly1305). File paths and the home folder are cut out of every text first. |
| On the way | HTTPS only, certificate checked, TLS 1.2 or newer, and no redirects followed. |
| At Cloudflare | The Worker and its R2 bucket only ever hold sealed bytes. Without your private key, nobody can read them: not Cloudflare, not someone who breaks into your Cloudflare account, and not a leaked bucket. |
| Kept about the sender | Nothing: no IP address, no headers, no time finer than the day. Request logs are off. |
| Who can add | Anyone with the app, at most 10 shares a minute per IP address and 8 MB each. Anything that is not a sealed share is refused. |
| Who can read | Only someone with the `INBOX_TOKEN` secret, and what they get is still sealed. Only your **private key**, kept off line, opens it. |

Never sent: the request the person typed, pictures they gave Claude, API keys, file names
or folders, the time, anything about the computer or the person. Nothing is sent at all
while the person has *Connect to AI models* turned off in *Settings > Models*.

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

```bash
npx wrangler r2 bucket create openstrand-shares
```

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

**3. Put both in the app.** In `src/claude_sharing.py`:

```python
SHARE_URL = 'https://openstrand-share.<account>.workers.dev/v1/share'
SHARE_PUBLIC_KEY = '<the public key from step 1>'
```

Commit that change. The public key is meant to be public; the private key never goes in
the repository.

**4. Optional: delete old shares automatically**, for example after 90 days:

```bash
npx wrangler r2 bucket lifecycle add openstrand-shares expire-90-days --expire-days 90
```

## Read what people shared

From the repository root:

```bash
OPENSTRAND_INBOX_TOKEN='<your inbox token>' python scripts/share_inbox.py fetch --url https://openstrand-share.<account>.workers.dev
```

Each share is saved in its own folder under `shared/`:

- `design.json` opens in OpenStrand Studio
- `design.png` is the design's picture
- `answer.md` is Claude's answer
- `about.json` holds the model, the app's language, how the request ended, and when the Worker received it

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

- the designs Claude makes in the app, with their pictures
- Claude's answers
- the model used, the app's language, and whether each request worked (with its error message, if any)

It is encrypted on the person's computer and stored with Cloudflare (R2) until you delete
it. You do not collect the person's requests, their own pictures or files, their API keys,
or their IP address.
