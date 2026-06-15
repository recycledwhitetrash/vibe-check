# vibe-check installer

You are Claude Code executing this installer. Follow each numbered step below in sequence. All instructions are contained in this document — do not search for additional files, scripts, or repos.

> **For humans reading this on GitHub:** To install vibe-check, open your project in Claude Code and say: "Fetch and follow the install instructions at `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/install.md`" — Claude will read this file and execute the steps automatically.

---

## What this does

1. Verifies this is a git repository
2. Downloads all 6 vibe-check skill files into `.claude/commands/` in your project
3. Adds a code commenting standard and vibe-check usage guide to your project's `CLAUDE.md`
4. Writes two memory files so Claude understands the vibe-check suite in future conversations
5. Tells you to run `/vc-bootstrap` to finish setup

Skills are installed **per-project** (not globally) because they read project-specific files
like your roadmap and feature plans.

---

## Step 1 — Find project root

Run:
```bash
git rev-parse --show-toplevel
```

If this succeeds: save the output as `PROJECT_ROOT` and continue to Step 2.

If this fails (not a git repository yet): run `pwd` to get the current working directory.
Then call AskUserQuestion:

- Question: "No git repository found. vibe-check will be installed into: `[pwd output]` — is this your project folder?"
- Options:
  - "Yes — install here"
  - "No — wrong folder"

If Yes: save the `pwd` output as `PROJECT_ROOT` and continue to Step 2. Note that
`/vc-bootstrap` will initialize the git repository as part of setup.

If No: tell the user to open Claude Code from inside their project folder and run the
install again. **Stop here.**

---

## Step 2 — Install skill files

<mandatory>Use ONLY the WebFetch tool and Write tool for this step. Do not use Bash commands, the Read tool on local paths, the gh CLI, curl, wget, or any other method. Use the exact fetch URLs from the table below — do not construct, guess, or shorten any URL. The skill files live in `.claude/commands/` in the GitHub repository; all fetch URLs in the table include this path. Always fetch from GitHub, never from local disk.</mandatory>

Use the WebFetch tool to fetch each URL below, then use the Write tool to save the content
to the corresponding path under `PROJECT_ROOT`. Fetch all 6 before writing any — if any
fetch fails, tell the user which file failed and stop without writing anything.

| Write to | Fetch from |
|---|---|
| `[PROJECT_ROOT]/.claude/commands/vc-bootstrap.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-bootstrap.md` |
| `[PROJECT_ROOT]/.claude/commands/vc-plan.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-plan.md` |
| `[PROJECT_ROOT]/.claude/commands/vc-audit.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-audit.md` |
| `[PROJECT_ROOT]/.claude/commands/vc-ship.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-ship.md` |
| `[PROJECT_ROOT]/.claude/commands/vc-retro.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-retro.md` |
| `[PROJECT_ROOT]/.claude/commands/vc-onboard.md` | `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-onboard.md` |

After all 6 are written, tell the user: "✓ 6 skill files installed."

---

## Step 3 — Update CLAUDE.md

Use the Read tool to check whether `[PROJECT_ROOT]/CLAUDE.md` exists.

Look for the line `# vibe-check` anywhere in the file content.

If that line **is already present**: the vibe-check section was written in a previous run —
skip this step and tell the user "✓ CLAUDE.md already up to date."

If that line **is not present** (whether the file exists or not): use the Edit tool to
append the following block to the end of `[PROJECT_ROOT]/CLAUDE.md`. If the file does not
exist, create it with the Write tool instead.

---

