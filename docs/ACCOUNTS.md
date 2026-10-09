# Contributor accounts

GitHub and Google sign-in give every new web or MCP submission a stable owner. The account email is private; the optional public credit is supplied separately. Reading and downloading the catalog requires no account.

## Before deployment

1. Bind a Cloudflare D1 database as `ACCOUNTS_DB`. Both Cloudflare configuration variants declare the name `opus-sounds-accounts`.
2. Apply `migrations/accounts/0001_accounts.sql` to that database before serving the new routes. For an existing database, review a new migration instead of reapplying or regenerating the initial migration.
3. Configure a random `BETTER_AUTH_SECRET` of at least 32 characters using Worker secrets. Keep it stable between deployments. Set `BETTER_AUTH_URL` to the exact origin, normally `https://opussounds.directory`.
4. Register provider applications with the callbacks below and set their client IDs and secrets on the Worker. Request only profile and email access; repository, Gmail, and Drive permissions are not needed.
5. Confirm sign-in, sign-out, token creation/revocation, and an owned submission in a preview before release. Providers without both settings are hidden. Without a database/secret the account endpoints fail closed.

| Provider | Callback | Worker settings |
| --- | --- | --- |
| GitHub | `https://opussounds.directory/api/auth/callback/github` | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Google | `https://opussounds.directory/api/auth/callback/google` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |

Use separate OAuth applications for local development; set callbacks and `BETTER_AUTH_URL` to the same localhost origin. Never commit `.dev.vars`, provider secrets, session cookies, or agent tokens. This feature uses Better Auth with native D1 support, not a paid hosted identity service. Cloudflare storage and request usage remain subject to the account's plan.

Automatic linking by matching email is disabled. To add a second provider, sign in with the original provider and use the account's link-provider action. Do not create separate accounts and assume they share submissions.

## MCP submissions

MCP server version `2.0.0` keeps the `/mcp` URL and public read tools unchanged. Submission and private status tools now require account tokens; clients that previously submitted anonymously must add the authorization header. This server version is separate from the MCP wire-protocol version.

At `/account`, create a named agent token. Supply it to `/mcp` as the HTTP header `Authorization: Bearer YOUR_TOKEN`. Configure the value through the client's private secret settings; do not put it in a public `.mcp.json`, prompt, example, or repository.

Tokens allow `submit_sound` and `get_submission_status` for their account. They cannot create browser sessions or manage account tokens. They default to 90-day expiry and are revocable immediately. Clients without configurable HTTP headers can still use the public read tools; browser OAuth authorization for MCP clients is not implemented.

Rate limits apply to the account, so creating multiple tokens does not bypass the submission cooldown. New records use D1's indexed account ownership. Existing anonymous KV submissions are admin-only and cannot be automatically assigned by email. The account page lists the latest 100 submissions.

## Verification

`npm test` includes real Better Auth database tests for OAuth state/origin checks, session lookup, token hashing, scope restrictions, expiry, revocation, and cross-account access. `npm run accounts:schema` regenerates the initial migration from the pinned auth configuration for a fresh database only.

Live provider callbacks require configured provider credentials and interactive consent; local tests do not substitute for that deployment check.
