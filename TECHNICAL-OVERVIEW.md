# vibe-check — Technical Overview

This document is written for technical leads, senior engineers, and CTOs evaluating
vibe-check for use by junior developers, bootcamp graduates, and teams building proofs of
concept or internal tooling with AI assistance.

---

## The problem this addresses

AI coding assistants have lowered the barrier to producing working software significantly.
A developer with no formal training can now produce a functioning web app, API, or data
pipeline in hours. What they cannot produce — without guidance — is software that is safe
to put in front of users, maintainable six months later, or recoverable when something
goes wrong.

The failure modes are predictable: no planning before implementation, secrets committed to
version control, no test coverage, pull requests with no meaningful description, no
retrospection, no understanding of what shipped or why. Not because the developer is
incapable, but because they have never been shown what the process looks like.

vibe-check is a set of Claude Code slash commands that enforce that process. Each command
is a structured workflow script — not a suggestion, not a prompt template — that Claude
executes step by step, with mandatory decision gates, artifact writes, and blocking
conditions that prevent common failure modes from reaching production.

---

## Architecture

vibe-check commands are Markdown files stored in `.claude/commands/` at the project root.
When a developer types `/vc-plan`, Claude reads the corresponding `.md` file and executes
it as a script. Commands use Claude's native tools — Bash, Read, Write, Edit, WebFetch,
AskUserQuestion — to interact with the filesystem, git, GitHub CLI, and the developer.

**All persistent state is written to files immediately when generated**, not held in
context. This is a deliberate design choice that makes every command recoverable after
an AI context compaction event, a session restart, or an interrupted run.

Artifacts are written to `.vibe-check/` in the project root and travel with the repo.
Every significant decision — a plan, an audit finding, a ship event, a retro — is on disk
and in version control.

---

## Build system

The skill files installed into `.claude/commands/` are generated from source templates in
`src/*.md.tmpl` via `build.py` and committed as built artifacts — developers install the
pre-built files directly and never interact with the build system.

Template tokens (`{{VERSION}}`, `{{SKILL_NAME}}`, `{{LOCAL_CONFIG}}`, `{{SLUG_RULE}}`, and
others) are resolved at build time. `src/sections/` contains shared Markdown blocks that
are included verbatim across multiple templates. `src/data/` contains JSON files that are
expanded into multiple tokens simultaneously — for example, `sensitive-patterns.json`
expands into the `.gitignore` block, the `SENSITIVE_READ_TABLE`, and the
`SENSITIVE_EXCLUSIONS` token used across bootstrap, onboard, and ship.

`versions.json` at the repo root tracks the current version of each skill. `build.py`
auto-increments the version on every build that changes a compiled file and fails with a
non-zero exit code if any `{{...}}` token remains unreplaced in the output — catching
missing template data before the build is committed. A `--diff` flag prints a summary of
what changed without writing files; `--check` validates without writing.

The `.claude/hooks/` and `.claude/lenses/` directories are also built outputs managed by
`build.py`. Hook scripts are written as source files in `src/hooks/` and copied on build.

---

## Security

Security is treated as a hard-stop concern in vibe-check, not a suggestion.

### Secret scanning (two-pass)