```
# vibe-check

## Code commenting standard — ELI10

All code in this project must be commented as if explaining to someone who is 10 years old.
Write comments in plain English. Every function, loop, condition, and non-obvious operation
should have a comment explaining:

- **What it does** — in simple words, not technical jargon
- **Why it exists** — what problem it solves, or what breaks if it's removed

Good example:
```javascript
// Loop through every item the user put in their cart.
// We add up the prices one by one to calculate the total they owe.
for (const item of cartItems) {
  total += item.price;
}
```

If in doubt, over-comment. A new developer (or future-you) should be able to read any
function in this codebase and understand it without asking anyone.

## vibe-check commands

Use these slash commands inside Claude Code to work like a professional developer:

| Command | When to use it | What it does |
|---|---|---|
| `/vc-bootstrap` | Once per machine or project | Sets up git, GitHub CLI, gitleaks, and a security `.gitignore` |
| `/vc-plan` | Before writing any new feature | Guides planning, creates a branch, writes a plan file, updates roadmap |
| `/vc-audit` | After finishing a feature | Reviews code for bugs and security issues — and fixes many of them |
| `/vc-ship` | When the branch is ready to push | Scans for secrets, checks tests, creates the GitHub pull request |
| `/vc-retro` | End of week or sprint | Looks back at what shipped, quantifies progress, asks reflection questions |
| `/vc-onboard` | Once, on a project with existing code | Maps existing code into feature areas, writes plan stubs to main |

**Recommended workflow:**

`/vc-bootstrap` → `/vc-plan` → [write code] → `/vc-audit` → `/vc-ship` → `/vc-retro` → repeat
```

---

Tell the user: "✓ CLAUDE.md updated with ELI10 commenting standard and vibe-check command guide."

---

## Step 4 — Write memory files

This step writes two memory files so Claude remembers what vibe-check is and how to use it
in every future conversation in this project. The user can ask questions about the suite
without having to explain it from scratch each time.

### Derive the memory directory path

Take `PROJECT_ROOT` from Step 1 (whether it came from git or `pwd`) and convert it to the memory path:

1. Replace every `/` in the path with `-`
   - The leading `/` becomes a leading `-`
2. Replace every `_` with `-`
3. The memory directory is: `~/.claude/projects/[converted-path]/memory/`

**Example:** `/home/user/my_project` → `~/.claude/projects/-home-user-my-project/memory/`

Save this as `MEMORY_DIR`.

### Check or create MEMORY.md

Use the Read tool to check whether `[MEMORY_DIR]/MEMORY.md` exists.

If it **does not exist**: use the Write tool to create `[MEMORY_DIR]/MEMORY.md` with this
content:

```markdown
# Memory Index

```

### Write vibe-check-overview.md

Use the Read tool to check whether `[MEMORY_DIR]/vibe-check-overview.md` exists.

If it **already exists**: skip — do not overwrite it.

If it **does not exist**: use the Write tool to create it with this content:

```markdown
---
name: vibe-check-overview
description: What vibe-check is, the 6 commands, and when to use each
metadata:
  type: project
---

vibe-check is a suite of 6 Claude Code slash commands that guide developers through
professional software workflows — plan before you code, review before you ship, and
keep a record of what you built and why.

Skills live in `.claude/commands/` in the project root. Artifacts go to `.vibe-check/`.

## The 6 commands

| Command | Purpose | When to run |
|---|---|---|
| `/vc-bootstrap` | One-time machine setup | First time on a new machine or project |
| `/vc-plan` | Feature planning | Before writing any code for a new feature |
| `/vc-audit` | Code review + auto-fix | After finishing implementation, before push |
| `/vc-ship` | Push + PR creation | When ready to ship — after audit |
| `/vc-retro` | Retrospective | End of week, sprint, or milestone |
| `/vc-onboard` | Existing project setup | Once, on a project that already has code |

## What each command does

**`/vc-bootstrap`** — Checks that git, GitHub CLI, and gitleaks are installed (installs
them if needed). Configures git name/email. Authenticates GitHub CLI. Adds a
security-baseline `.gitignore`. Writes a summary to `.vibe-check/vc-bootstrap.md`.

**`/vc-plan`** — Reads project context, guides a structured planning conversation (scope,
status quo, narrowest useful version, premise challenge, risks, security). Runs adversarial
subagent review of the plan. Creates a branch, writes a plan to
`.vibe-check/vc-plan/[branch].md`, and registers it in the roadmap at
`.vibe-check/vc-plan/roadmap.md`.

**`/vc-audit`** — Reads the diff between the feature branch and main. Applies review
lenses (security, error handling, auth, test coverage, etc.). Applies high-confidence fixes
directly with the Edit tool; asks for user decisions on ambiguous findings. Loops until two
consecutive passes find zero open findings (convergence). Records everything in the audit
artifact. Switches to FILE_READ_MODE when reviewing code with no diff (e.g., after vc-onboard).

**`/vc-ship`** — Runs gitleaks (secret scan — stops if secrets found). Runs linter. Checks
test coverage vs 80% goal, writes missing tests if needed. Scans for files that shouldn't
be committed. Checks commit history for non-bisectable patterns. Creates the GitHub PR with
a description and functional testing checklist. Updates the plan artifact and roadmap to
mark the branch as shipped.

**`/vc-retro`** — Reads git history for the last 31 days (scoped to your commits). Counts
commits, active days, most-changed files, planning discipline. Compares to previous retro
if one exists within 31 days. Asks 4 structured reflection questions. Writes the retro to
`.vibe-check/vc-retro/`.

**`/vc-onboard`** — Scans the existing codebase, detects tech stack. Proposes a breakdown
into feature chunks (max 15 files each). Sets up git if needed. Commits existing code as
baseline. Writes plan stubs to main for each chunk. After it finishes, run `/vc-plan` to
pick a chunk and start working.
```

