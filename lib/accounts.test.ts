import { test } from "node:test";
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { serializeSignedCookie } from "better-call";
import { createAuth, enabledProviders } from "./auth-config.ts";
import { ownsSubmission, ownedSubmissionInput } from "./submission-access.ts";

const secret = "test-only-secret-with-at-least-thirty-two-characters";
function fixture() {
  const db = new DatabaseSync(":memory:");
  db.exec(readFileSync(new URL("../migrations/accounts/0001_accounts.sql", import.meta.url), "utf8"));
  const auth = createAuth(db, { BETTER_AUTH_SECRET: secret, BETTER_AUTH_URL: "http://localhost:43125", GITHUB_CLIENT_ID: "test-client", GITHUB_CLIENT_SECRET: "test-secret", GOOGLE_CLIENT_ID: "test-client", GOOGLE_CLIENT_SECRET: "test-secret" });
  return { db, auth };
}

test("auth is unavailable without a strong deployment secret", () => {
  assert.throws(() => createAuth(undefined, {}));
  assert.deepEqual(enabledProviders({ GITHUB_CLIENT_ID: "partial" }), []);
});

test("tokens are hashed, scoped, owner-bound, expire, and can be revoked", async () => {
  const { db, auth } = fixture();
  const context = await auth.$context;
  const alice = await context.internalAdapter.createUser({ name: "Alice", email: "alice@example.test", emailVerified: true }, { method: "email" });
  const bob = await context.internalAdapter.createUser({ name: "Bob", email: "bob@example.test", emailVerified: true }, { method: "email" });
  const key = await auth.api.createApiKey({ body: { userId: alice.id, name: "Test agent" } });
  assert.match(key.key, /^opus_/);
  assert.ok(key.expiresAt && key.expiresAt.getTime() > Date.now() + 89 * 86400000);
  const stored = db.prepare("SELECT key FROM apikey WHERE id = ?").get(key.id) as { key: string };
  assert.notEqual(stored.key, key.key);
  const valid = await auth.api.verifyApiKey({ body: { key: key.key, permissions: { submissions: ["create"] } } });
  assert.equal(valid.valid, true);
  assert.equal(valid.key?.referenceId, alice.id);
  assert.equal((await auth.api.verifyApiKey({ body: { key: key.key, permissions: { account: ["admin"] } } })).valid, false);
  assert.equal(await auth.api.getSession({ headers: new Headers({ authorization: `Bearer ${key.key}`, "x-api-key": key.key }) }), null);
  const bobSession = await context.internalAdapter.createSession(bob.id);
  const bobCookie = (await serializeSignedCookie("better-auth.session_token", bobSession.token, secret)).split(";")[0];
  await assert.rejects(() => auth.api.deleteApiKey({ body: { keyId: key.id }, headers: new Headers({ cookie: bobCookie }) }));
  const aliceSession = await context.internalAdapter.createSession(alice.id);
  const cookie = (await serializeSignedCookie("better-auth.session_token", aliceSession.token, secret)).split(";")[0];
  const session = await auth.api.getSession({ headers: new Headers({ cookie }) });
  assert.equal(session?.user.id, alice.id);
  await auth.api.deleteApiKey({ body: { keyId: key.id }, headers: new Headers({ cookie }) });
  assert.equal((await auth.api.verifyApiKey({ body: { key: key.key } })).valid, false);
  const expired = await auth.api.createApiKey({ body: { userId: alice.id, name: "Expired" } });
  db.prepare('UPDATE apikey SET expiresAt = ? WHERE id = ?').run(Date.now() - 1000, expired.id);
  assert.equal((await auth.api.verifyApiKey({ body: { key: expired.key } })).valid, false);
  db.close();
});

test("OAuth redirects contain state and reject a foreign callback origin", async () => {
  const { db, auth } = fixture();
  for (const provider of ["github", "google"]) {
    const response = await auth.handler(new Request("http://localhost:43125/api/auth/sign-in/social", { method: "POST", headers: { "Content-Type": "application/json", origin: "http://localhost:43125" }, body: JSON.stringify({ provider, callbackURL: "/account" }) }));
    assert.equal(response.status, 200);
    const body = await response.json() as { url: string };
    const url = new URL(body.url);
    assert.ok(url.searchParams.get("state"));
    assert.equal(url.searchParams.get("redirect_uri"), `http://localhost:43125/api/auth/callback/${provider}`);
  }
  const blocked = await auth.handler(new Request("http://localhost:43125/api/auth/sign-in/social", { method: "POST", headers: { "Content-Type": "application/json", origin: "https://attacker.test" }, body: JSON.stringify({ provider: "github", callbackURL: "https://attacker.test" }) }));
  assert.equal(blocked.status, 403);
  db.close();
});

test("a supplied contact email cannot override the verified submitter", () => {
  const input = { title: "Chime", prompt: "A softly synthesized chime", email: "someone-else@example.test", category: "ui", mood: ["calm"] };
  assert.equal(ownedSubmissionInput(input, { id: "alice", email: "alice@example.test", emailVerified: true }).email, "alice@example.test");
  assert.throws(() => ownedSubmissionInput(input, { id: "alice", email: "alice@example.test", emailVerified: false }));
  assert.equal(ownsSubmission("alice", "alice"), true);
  assert.equal(ownsSubmission("alice", "bob"), false);
  assert.equal(ownsSubmission(undefined, "alice"), false);
});

test("submission cooldown is enforced by the database even with separate tokens", () => {
  const { db } = fixture();
  db.prepare('INSERT INTO user (id, name, email, emailVerified, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)').run("alice", "Alice", "a@example.test", 1, Date.now(), Date.now());
  const insert = db.prepare(`INSERT INTO submission (id, ownerId, createdAt, payload) SELECT ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM submission WHERE ownerId = ? AND createdAt > ?)`);
  const now = new Date().toISOString();
  const since = new Date(Date.now() - 3600000).toISOString();
  assert.equal(insert.run("first", "alice", now, "{}", "alice", since).changes, 1);
  assert.equal(insert.run("second", "alice", now, "{}", "alice", since).changes, 0);
  db.close();
});
