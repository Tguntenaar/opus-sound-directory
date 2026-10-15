#!/usr/bin/env node
/**
 * Wrapper for runner/loudness_audit.py (catalog LUFS / true-peak report).
 * Usage: node scripts/loudness-audit.mjs [--check] [--takes]
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const pyArgs = ["runner/loudness_audit.py", ...args];
const result = spawnSync("python3", pyArgs, { cwd: root, stdio: "inherit" });
process.exit(result.status ?? 1);