### Write vibe-check-workflow.md

Use the Read tool to check whether `[MEMORY_DIR]/vibe-check-workflow.md` exists.

If it **already exists**: skip — do not overwrite it.

If it **does not exist**: use the Write tool to create it with this content:

```markdown
---
name: vibe-check-workflow
description: Recommended vibe-check workflow and key rules for using the suite correctly
metadata:
  type: project
---

## Standard workflow (new features)

```
/vc-bootstrap  ← run once per machine or project
     ↓
/vc-plan       ← start every new feature here (creates branch + plan)
     ↓
[write code]   ← implement on the feature branch
     ↓
/vc-audit      ← review and fix before shipping (must reach convergence)
     ↓
/vc-ship       ← push branch + create PR
     ↓
[merge PR]     ← in GitHub — always merge before starting the next feature
     ↓
/vc-retro      ← end of week or sprint — look back and reflect
     ↓
[repeat from /vc-plan]
```

## For existing projects (first time setup)

```
/vc-bootstrap  ← setup
     ↓
/vc-onboard    ← maps existing code into feature chunks, writes plan stubs to main
     ↓
/vc-plan       ← pick a chunk to work on (creates branch)
     ↓
/vc-audit      ← reviews chunk files directly (FILE_READ_MODE — no diff yet)
     ↓
/vc-ship       ← push + PR
     ↓
[merge PR, then repeat /vc-plan for the next chunk]
```

## Key rules

- Always start features from the default branch (main/master), not from another feature branch
- Always merge a PR before starting the next feature — stale branches cause merge conflicts
- `/vc-audit` must reach convergence (two consecutive clean passes) before running `/vc-ship`
- The plan artifact and roadmap are updated automatically when `/vc-ship` creates the PR
- If gitleaks finds secrets during `/vc-ship`, the push stops — remove the secrets from
  the commit and retry; do not add them to the gitleaks allowlist unless they are false positives
- If you are unsure what to do next, run `/vc-plan` from main — it reads your roadmap and
  routes you to the right place
```

### Update MEMORY.md index

Use the Read tool to read the current content of `[MEMORY_DIR]/MEMORY.md`.

Check whether a line containing `vibe-check-overview.md` is already present.

If it is **not present**: use the Edit tool to append these two lines to `MEMORY.md`:

```
- [vibe-check overview](vibe-check-overview.md) — what vibe-check is, the 6 commands, and when to use each
- [vibe-check workflow](vibe-check-workflow.md) — recommended workflow and key rules for using the suite
```

Tell the user: "✓ Memory files written — Claude will remember the vibe-check suite in future conversations."

---

## Step 5 — Done

Tell the user:

---

**vibe-check is installed.**

The 6 skill commands are ready in `.claude/commands/`. Your `CLAUDE.md` has been updated
with a code commenting standard and a quick-reference guide to the commands.

**Next step: run `/vc-bootstrap`**

This will:
- Check that git, GitHub CLI, and gitleaks are installed (and install them if missing)
- Configure your git name and email if not already set
- Connect GitHub CLI to your GitHub account
- Add a security `.gitignore` to block secrets and credentials from being committed

After bootstrap finishes, it will tell you exactly what to run next based on whether you
have an existing project or are starting fresh.

---
