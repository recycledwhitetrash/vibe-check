#!/usr/bin/env node
// SessionStart compact hook: re-inject vc-audit context after compaction.
// Registered in .claude/settings.json under hooks.SessionStart with matcher "compact".
// Fires when Claude's context window is compacted mid-session, restoring the audit
// state so the model knows where it left off without needing manual intervention.

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// --- helpers -----------------------------------------------------------------

function git(cmd) {
  try {
    return execSync(`git ${cmd}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch {
    return '';
  }
}

// Mirrors the slugify used by vc-audit when naming artifact files:
// lowercase, non-alphanumeric/hyphen → hyphen, collapse runs, strip edges.
function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
}

// Extract lines between two HTML comment sentinels (sentinels themselves excluded).
// Used to pull Phase 5/6 gate instructions and receipt format out of the compiled skill.
function extractBetween(text, startSentinel, endSentinel) {
  const lines = text.split('\n');
  let inside = false;
  const result = [];
  for (const line of lines) {
    if (line.includes(startSentinel)) { inside = true; continue; }
    if (line.includes(endSentinel))   { inside = false; continue; }
    if (inside) result.push(line);
  }
  return result.join('\n');
}

// --- main --------------------------------------------------------------------

const repoRoot = git('rev-parse --show-toplevel');
if (!repoRoot) process.exit(0);

const branch = git('branch --show-current');
if (!branch) process.exit(0); // detached HEAD — nothing to resume

const slug = slugify(branch);
const auditDir = path.join(repoRoot, '.vibe-check', 'vc-audit');

// Find the artifact: prefer the full-branch audit, fall back to any scoped audit.
let artifact = '';
const full = path.join(auditDir, `${slug}.md`);
if (fs.existsSync(full)) {
  artifact = full;
} else {
  // Scoped audits are named <slug>--<scope>.md
  try {
    const entries = fs.readdirSync(auditDir).filter(f => f.startsWith(`${slug}--`) && f.endsWith('.md'));
    if (entries.length) artifact = path.join(auditDir, entries[0]);
  } catch { /* auditDir doesn't exist yet */ }
}

if (!artifact) process.exit(0);

const artifactText = fs.readFileSync(artifact, 'utf8');

// Only fire if there is an audit actively in progress.
if (!artifactText.includes('**Status:** IN PROGRESS')) process.exit(0);

// Extract the in-progress pass number from the pass log entry.
const inProgressMatch = artifactText.match(/Pass (\d+).*— in progress/g);
const pass = inProgressMatch
  ? inProgressMatch[inProgressMatch.length - 1].match(/Pass (\d+)/)[1]
  : '?';

// Pull Phase 5+6 gate instructions and the receipt format block verbatim from
// the compiled skill. The sentinels are stable across versions — if the skill
// file is absent (not yet installed), we omit these sections gracefully.
const skillPath = path.join(repoRoot, '.claude', 'commands', 'vc-audit.md');
let phaseGates = '';
let receiptFormat = '';
if (fs.existsSync(skillPath)) {
  const skillText = fs.readFileSync(skillPath, 'utf8');
  phaseGates     = extractBetween(skillText, '<!-- COMPACT_HOOK_START -->', '<!-- COMPACT_HOOK_END -->');
  receiptFormat  = extractBetween(skillText, '<!-- RECEIPT_FORMAT_START -->', '<!-- RECEIPT_FORMAT_END -->');
}

const context = `Context was compacted mid-audit.

In-progress artifact: ${artifact} (Pass ${pass} in progress)

Re-read that artifact now before doing anything else. Resume rules for /vc-audit:
- Check "## Pass ${pass} progress" checklist: [x] = done, resume from first [ ] surface
- After each surface: Edit artifact to change "- [ ] Surface" to "- [x] Surface" — mandatory, do not skip
- The "— in progress" marker in the pass log satisfies the Phase 4 authorization gate — no new Continue response needed
- Finding IDs: read the highest F-NNN from the artifact findings table and continue from there — never use a subagent's own labels
- Pass checkpoint: call AskUserQuestion — do NOT write text output summarizing results or next steps

--- RECEIPT FORMAT (verbatim from skill — required for every surface) ---

${receiptFormat}

--- PHASE 5 AND 6 GATE INSTRUCTIONS (verbatim from skill) ---

${phaseGates}`;

// Claude Code hook output format: JSON on stdout.
console.log(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: context,
    reloadSkills: true,
  },
}));
