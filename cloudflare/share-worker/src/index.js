/**
 * OpenStrand Studio's share inbox: a Cloudflare Worker that keeps, in an R2 bucket, what
 * people choose to share with the developer from the app (src/claude_sharing.py).
 *
 * The world can only add to it: POST /v1/share keeps one sealed share. Each share is
 * encrypted in the app with the developer's public key (HPKE with ML-KEM-768 + X25519)
 * before it is sent, so this Worker, Cloudflare and anyone who gets into the bucket only
 * ever hold bytes they cannot read.
 *
 * Only the developer reads the inbox: GET /v1/inbox (with the INBOX_TOKEN secret) lists
 * the sealed shares and GET /v1/inbox/<key> fetches one (scripts/share_inbox.py fetch),
 * which their private key, kept off line, then opens. Without INBOX_TOKEN set, reading is
 * off altogether.
 *
 * Nothing about the sender is kept: no IP address, no headers, nothing but the day in the
 * share's name. Request logs are off (wrangler.toml).
 */
const MAGIC = [0x4f, 0x53, 0x53, 0x31]; // "OSS1": what every sealed share starts with
const ENCAPSULATED = 1120; // HPKE's encapsulated key, for ML-KEM-768 + X25519
const TAG = 16; // ChaCha20-Poly1305's tag
const MIN_BYTES = MAGIC.length + ENCAPSULATED + TAG;
const DEFAULT_MAX_BYTES = 8 * 1024 * 1024; // as the app's own limit
const PREFIX = 'shares/';
const NAME = /^shares\/\d{4}-\d{2}-\d{2}\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.oss$/;

const HEADERS = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' };

function reply(status, body = null, headers = {}) {
  return new Response(body, { status, headers: { ...HEADERS, ...headers } });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === '/v1/share') return await share(request, env);
      if (url.pathname === '/v1/inbox' || url.pathname.startsWith('/v1/inbox/')) return await inbox(request, env, url);
      return reply(404);
    } catch {
      return reply(500); // nothing about what went wrong goes back
    }
  },
};

// ------------------------------------------------------------------ POST /v1/share
async function share(request, env) {
  // Only POST, and only the app's own content type: a web page cannot send one without
  // asking first (a CORS preflight), which this Worker never allows.
  if (request.method !== 'POST') return reply(405, null, { Allow: 'POST' });
  if (env.SHARE_LIMIT) {
    const { success } = await env.SHARE_LIMIT.limit({ key: request.headers.get('CF-Connecting-IP') || 'unknown' });
    if (!success) return reply(429, null, { 'Retry-After': '60' });
  }
  const type = (request.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
  if (type !== 'application/octet-stream') return reply(415);
  const max = Number(env.MAX_BYTES) > 0 ? Number(env.MAX_BYTES) : DEFAULT_MAX_BYTES;
  if (Number(request.headers.get('Content-Length') || 0) > max) return reply(413);
  const body = await read(request.body, max);
  if (body === null) return reply(413);
  if (body.length < MIN_BYTES || !MAGIC.every((byte, i) => body[i] === byte)) return reply(400);
  const key = `${PREFIX}${new Date().toISOString().slice(0, 10)}/${crypto.randomUUID()}.oss`;
  await env.SHARES.put(key, body, { httpMetadata: { contentType: 'application/octet-stream' } });
  return reply(204);
}

/** The whole body, or null once it passes max bytes (a missing or false Content-Length
 * cannot get more than max in). */
async function read(stream, max) {
  if (!stream) return new Uint8Array(0);
  const reader = stream.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > max) {
      await reader.cancel();
      return null;
    }
    chunks.push(value);
  }
  const body = new Uint8Array(size);
  let at = 0;
  for (const chunk of chunks) {
    body.set(chunk, at);
    at += chunk.byteLength;
  }
  return body;
}

// ------------------------------------------------------------- the developer's inbox
async function inbox(request, env, url) {
  if (typeof env.INBOX_TOKEN !== 'string' || env.INBOX_TOKEN.length < 32) return reply(404); // reading is off
  if (!(await authorized(request, env.INBOX_TOKEN))) return reply(401, null, { 'WWW-Authenticate': 'Bearer' });
  if (url.pathname === '/v1/inbox') {
    if (request.method !== 'GET') return reply(405, null, { Allow: 'GET' });
    const listed = await env.SHARES.list({ prefix: PREFIX, limit: 500, cursor: url.searchParams.get('cursor') || undefined });
    const shares = listed.objects.map((o) => ({ key: o.key, size: o.size, uploaded: o.uploaded }));
    return reply(200, JSON.stringify({ shares, cursor: listed.truncated ? listed.cursor : null }),
      { 'Content-Type': 'application/json' });
  }
  const key = decodeURIComponent(url.pathname.slice('/v1/inbox/'.length));
  if (!NAME.test(key)) return reply(404);
  if (request.method === 'GET') {
    const object = await env.SHARES.get(key);
    return object ? reply(200, object.body, { 'Content-Type': 'application/octet-stream' }) : reply(404);
  }
  if (request.method === 'DELETE') {
    await env.SHARES.delete(key);
    return reply(204);
  }
  return reply(405, null, { Allow: 'GET, DELETE' });
}

/** Whether the request carries the inbox token, compared in constant time (as SHA-256
 * digests, so their lengths say nothing either). */
async function authorized(request, token) {
  const given = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!given) return false;
  const encode = (text) => crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  const [a, b] = (await Promise.all([encode(given), encode(token)])).map((d) => new Uint8Array(d));
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}
