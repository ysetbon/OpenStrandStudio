// The share inbox Worker (src/index.js), with an R2 bucket and a rate limiter in memory:
// the world can add sealed shares and nothing else; the developer's token reads them.
import assert from 'node:assert/strict';
import { test } from 'node:test';

import worker from '../src/index.js';

const TOKEN = 'a'.repeat(43); // as `openssl rand -base64 32` gives, without its '='
const SEALED = new Uint8Array(4 + 1120 + 16 + 200);
SEALED.set([0x4f, 0x53, 0x53, 0x31]); // "OSS1"
SEALED.fill(7, 4);

function bucket() {
  const objects = new Map();
  return {
    objects,
    async put(key, body, options) { objects.set(key, { body: new Uint8Array(body), options, uploaded: new Date() }); },
    async get(key) {
      const o = objects.get(key);
      return o ? { body: o.body } : null;
    },
    async delete(key) { objects.delete(key); },
    async list({ prefix }) {
      const found = [...objects].filter(([key]) => key.startsWith(prefix));
      return { objects: found.map(([key, o]) => ({ key, size: o.body.length, uploaded: o.uploaded })), truncated: false };
    },
  };
}

function limiter(limit) {
  const counts = new Map();
  return { async limit({ key }) {
    counts.set(key, (counts.get(key) || 0) + 1);
    return { success: counts.get(key) <= limit };
  } };
}

function env(extra = {}) {
  return { SHARES: bucket(), SHARE_LIMIT: limiter(10), MAX_BYTES: '8388608', INBOX_TOKEN: TOKEN, ...extra };
}

function post(body, headers = {}) {
  return new Request('https://inbox.example/v1/share', {
    method: 'POST', body, headers: { 'Content-Type': 'application/octet-stream', 'CF-Connecting-IP': '203.0.113.9', ...headers },
  });
}

test('a sealed share is kept as it came, under a name that says nothing of its sender', async () => {
  const e = env();
  const answer = await worker.fetch(post(SEALED), e);
  assert.equal(answer.status, 204);
  assert.equal(await answer.text(), '');
  const [[key, kept]] = [...e.SHARES.objects];
  assert.match(key, /^shares\/\d{4}-\d{2}-\d{2}\/[0-9a-f-]{36}\.oss$/);
  assert.deepEqual(kept.body, SEALED);
  assert.deepEqual(kept.options, { httpMetadata: { contentType: 'application/octet-stream' } }); // no IP, no headers
  assert.equal(answer.headers.get('Cache-Control'), 'no-store');
  assert.equal(answer.headers.get('Access-Control-Allow-Origin'), null); // no web page may use it
});

test('anything but a sealed share is refused, and nothing is kept', async () => {
  const e = env();
  const plain = new TextEncoder().encode(JSON.stringify({ answer: ['not sealed'] }).padEnd(2000));
  const cases = [
    [new Request('https://inbox.example/v1/share'), 405], // GET: nothing to read here
    [new Request('https://inbox.example/v1/share', { method: 'OPTIONS' }), 405], // no CORS preflight
    [post(SEALED, { 'Content-Type': 'application/json' }), 415],
    [post(plain), 400], // not "OSS1"
    [post(SEALED.slice(0, 1000)), 400], // too short to be one
    [post(SEALED, { 'Content-Length': '9000000' }), 413],
    [post(SEALED, { 'Content-Length': 'not a number' }), 413],
    [new Request('https://inbox.example/shares/2026-11-09/x.oss'), 404],
  ];
  for (const [request, status] of cases) assert.equal((await worker.fetch(request, e)).status, status);
  const big = new Uint8Array(9000);
  big.set(SEALED.slice(0, 4));
  assert.equal((await worker.fetch(post(big), env({ MAX_BYTES: '8000' }))).status, 413); // counted as it streams
  assert.equal(e.SHARES.objects.size, 0);
});

test('one address sends at most ten shares a minute', async () => {
  const e = env();
  const statuses = [];
  for (let i = 0; i < 12; i++) statuses.push((await worker.fetch(post(SEALED), e)).status);
  assert.deepEqual(statuses, [...Array(10).fill(204), 429, 429]);
  assert.equal((await worker.fetch(post(SEALED, { 'CF-Connecting-IP': '198.51.100.4' }), e)).status, 204);
});

test('the inbox opens with the token only, and gives back the sealed bytes', async () => {
  const e = env();
  await worker.fetch(post(SEALED), e);
  const [key] = [...e.SHARES.objects.keys()];
  const ask = (path, token, method = 'GET') => worker.fetch(new Request(`https://inbox.example${path}`, {
    method, headers: token ? { Authorization: `Bearer ${token}` } : {} }), e);
  assert.equal((await ask('/v1/inbox')).status, 401);
  assert.equal((await ask('/v1/inbox', 'b'.repeat(43))).status, 401);
  assert.equal((await ask(`/v1/inbox/${key}`, TOKEN.slice(1))).status, 401);
  const listed = await (await ask('/v1/inbox', TOKEN)).json();
  assert.deepEqual(listed.shares.map((s) => [s.key, s.size]), [[key, SEALED.length]]);
  assert.equal(listed.cursor, null);
  const got = await ask(`/v1/inbox/${encodeURIComponent(key)}`, TOKEN);
  assert.equal(got.status, 200);
  assert.deepEqual(new Uint8Array(await got.arrayBuffer()), SEALED);
  assert.equal((await ask('/v1/inbox/../wrangler.toml', TOKEN)).status, 404);
  assert.equal((await ask('/v1/inbox/shares/2026-11-09/other.txt', TOKEN)).status, 404);
  assert.equal((await ask(`/v1/inbox/${key}`, TOKEN, 'DELETE')).status, 204);
  assert.equal(e.SHARES.objects.size, 0);
});

test('without its token set, the inbox does not exist', async () => {
  for (const token of [undefined, '', 'short']) {
    const answer = await worker.fetch(new Request('https://inbox.example/v1/inbox', {
      headers: { Authorization: `Bearer ${token}` } }), env({ INBOX_TOKEN: token }));
    assert.equal(answer.status, 404);
  }
});