`/vc-ship` runs [gitleaks](https://github.com/gitleaks/gitleaks) twice before anything
reaches GitHub:

1. Against the committed diff (`git diff [BASE_BRANCH]...HEAD`) — catches secrets already
   in commits
2. Against uncommitted changes (`git diff HEAD`) — catches secrets staged or modified but
   not yet committed

If gitleaks finds anything in either pass, the ship command stops immediately. The
developer cannot proceed past the secret scan with findings present. They must either
remove the secret from the commit history, or — for confirmed false positives — add an
explicit gitleaks allowlist entry, which is shown to the developer for confirmation before
being committed.

gitleaks is installed automatically by `/vc-bootstrap` and by `/vc-ship` if not present,
so there is no path by which a developer skips the scan because the tool is not set up.

### Security-baseline .gitignore

`/vc-bootstrap` writes or appends a security-baseline `.gitignore` covering:

- Environment files (`.env`, `.env.*`, `.envrc`)
- Private keys and certificates (`.pem`, `.key`, `.p12`, `.p8`, `.pkcs8`, `id_rsa`, etc.)
- Secret stores (`.secret`, `*credentials.json`, `*service-account*.json`, `*-key.json`)
- Package manager auth files (`.npmrc`, `.yarnrc`, `.pypirc`)
- Infrastructure secrets (`.tfstate`, `.tfvars`, `kubeconfig`, `google-services.json`,
  `GoogleService-Info.plist`, `wrangler.toml`, `fly.toml`)

The bootstrap command checks for an existing `.gitignore` before writing and does not
overwrite custom entries. The security block is idempotent — a marker line prevents
duplicate appends on re-runs.

### Security review lens in /vc-audit

The audit command applies a security-specific review lens to every changed file:

- Injection vectors (SQL, shell, template, path traversal)
- Authentication and authorization gaps (missing checks, broken access control)
- Hardcoded credentials in source
- Insecure deserialization
- Sensitive data exposure in logs, error messages, or API responses
- Missing input validation at system boundaries

Security findings are rated by severity. High-severity findings are applied directly to
source files using the Edit tool without requiring user confirmation — the developer
cannot choose to defer a high-confidence critical security issue past the audit phase.

---

## Testing

vibe-check enforces test coverage as a ship gate, not an afterthought.

### Coverage target and auto-remediation

`/vc-ship` checks test coverage against an 80% target before creating the pull request.
If coverage is below 80%:

1. Claude identifies the specific files below threshold
2. Writes missing tests automatically using the project's existing test framework and
   conventions (detected from `devDependencies` and the `test` script value in
   `package.json`, or equivalent for other ecosystems)
3. Runs the test suite to verify the new tests pass
4. If tests fail: failing cases are pruned individually — the whole test file is not
   discarded, only the specific cases that cannot be made to pass in the session
5. Loops up to three rounds before reporting the remaining gap and noting it in the PR body

This means a developer cannot open a PR with no test coverage without a documented reason.
The gap, if any, is explicit in the PR description rather than invisible.

### Test planning in /vc-plan

Before any implementation begins, `/vc-plan` asks the developer to define their definition
of done, which includes test cases. If tests are not applicable (e.g., a config change, a
data migration script), the developer must explicitly state why and that reason is written
into the plan artifact. There is no silent "no tests" path.

### Test coverage as an audit lens

`/vc-audit` applies a test coverage lens that is independent of the coverage percentage
check in `/vc-ship`. The audit reviews whether:

- Happy path cases are covered
- Error paths and edge cases have coverage
- Integration points are tested
- The test cases that exist actually test the behavior they claim to test

This catches test suites that pass coverage metrics but are not meaningfully protective.

---

## Context compaction mitigation

Long AI sessions — especially code reviews of large diffs — can exceed Claude's context
window and trigger automatic compaction. vibe-check is designed to survive this cleanly
without losing state or requiring a restart.

### Compact hook

`/vc-bootstrap` installs a `SessionStart` hook (`vc-audit-resume.js`) that fires on
context compaction events during an active `/vc-audit` session. The hook re-injects the
Phase 5 and Phase 6 instructions and the receipt format block directly into the context
window, so Claude has the critical gate instructions available immediately after compaction
without requiring the developer to manually resume. The hook script is stored in
`.claude/hooks/` and registered in `.claude/settings.json` during bootstrap.

### Artifact-as-source-of-truth

Every audit finding is written to the audit artifact file **immediately when discovered**,
before any fix is attempted and before the next finding is processed. The artifact is the
canonical record, not the AI's in-context state. After a compaction event, Claude re-reads
the artifact to reconstruct exactly where it was: which findings are open, which are
resolved, which were deferred or dismissed, and which pass it is currently on.

### Finding chain with cross-references

Each finding is assigned a persistent identifier (`F-NNN`). When a finding is resolved,
deferred, or dismissed, the original `F-NNN` entry is updated with a cross-reference to
the outcome record (`R-NNN`, `D-NNN`, or `X-NNN`). Dismissals require a stated reason.
This means the full decision trail is recoverable from the artifact alone, even after
compaction.

### Session variable re-derivation on all entry paths

Every command that might resume after compaction re-derives its session variables from
first principles on entry — it does not rely on in-context state persisting. For
`/vc-audit` specifically:

- `BASE_BRANCH` is re-derived using a priority chain: symbolic-ref → `git remote show
  origin` → common name fallback (`main`, `master`, `develop`)
- The artifact path is re-computed from the branch name and any `$ARGUMENTS` passed to
  the command
- Open findings are re-read from the artifact, not assumed from prior context

### Convergence requirement

`/vc-audit` does not stop when it "feels done." It requires **two consecutive passes with
zero open findings** before declaring convergence. This prevents premature termination
after a partial review and ensures that fixes applied in one pass did not introduce new
issues that would be caught in the next.

### LARGE_DIFF detection

When the diff between a feature branch and the base branch is too large to review in a
single context window, `/vc-audit` detects this condition and presents the developer with
structured scope options rather than silently truncating the review. The developer can
scope the audit to a subdirectory, exclude specific file patterns, or split the PR — and
each option comes with a coverage checklist showing what will and will not be reviewed.

---

## Development pattern enforcement

vibe-check enforces patterns that experienced developers follow by habit but that new
developers have never been shown.

### Branch-per-feature with upfront planning

`/vc-plan` creates the feature branch **before** the developer writes any code. This is
not optional — the branch is created as part of the planning workflow. The developer
cannot produce a plan without also having a branch. Work on `main` without a plan is
not a supported workflow.

### Premise challenge and adversarial review

Before any implementation begins, `/vc-plan` runs an adversarial subagent review of the
feature plan. This is a second Claude instance with no prior context, given only the plan
and asked to challenge it: find assumptions that are wrong, scope that is larger than
stated, risks that were not identified, and alternatives that were not considered. The
outcome of the adversarial review is written into the plan artifact in all cases — passed,
issues found, or unavailable.

This catches "I'll figure it out as I go" planning before it becomes three weeks of rework.

### Merge before next feature

After every pull request is created by `/vc-ship`, the developer receives an explicit
reminder: merge this PR before starting your next feature. Starting a new branch before
the current one is merged will cause merge conflicts. This is stated plainly, not buried
in documentation.

### Bisectable commit history

`/vc-ship` scans the commit history for non-bisectable patterns: WIP commits, fixup
commits, squash commits, and temp commits. If found, the developer is offered a soft
reset to the base branch with a proposed reorganization into clean atomic commits. The
developer approves the groupings before anything is recommitted. The result is a commit
history that `git bisect` can actually work with.

### Roadmap as living document

Every feature planned with `/vc-plan` is registered in a project-level roadmap at
`.vibe-check/vc-plan/roadmap.md`. The roadmap row is updated automatically when `/vc-ship`
creates the PR, and again when the retro is run. At any point, the roadmap shows every
feature from first plan to shipped state, with links to the plan artifact and PR for each.

This is the document a senior dev can read to understand what the project is, what
has shipped, what is in progress, and what is planned next — without asking the developer.

### Quantified retrospectives with planning discipline scoring

`/vc-retro` produces a quantified retrospective on every run, not a freeform journal entry.
It computes:

- Commit count and active coding days for the period
- Most frequently modified files (instability signal)
- Planning discipline: the percentage of commits that had a corresponding plan file
  in place before work began
- Period-over-period deltas if a prior retro exists within 31 days

The planning discipline metric specifically gives visibility into whether the developer is
actually using `/vc-plan` before writing code, or shipping directly to main without
planning. The retro output is written to `.vibe-check/vc-retro/` and travels with the
repo — it is not a private note.

---

## Per-command technical reference

### /vc-bootstrap

**Purpose:** one-time setup for a machine and project.

Detects OS via `uname -s` and `winget --version` to determine whether to use
`brew`, `winget`, or `apt` for tool installation. On Linux/WSL, attempts
`sudo apt install -y` automatically (blank sudo password is common on WSL2 — this
succeeds silently for most users) before falling back to a manual install + pause-and-resume
pattern. Does not stop the session and force a restart for tool installation on any platform.

Configures `git user.name`, `git user.email`, and `init.defaultBranch`. Authenticates
`gh` CLI with step-by-step browser instructions. Writes the security-baseline `.gitignore`.
Writes a bootstrap artifact to `.vibe-check/vc-bootstrap.md`.

Installs the compact hook: downloads `vc-audit-resume.js` into `.claude/hooks/` and
registers it as a `SessionStart` hook in `.claude/settings.json`. The hook fires on
compaction events during `/vc-audit` sessions to re-inject critical phase instructions.

Offers an optional notification hook (`PermissionRequest`) that plays a system sound when
Claude Code is waiting for developer input — installed globally on macOS or per-project
on other platforms.

Idempotent: re-running on an already-bootstrapped project skips machine-level steps that
are already configured and re-runs project-level steps (`.gitignore` check, orientation).

### /vc-plan

**Purpose:** structured planning before any implementation begins.

Reads `CLAUDE.md`, `TODOS.md`, and the project roadmap on entry. Routes the developer to:
an existing in-progress plan, a pending chunk from an onboard run, a new feature, or a
roadmap decomposition for a large initiative.

For new features, runs a structured discovery conversation covering: scope calibration,
status quo assessment, narrowest useful version, premise challenge, distribution channel
(for external products), implementation approaches, definition of done, risk inventory,
failure modes, and security considerations. Then invokes an adversarial subagent to
challenge the plan before it is written.

Slugifies the feature name for the branch (`lowercase`, `non-alphanumeric → hyphen`,
`consecutive hyphens collapsed`, `leading/trailing stripped`) and creates the branch.
Writes the plan to `.vibe-check/vc-plan/[branch].md` and registers it in the roadmap.

Offers to commit the `.vibe-check/` directory after the plan is written, so the plan is
in version control before implementation begins.

### /vc-audit

**Purpose:** multi-pass code review with direct fix application.

Reads the diff between the current branch and the base branch. Selects applicable review
lenses from the set: security, data integrity, error handling, authentication/authorization,
API contracts, performance, test coverage, logging/observability, dependency risk, and
accessibility. Applies each lens to every changed file.

**Two-bucket fix model:**
- High-confidence findings ("Acting on"): applied directly to source files using the Edit
  tool, no user confirmation required
- Ambiguous findings ("Want to skip?"): one `AskUserQuestion` per finding with options:
  Fix now, Defer, or Dismiss (Dismiss requires a stated reason)

Loops until convergence. Supports FILE_READ_MODE for reviewing chunk files when no diff
exists (after `/vc-onboard`). Supports LARGE_DIFF detection with structured scope options.
Resumes automatically after context compaction by re-reading the artifact.

**Two background agents per pass:**
- *Adversarial subagent*: a second Claude instance with no prior context that reviews the
  same diff independently. Its prompt includes explicit checklist rules targeting the six
  historically-missed blind spot categories: ELI10 comment compliance, parallel function
  bug class, pre-existing code in modified files, CSS edge cases, and aria-live on dynamic
  elements.
- *Test integrity agent*: reviews all new and modified test files against a 6-pattern
  checklist — fixture shape mismatches, sync assertion on async throw, `fireEvent` on
  disabled elements (should be `userEvent`), prototype mutation restorability, implicit ARIA
  role vs. explicit attribute assertion, and non-discriminating assertions that pass even if
  the bug is reintroduced. Output is tagged `[test-integrity]` in the artifact.

Both agents are dispatched with `run_in_background: true` at the start of the surface walk
and collected before the pass closes.

### /vc-ship

**Purpose:** secret scan, quality gates, and PR creation.

Executes in order:
1. `gitleaks` two-pass scan (committed diff + uncommitted) — hard stop if secrets found
2. Lint check — sets up a linter if none is configured; runs and reports findings
3. Test coverage check — auto-writes tests if below 80%, up to three rounds
4. Suspicious file scan — identifies build output, OS metadata, dependency directories,
   log files; offers `.gitignore` entries for anything that should not be committed
5. Bisectability check — identifies non-atomic commits; offers soft-reset + reorganization
6. Remote check — if no remote is configured, offers to create via `gh repo create`
7. PR creation — generates title and body with a functional testing checklist; updates
   the plan artifact and roadmap

All auto-commits (tests, `.gitignore` changes) are done before the PR draft is written,
and before the bisectability check, so the final commit history is clean.

### /vc-retro

**Purpose:** quantified retrospective with period-over-period comparison.

Reads git log for the period since the last retro (up to 31 days), scoped to the
authenticated user's commits. Computes: commit count, active days, most-modified files,
test coverage signal, planning discipline percentage. If a prior retro exists within 31
days, loads it and computes deltas for each metric.

Asks four structured reflection questions. Prompts once on a non-answer before accepting
a fallback. Writes the full retro to `.vibe-check/vc-retro/[date]-[user-slug].md`.

### /vc-onboard

**Purpose:** bootstrapping vibe-check on a project that already has code.

Scans the codebase (excluding dependency and build directories) and detects the tech
stack from lockfiles, config files, and directory structure. Proposes a breakdown into
feature chunks with a maximum of 15 files per chunk. Chunks are logical feature areas
(auth, payments, api, ui) — not arbitrary file groupings. The developer confirms or
adjusts the breakdown before anything is written.

Writes plan stubs for every chunk **directly to the main branch** in a single commit.
Does not create one branch per chunk — this was an earlier design that caused merge
conflicts when multiple chunk branches were created from the same baseline. The current
design: all stubs on main, then the developer uses `/vc-plan` to pick a chunk and create
a branch, exactly as they would for any other feature.

Resumes automatically if interrupted: detects which stubs have been written and continues
from where it left off.
