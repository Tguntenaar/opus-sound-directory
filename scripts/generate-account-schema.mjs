import { DatabaseSync } from 'node:sqlite';
import { writeFileSync, mkdirSync } from 'node:fs';
import { getMigrations } from 'better-auth/db/migration';
import { createAuth } from '../lib/auth-config.ts';
const database = new DatabaseSync(':memory:');
const auth = createAuth(database, { BETTER_AUTH_SECRET: 'schema-generation-placeholder-not-a-deployment-secret' });
const migration = await getMigrations(auth.options);
const sql = await migration.compileMigrations();
mkdirSync('migrations/accounts', { recursive: true });
writeFileSync('migrations/accounts/0001_accounts.sql', '-- Generated from the pinned Better Auth configuration.\n' + sql + `\n\nCREATE TABLE submission (
  id TEXT PRIMARY KEY NOT NULL,
  ownerId TEXT NOT NULL REFERENCES user(id) ON DELETE RESTRICT,
  createdAt TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE INDEX submission_owner_created ON submission(ownerId, createdAt);
CREATE INDEX submission_created ON submission(createdAt);
`);
database.close();
