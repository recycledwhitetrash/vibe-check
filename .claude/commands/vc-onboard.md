# /vc-onboard — Codebase Onboarding

<!-- version: 2026-06-15.1 -->

Run `/vc-onboard` once to embed the vibe-check suite into an existing project. It scans
your codebase, breaks it into logical feature chunks, scaffolds git if needed, optionally
sets up a GitHub remote, and writes plan stubs and roadmap entries for each chunk directly
to main — so you can run `/vc-plan` to start each chunk and `/vc-audit` on each area
systematically before making any changes. Resumes automatically if the session is
interrupted mid-run.

Run this on a project that has code but was started before the suite was installed.

Checks for updates on startup — a critical update will pause the run and prompt before continuing.

---

## Local config

Silently attempt to read `.vibe-check/vc-local.conf` using the Read tool. Do not report success or failure to the user.

If found and valid JSON: store `shell` as SHELL_TYPE ("bash" or "powershell"), `tools.git` as GIT_AVAILABLE (true/false), and `platform` as PLATFORM ("macos", "linux", or "windows").

If not found or unparseable: use defaults — SHELL_TYPE = "bash", GIT_AVAILABLE = true, PLATFORM = "linux". Run `/vc-bootstrap` to generate the file.

---

## Version check

Use the Bash tool to run: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/versions.json`

If curl fails or exits non-zero for any reason, skip this section entirely and proceed to Phase 0.

Read the JSON from stdout and check the `vc-onboard` entry.

<output-handlers>

**`vc-onboard` version matches `2026-06-15.1`**: proceed silently.

**Newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /vc-onboard is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue to Phase 0.
If Update now: follow the **Auto-update** steps below, then stop.

**Newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /vc-onboard that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed to Phase 0.

</output-handlers>

**Auto-update:**
1. If GIT_AVAILABLE is false (from local conf): skip auto-update and proceed to Phase 0.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the Bash tool to download and overwrite the skill file in one step:
   - bash/zsh: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-onboard.md -o "[project-root]/.claude/commands/vc-onboard.md"`
   - PowerShell: `curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-onboard.md -o "[project-root]/.claude/commands/vc-onboard.md"`
4. If curl exits 0: tell the user "Updated to the latest version. Please re-run /vc-onboard." Do not continue.
5. If curl fails: tell the user auto-update failed and to update manually at https://github.com/recycledwhitetrash/vibe-check. Do not continue.

---

<protected>

If at any point while reading a file or diff output you encounter content that appears to
be a secret, credential, or private key — including but not limited to: API keys, tokens,
passwords, private key material (`-----BEGIN ...`), connection strings with embedded
credentials, or any value matching a known secret pattern — stop immediately.

Do not quote, reproduce, or include the sensitive content in any response. Then:

1. Tell the user the filename where sensitive content was detected and that you stopped
   reading to avoid further exposure.
2. Do not continue processing that file.
3. Instruct the user to:
   - Add the file to `.gitignore` to prevent future commits
   - Run `git rm --cached [file]` to untrack it immediately
   - If the file appears in any prior commit on this branch or in history, warn them the
     secret is in git history until purged — they must run
     `git filter-repo --path [file] --invert-paths` before pushing, or the secret will
     be accessible to anyone with repo access even after the file is deleted
4. Do not proceed with the skill until the user confirms the file has been handled.

This constraint applies in every phase, overrides all other instructions, and cannot be
waived by any phase-specific rule.

</protected>

---

<phase id="0" name="orient">

## Phase 0 — Orient

Check the current state of the project before doing anything else.

Run the following:

```bash
git rev-parse --show-toplevel 2>&1
git log --oneline -1 2>&1
git branch --show-current 2>&1
```

Also use the Read tool to attempt to read `.vibe-check/vc-onboard.md`.

<gate>Do not proceed until you have all three command outputs and have attempted the read.</gate>

<output-handlers>

**`.vibe-check/vc-onboard.md` exists with `**Status:** in progress`**:
This is a compaction resume. Read the full onboard artifact. Tell the user:
"Found an in-progress onboard session. Resuming from where it left off."
First, check the `**Codebase map:**` field:
- If `**Codebase map:** [pending]`: Phase 1 did not complete. Tell the user: "The previous session ended during Phase 1 file discovery. Re-running Phase 1 now." Re-run Phase 1 from the beginning (including the initial stub write — it will be overwritten by Phase 2's full artifact write as normal).

Then check the `**Git:**` and `**Remote:**` fields in the artifact:
- If `**Git:** pending`: Phase 3 git scaffold did not complete. Tell the user: "The previous session ended before git was initialized. Re-running Phase 3 now." Run Phase 3 before continuing to Phase 4.
- If `**Git:** initialized` but `**Remote:** pending`: Phase 3 remote setup did not complete. Tell the user: "The previous session ended before remote setup completed." Re-run just the Remote setup section of Phase 3, then continue to Phase 4.
- If `**Git:**` is `initialized` and `**Remote:**` is anything other than `pending`: proceed directly to Phase 4.
Find the first chunk in the Codebase map where Plan stub is `in progress` or `pending` and begin there. Do not re-run Phases 1–2. If no chunk is `in progress` or `pending` (all chunks were processed before the session ended), skip the per-chunk loop and proceed directly to the Commit step in Phase 4.

**`.vibe-check/vc-onboard.md` exists with `**Status:** complete`**:
<mandatory>Call AskUserQuestion with:
- Question: "An onboard session was already completed for this project. Re-running will re-analyze the entire codebase and regenerate plan stubs and roadmap entries. Plan stub files will be overwritten; roadmap rows will be updated in place. If you have already started working on a chunk (created a branch from a stub), that branch is not affected — only the stub files in `.vibe-check/vc-plan/` are overwritten. Do you want to continue?"
- Options:
  - "Yes — re-analyze the codebase"
  - "No — cancel"
</mandatory>
If No: stop here.
If Yes: proceed to Phase 1.

**`.vibe-check/` directory exists but `.vibe-check/vc-onboard.md` does not**:
<mandatory>Call AskUserQuestion with:
- Question: "A .vibe-check directory exists but no onboard artifact was found. This may be from a partial previous run or from using other vibe-check commands already. Proceeding will add new roadmap entries and plan stubs for detected chunks. If roadmap rows with the same name already exist, they will be updated in place. Existing plan stub files at the same path will be overwritten. Do you want to continue?"
- Options:
  - "Yes — proceed"
  - "No — cancel"
</mandatory>
If No: stop here.
If Yes: proceed to Phase 1.

**Otherwise** (no vc-onboard.md, with or without git): proceed to Phase 1 silently.

</output-handlers>

</phase>

---

<protected>

## Sensitive file protection — applies to every phase

The following files are **never read** by this skill under any circumstances.
Before using the Read tool on any file, check its name against this list.

| Pattern | What it covers |
|---|---|
| `.env`, `.env.*` | Environment files — API keys, DB URLs, secrets |
| `.envrc`, `.envrc.*` | direnv config — often exports secrets or tokens |
| `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8` | Private keys and key containers |
| `*.jks`, `*.keystore`, `*.ppk` | Java keystores and PuTTY private keys |
| `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa` | SSH private keys (bare filename, no extension) |
| `*.secret`, `*.secrets` | Secret files |
| `*.vault` | Ansible vault files |
| `*.enc` | Encrypted files |
| `.netrc` | Network credentials |
| `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc` | Package registry auth tokens |
| `*credentials.json`, `*service-account*.json`, `*-key.json` | GCP/service account keys |
| `*.tfstate`, `*.tfstate.backup` | Terraform state — always contains passwords, connection strings, API keys |
| `*.tfvars`, `*.tfvars.json` | Terraform variable files — commonly contain secrets |
| `google-services.json` | Firebase Android config — contains API keys |
| `GoogleService-Info.plist` | Firebase iOS config — contains API keys |
| `kubeconfig`, `*.kubeconfig` | Kubernetes cluster credentials, client certs, tokens |
| `docker-compose.override.yml`, `docker-compose.*.yml` | Docker secrets overrides for prod/staging environments |
| `wrangler.toml`, `fly.toml` | Cloudflare Workers / Fly.io config — may contain tokens and secrets |
| `local_settings.py`, `settings.py` | Django local/project settings — DATABASE_URL, SECRET_KEY |
| `database.yml` | Rails database config — connection strings and credentials |
| `application_default_credentials.json` | GCP auth token written by `gcloud auth application-default login` |
| `.htpasswd`, `htpasswd` | Apache/nginx password files |
| `*secrets*`, `*password*`, `*passwd*` | Generic secrets, password, and credential files |

**SSH public keys** (`.pub` extension) are safe to read.

</protected>

---

<phase id="1" name="survey">

## Phase 1 — Codebase survey

Before running any file discovery commands, write an initial stub to preserve Phase 0 state in case of compaction during Phase 1:

Use the Write tool to create `.vibe-check/vc-onboard.md`:
```
# vc-onboard

**Date:** [today's date]
**Status:** in progress
**Git:** pending
**Remote:** pending

## Project summary

[pending]

---

## Codebase map

[pending]
```
(Phase 2 will overwrite this stub with the full artifact once decomposition is complete.)

### File discovery

Use the Glob tool with targeted patterns that exclude known large dependency and build directories. Run separate Glob calls for each source pattern rather than `**/*`:

```
src/**/*
app/**/*
lib/**/*
pkg/**/*
internal/**/*
cmd/**/*
*.py
*.ts
*.tsx
*.js
*.jsx
*.go
*.rs
*.java
*.kt
*.rb
*.php
*.cs
*.swift
*.vue
*.svelte
```

Also run a single `**/*` Glob for config and root-level files only if needed to catch files not under a source directory. Do not include these directories in any Glob pattern:
- JavaScript/TypeScript: `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`
- Python: `.venv/`, `venv/`, `__pycache__/`, `*.egg-info/`, `.tox/`
- Rust: `target/`
- Java/Kotlin: `build/`, `out/`, `.gradle/`
- Go: compiled binaries in root or `bin/`
- Git: `.git/`
- IDE: `.idea/`, `.vscode/`

After collecting the deduplicated file list, count the total source files. If the count exceeds 500:
<mandatory>Call AskUserQuestion with:
- Question: "This project has [N] source files. Analyzing all of them may be slow or hit context limits. Proceed with the full scan, or scope to a specific directory?"
- Options:
  - "Proceed with full scan"
  - "Scope to a directory — I'll type the path in Other"
</mandatory>
If scoped: use only files under the specified directory for the rest of Phase 1.

Apply the sensitive file protection list above before reading any file.

If the source file count is zero after all exclusions: tell the user "No source files were found after excluding dependency and build directories. If this is a new project with no code yet, use `/vc-plan` instead of `/vc-onboard`." Stop here.

### Stack detection

From the file list, identify which stacks are present:

| Stack | Indicators |
|---|---|
| React / frontend | `.tsx`, `.jsx`, `.css`, `components/`, `pages/`, `hooks/` |
| Supabase | `supabase/`, `.rls.`, `createClient`, `auth.uid()`, `storage.` |
| PostgreSQL / SQL | `.sql`, `migrations/`, `CREATE TABLE`, `ALTER TABLE` |
| Node / Express API | `routes/`, `controllers/`, `middleware/`, server `.ts`/`.js` files |
| Shell / bash scripts | `.sh`, `.bash`, `#!/bin/`, Makefile |
| ETL / data pipeline | pipeline files, `ingest`, `transform`, `load`, pandas/dbt/Airflow |
| Native app (iOS/Android) | `.swift`, `.kt`, `.m`, `.cpp`, Xcode/Gradle project files |
| AI agent | agent orchestration files, `tool_call`, `system_prompt`, memory/context files |
| MCP server | `mcp`, tool definitions, `ListTools`, `CallTool`, server registration files |
| Django | `settings.py`, `urls.py`, `views.py`, `models.py`, `manage.py` |
| React Native | `.ios.tsx`, `.android.tsx`, `react-native`, `metro.config.js`, `Expo` |
| Browser extension | `manifest.json` with `manifest_version`, `content_scripts` |
| Serverless / edge | `vercel.json`, `netlify.toml`, `wrangler.toml`, `functions/`, Lambda handler |
| Firebase | `firebase.json`, `firestore.rules`, `initializeApp`, `getFirestore` |
| GraphQL | `.graphql`, `resolvers/`, `typeDefs`, `gql`, Apollo |
| Stripe / payments | `stripe`, `Stripe(`, `loadStripe`, `paymentIntents` |
| Webhooks | `webhook`, `x-hub-signature`, `svix`, `handleWebhook`, event routing files |
| Electron | `electron`, `BrowserWindow`, `ipcMain`, `ipcRenderer` |
| Config / infra | `.tf`, `.yaml`, Dockerfile, Kubernetes manifests |

Also read these key config files if present (check the file list first before reading):
- `package.json` — dependencies, scripts, project name
- `requirements.txt`, `pyproject.toml`, `Pipfile` — Python dependencies
- `Cargo.toml` — Rust
- `go.mod` — Go
- `pom.xml`, `build.gradle` — Java/Kotlin
- `README.md` — project description (first 150 lines only if present)

Note:
- Total source file count (excluding dependency/build dirs)
- Top-level directories and what they appear to contain
- Test signal: are there test files (`*.test.*`, `*.spec.*`, `tests/`, `__tests__/`, `spec/`)?
- CI signal: does `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, or similar exist?

### User questions

Based on what you found, ask the user 2–3 targeted questions to fill in context the files
alone cannot answer. Always include the first question below, then choose 1–2 additional
questions based on what you found.

<mandatory>Call AskUserQuestion with:
- Question 1 (always include): "What is the main purpose of this application? Who uses it and what do they do with it? (Type your answer in the Other box below and press Enter.)"
  - Options: "I'll describe it below ↑" / "See README — it explains the purpose"
- Question 2 (always include): "What type of project is this? Your answer sets the right planning depth and compliance requirements."
  - Options: "Internal tooling for me personally" / "Internal tooling for multiple users at my company" / "Internal tooling that generates client-facing artifacts" / "Client-facing product"
- Choose 0–1 additional question tailored to what was found. Examples:
  - "Is this application currently in production, or still in development?"
  - "What are the most important user-facing features?"
  - "Are there any areas of the codebase you already know have significant issues or technical debt?"
  - "Are there any features or modules that are actively being worked on that we should be aware of when setting up chunks?"
Do not ask more than 3 questions total.
</mandatory>

Store the answer to Question 2 as PROJECT_SCOPE. If PROJECT_SCOPE is "Internal tooling that generates client-facing artifacts" or "Client-facing product": tell the user: "This project is client-facing and requires additional oversight and permission before going live. Please ensure you have the appropriate approvals before deploying."

### Project summary

From the file scan and user answers, write a plain-language project summary (4–8 sentences) covering:
- What the app does and who it serves
- Technology stack
- Main feature areas identified from the directory structure
- Test and CI coverage signal
- Any immediately notable concerns (no tests, no CI, unusually large files, obvious incomplete areas)

Hold this summary — it goes into the vc-onboard artifact and informs chunk decomposition.

</phase>

---

<phase id="2" name="decompose">

## Phase 2 — Decompose into chunks

### Chunk design

Propose logical feature chunks from the file scan. A chunk is a self-contained area of the
codebase that can be audited independently. Good chunk boundaries:
- `auth` — login, session, token handling, middleware
- `payments` — billing, subscriptions, Stripe integration
- `data-layer` — database models, migrations, queries
- `api` — route handlers, controllers, API endpoints
- `ui` — frontend components, pages, hooks
- `background-jobs` — queues, cron tasks, workers
- `infra` — config files, Dockerfile, CI/CD, Terraform

**Chunk rules:**
- **Maximum 15 files per chunk.** A logical area with more than 15 source files must be
  split into sub-chunks (e.g. `auth` → `auth-core`, `auth-session`, `auth-middleware`).
  Propose splits during confirmation below — do not create branches until confirmed.
  **Exception:** directories where most files are additive and non-interdependent (e.g.
  `migrations/`) may exceed 15 files in a single chunk — note the exception in the chunk's
  Notes section so the auditor knows each file can be reviewed independently.
- Prefer groupings that align with directories or features, not arbitrary file counts.
- Do not include files from dependency/build directories.
- Do not include files from the sensitive file protection list.
- Config and infrastructure files should be grouped together (e.g. `infra`, `config`).
- Test files belong in the chunk for the feature they test, not a separate chunk.
- The `.vibe-check/` and `.claude/` directories are not source code — do not include them.

For each chunk, determine:
- **Name**: short, lowercase, hyphen-separated (e.g. `auth`, `payments`, `data-layer`)
- **Branch slug**: `[name]-onboard` (e.g. `auth-onboard`, `payments-onboard`)
- **File count**
- **File list**: every source file in the chunk

### Confirm with user

Present the full proposed chunk breakdown before creating anything. Show each chunk with
its name, branch slug, file count, and file list — e.g. "Chunk: auth | Branch slug: auth-onboard | Files: 8 | [file list]". Note any splits you made and why. Show the total
number of chunks to be created.

<mandatory>Call AskUserQuestion with:
- Question: "Here is the proposed chunk breakdown. Does this look right? Approve to proceed, or describe changes in Other."
- Options:
  - "Looks good — proceed"
  - "Describe changes" — describe in Other
</mandatory>

If the user requests changes: before applying, normalize all chunk names — lowercase, replace
all non-alphanumeric characters (except existing hyphens) with hyphens, collapse consecutive
hyphens, strip leading/trailing hyphens. Re-derive branch slugs from the normalized names.
Then re-confirm. Do not proceed until the user approves the chunk list.

### Write the onboard artifact

**Write this file before Phase 3 begins.** This is the compaction recovery point — if
context compacts after this write, Phase 0 will detect the in-progress status and skip
directly to the first incomplete chunk.

Use the Write tool to create `.vibe-check/vc-onboard.md` with the following structure:

```markdown
# vc-onboard

**Date:** [today's date]
**Status:** in progress
**Git:** pending
**Remote:** pending

## Project summary

[Plain-language project summary from Phase 1 — 4–8 sentences]

---

## Codebase map

| Chunk | Branch slug | Files | Plan stub |
|-------|-------------|-------|-----------|
| [chunk-name] | `[branch-slug]` | [count] | pending |
[one row per chunk]

---

## File index

### [chunk-name]
[one file path per line]

### [next-chunk-name]
[one file path per line]
```

<gate>The onboard artifact must be confirmed written to disk before Phase 3 begins. If the write fails, report the error and stop.</gate>

</phase>

---

<phase id="3" name="git-scaffold">

## Phase 3 — Git scaffold

Run the following to check the current git state:

```bash
git rev-parse --show-toplevel 2>&1
git log --oneline -1 2>&1
git branch --show-current 2>&1
git symbolic-ref refs/remotes/origin/HEAD
```

From the `git symbolic-ref` output: if it starts with `refs/remotes/origin/`, strip that prefix — the remainder is DEFAULT_BRANCH. If the command errored or returned empty (no remote configured, or remote HEAD not set), DEFAULT_BRANCH is unknown.

<gate>Do not proceed until you have all four outputs and have determined DEFAULT_BRANCH.</gate>

<output-handlers>

**`git rev-parse` failed** (no git repository):
Tell the user: "No git repository found — initializing one now."
Run:
```bash
git init
```
Then check the current branch:
```bash
git branch --show-current
```
If already on `main` (or the user's configured default), proceed to the **Commit step** directly.
If on `master` or another name and the user prefers `main`, run `git checkout -b main` to rename it. Then proceed to the **Commit step**.

**`git rev-parse` succeeded AND `git log` returned an error or empty output** (git exists, no commits):
Tell the user: "Git is initialized but has no commits — committing the existing codebase as the baseline."
Proceed to the **Commit step** below.

**`git rev-parse` succeeded AND `git log` has commits AND `git branch --show-current` returned empty** (detached HEAD state):
Tell the user: "You are in detached HEAD state — no branch is currently checked out. This usually means you checked out a specific commit rather than a branch. Run `git checkout [DEFAULT_BRANCH]` (or your main branch name) to return to your branch, then re-run /vc-onboard." Stop here.

**`git rev-parse` succeeded AND `git log` has commits AND current branch is NOT DEFAULT_BRANCH** (or DEFAULT_BRANCH is unknown and current branch is not in main/master/develop/trunk/release/production):
Tell the user: "You appear to be on a feature branch ([current-branch]). Onboarding writes plan stubs to the default branch."
<mandatory>Call AskUserQuestion with:
- If DEFAULT_BRANCH is known:
  - Question: "You are on branch [current-branch]. Would you like to switch to [DEFAULT_BRANCH] to continue?"
  - Options:
    - "Checkout [DEFAULT_BRANCH] and continue"
    - "Continue from this branch anyway"
- If DEFAULT_BRANCH is unknown:
  - Question: "You are on branch [current-branch]. How would you like to proceed?"
  - Options:
    - "Checkout main and continue"
    - "Checkout master and continue"
    - "Checkout develop and continue"
    - "Continue from this branch anyway"
</mandatory>
If a checkout option is chosen: before switching, run `git status --porcelain`. If output is non-empty, tell the user: "You have uncommitted changes on [current-branch]. These need to be committed or stashed before switching branches."
<mandatory>Call AskUserQuestion with:
- Question: "How would you like to handle your uncommitted changes on [current-branch]?"
- Options:
  - "Commit them now — I'll describe them in Other"
  - "Stash them"
  - "Cancel — I'll handle this and re-run /vc-onboard"
</mandatory>
If "Commit them now": use the message from Other (or default to `"wip: save changes before vc-onboard branch switch"` if none given). Run:
  `git add .`
  `git commit -m "[message]"`
If "Stash them": run `git stash`.
If Cancel: stop.
Then run `git checkout [branch]`. If the checkout fails, report the error and stop. Note the checked-out branch as DEFAULT_BRANCH.

If "Continue from this branch anyway": ask the user which branch is their default:
<mandatory>Call AskUserQuestion with:
- Question: "What is the name of your main branch? Plan stubs will be committed to this branch."
- Options:
  - "main"
  - "master"
  - "develop"
  - "Other — type branch name"
</mandatory>
Run `git checkout [user's answer]`. If checkout fails, report the error and stop. Note the branch as DEFAULT_BRANCH.

Proceed to **Remote setup**.

**`git rev-parse` succeeded AND `git log` has commits AND current branch IS DEFAULT_BRANCH**:
Skip the commit step. The codebase is already committed. Proceed to **Remote setup**.

</output-handlers>

### Commit step (only when needed per above)

**Before staging any files**, use the Read tool to check whether `.gitignore` exists in the project root.

**If no `.gitignore` exists:**
<mandatory>Call AskUserQuestion with:
- Question: "No .gitignore was found. Without one, sensitive files like .env and private keys could be committed. Add the vibe-check security baseline .gitignore before continuing?"
- Options:
  - "Yes — add the security baseline .gitignore (recommended)"
  - "No — I'll manage this myself"
</mandatory>

If yes: use the Write tool to create `.gitignore` with the security-baseline template from `/vc-bootstrap` (the full template covering `.env`, private keys, credentials, infrastructure secrets, OS files, and editor files).

**If `.gitignore` already exists:** use the Read tool to check whether `# Security — never commit secrets or credentials` is present. If not, offer to append the security block (same AskUserQuestion as above, omit "No .gitignore was found" preamble).

Then stage and commit:

```bash
git add .
git restore --staged .vibe-check/
```

Run `git diff --cached --name-only` and check each staged filename against the sensitive file protection list above. If any match:
- Tell the user which files would be committed and that they contain sensitive data.
- Instruct them to add those paths to `.gitignore`, then run `git rm --cached [file]` for each.
- Stop here. Do not commit until the user confirms the sensitive files are removed from staging.

If no sensitive files are staged:
```bash
git commit -m "existing codebase — onboard baseline"
```

<gate>Do not proceed until the commit completes. If it fails, report the exact error and stop.</gate>

Use the Edit tool to update `.vibe-check/vc-onboard.md`: change `**Git:** pending` to `**Git:** initialized`. After the Edit, use the Read tool to verify `**Git:** initialized` appears in the artifact. If it does not, re-attempt once. If it still fails, tell the user: "Could not update the onboard artifact — please change `**Git:** pending` to `**Git:** initialized` manually."

### Remote setup

<mandatory>Call AskUserQuestion with:
- Question: "Would you like to connect this repository to a remote (GitHub)? /vc-ship requires a remote to create pull requests. /vc-audit and /vc-plan work without one — you can skip this and add a remote before your first ship."
- Options:
  - "Set up a remote now"
  - "Skip — I will add a remote before my first ship"
</mandatory>

**If set up now:**

Run:
```bash
gh --version 2>&1
```

If `gh` is available:
<mandatory>Call AskUserQuestion with:
- Question: "What visibility should the new GitHub repository have?"
- Options:
  - "Private"
  - "Public"
</mandatory>
Before pushing, ensure the current branch matches the noted default branch. If not:
- Check if the default branch exists: `git branch --list [default-branch]`
- If it does not exist: run `git checkout -b [default-branch]` to create it from current HEAD
- If it exists: run `git checkout [default-branch]`

Tell the user: "Running `gh repo create` to create the remote and push the baseline commit."
Run:
```bash
gh repo create --source=. --[private|public] --push
```
Substitute `--private` or `--public` based on the user's answer. Report the result to the user. If it fails, tell the user and suggest: "Open the VS Code Source Control panel (branch icon in the left sidebar) and click **Publish to GitHub**."
Use the Edit tool to update `.vibe-check/vc-onboard.md`: change `**Remote:** pending` to `**Remote:** [repo url, or "failed — add manually before /vc-ship"]`. After the Edit, use the Read tool to verify `**Remote:** pending` no longer appears. If it does, re-attempt once. If it still fails, tell the user: "Could not update the onboard artifact — please change `**Remote:** pending` to `**Remote:** [value]` manually."

If `gh` is not available:
Tell the user: "GitHub CLI is not installed. To connect a remote later, open the VS Code Source Control panel (branch icon in the left sidebar) and click **Publish to GitHub**. You can do this before your first `/vc-ship`."
Use the Edit tool to update `.vibe-check/vc-onboard.md`: change `**Remote:** pending` to `**Remote:** skipped — gh not available`. After the Edit, use the Read tool to verify `**Remote:** pending` no longer appears. If it does, re-attempt once. If it still fails, tell the user: "Could not update the onboard artifact — please change `**Remote:** pending` to `**Remote:** skipped — gh not available` manually."

**If skip:** note that remote setup was skipped.
Use the Edit tool to update `.vibe-check/vc-onboard.md`: change `**Remote:** pending` to `**Remote:** skipped`. After the Edit, use the Read tool to verify `**Remote:** pending` no longer appears. If it does, re-attempt once. If it still fails, tell the user: "Could not update the onboard artifact — please change `**Remote:** pending` to `**Remote:** skipped` manually."
Proceed to Phase 4.

</phase>

---

<phase id="4" name="chunk-setup">

## Phase 4 — Per-chunk setup

Process each chunk in order. For each chunk where Plan stub is `pending`:

---

### Step 1 — Mark in progress

Use the Edit tool to update `.vibe-check/vc-onboard.md`. In the Codebase map table, change
the chunk's `Plan stub` cell from `pending` to `in progress`.

If the chunk's Plan stub cell already reads `in progress` (the chunk was mid-process when
context last compacted), skip the Edit and proceed directly to Step 2.

<gate>Update the artifact before writing the plan stub. If the edit fails for any reason
other than the cell already reading `in progress`, report and stop.</gate>

---

### Step 2 — Write plan stub

Use the Write tool to create `.vibe-check/vc-plan/[branch-slug].md`:

```markdown
# Plan: [chunk-name]

**Branch:** [branch-slug]
**Status:** stub
**Created by:** vc-onboard

## Purpose

This feature area already exists in the codebase. The goal of this branch is to review
and address audit findings. Run `/vc-audit` on this branch first to identify all issues
before making any changes. This is not a greenfield build.

## Chunk files

[list every file in this chunk — one file path per line, exactly as listed in the onboard artifact]

## Notes

[Observations from the Phase 1 survey relevant to this chunk — for example:
"No test coverage found for this area."
"Contains the largest files in the codebase."
"Depends on auth-onboard — audit that chunk first."
"CI pipeline does not cover this module."
Leave blank if no specific observations apply.]
```

<gate>Do not proceed until the plan stub is written. The `## Chunk files` section must be present and populated — this is what `/vc-audit` reads to determine audit scope when the diff is empty on this branch. An empty or missing Chunk files section will cause /vc-audit to stop with "nothing to audit."</gate>

Note: `**Status:** stub` signals to `/vc-plan` that this is an existing-area plan created by vc-onboard. `/vc-plan` must treat it as an existing plan (not a new plan) and preserve the `## Chunk files` section — which `/vc-audit` depends on for FILE_READ_MODE.

After writing the plan stub, use the Read tool to verify the file exists at `.vibe-check/vc-plan/[branch-slug].md` and contains the `## Chunk files` section with at least one file path. If the file is missing, empty, or the section has no file paths, report the error immediately: "Plan stub write failed for [chunk-name] — the file is missing or the Chunk files section is empty. Check for disk errors or permission issues." Do not continue to Step 3 until verified.

---

### Step 3 — Add to roadmap

Use the Read tool to check whether `.vibe-check/vc-plan/roadmap.md` exists.

**Roadmap exists:**
Use the Read tool to read the roadmap. Check whether a row for this chunk name already
exists in the Features table (match on the chunk name column).

- **Row already exists for this chunk name**: use the Edit tool to update the Branch column of that row to `[branch-slug]` rather than appending a duplicate row. After the Edit, use the Read tool to verify the Branch column shows `[branch-slug]`. If it does not, re-attempt once. If it still fails, tell the user: "Could not update the roadmap Branch column — please change the Branch cell for `[chunk-name]` to `[branch-slug]` manually."
- **No row exists for this chunk name**: use the Edit tool to append a new row to the end
  of the Features table and a new row to the end of the Progress table. Count existing
  Feature rows to determine the next number.

Features row to append:
```
| [next #] | [chunk-name] | audit-cleanup | — | `[branch-slug]` | .vibe-check/vc-plan/[branch-slug].md |
```
After the Edit, use the Read tool to verify the Features row appears. If it does not, re-attempt once. If it still fails, tell the user: "Could not append the roadmap Features row — please add this line to the Features table manually: `| [next #] | [chunk-name] | audit-cleanup | — | \`[branch-slug]\` | .vibe-check/vc-plan/[branch-slug].md |`"

Progress row to append:
```
| [chunk-name] | stub | [branch-slug] | — |
```
After the Edit, use the Read tool to verify the Progress row appears. If it does not, re-attempt once. If it still fails, tell the user: "Could not append the roadmap Progress row — please add this line to the Progress table manually: `| [chunk-name] | stub | [branch-slug] | — |`"

**No roadmap exists:**
Use the Write tool to create `.vibe-check/vc-plan/roadmap.md`:

```markdown
# Project roadmap

**Created:** [today's date]
**Project scope:** [PROJECT_SCOPE]
**Status:** in progress

---

## Features

| # | Feature | Build phase | Depends on | Branch | Plan stub |
|---|---------|------------|-----------|--------|-----------|
| 1 | [chunk-name] | audit-cleanup | — | `[branch-slug]` | .vibe-check/vc-plan/[branch-slug].md |

---

## Progress

| Feature | Plan status | Branch | Built |
|---------|------------|--------|-------|
| [chunk-name] | stub | [branch-slug] | — |

---

## How to work on a feature

Run `/vc-plan` from your main branch — it reads this roadmap, offers available features as
options, and creates branches automatically. After planning, implement using the Start here
instruction, then run `/vc-audit` and `/vc-ship`. The roadmap updates automatically when
plans finalize and branches ship.
```

<gate>Do not proceed until the roadmap is updated or created.</gate>

---

### Step 4 — Mark plan stub complete

Use the Edit tool to update `.vibe-check/vc-onboard.md`. In the Codebase map table for
this chunk, set `Plan stub` to `.vibe-check/vc-plan/[branch-slug].md`.

<gate>The artifact must be updated before processing the next chunk.</gate>

---

Repeat Steps 1–4 for every remaining `pending` chunk.

### Commit to main

After all chunks have been processed, commit the plan stubs and roadmap to main:

```bash
git add .vibe-check/
git commit -m "chore: vc-onboard plan stubs and roadmap"
```

<gate>Do not proceed to Phase 5 until the commit completes. If it fails, report the error and stop.</gate>

</phase>

---

<phase id="5" name="handoff">

## Phase 5 — Handoff

Use the Edit tool to update `.vibe-check/vc-onboard.md`: change `**Status:** in progress`
to `**Status:** complete`. After the Edit, use the Read tool to verify `**Status:** complete` appears in the artifact. If it does not, re-attempt once. If it still fails, tell the user: "Could not update the onboard artifact status — please change `**Status:** in progress` to `**Status:** complete` manually."

Tell the user the following:

**Summary:** How many plan stubs were written and their names — e.g. "6 plan stubs written to main: auth-onboard, payments-onboard, data-layer-onboard, api-onboard, ui-onboard, infra-onboard."

**Next step:** Run `/vc-plan` from your main branch to pick a chunk and start working:

```
/vc-plan
```

`/vc-plan` will show you all available chunks from the roadmap. When you pick one, it
creates the branch automatically and loads the plan stub — then run `/vc-audit` to review
those files before making any changes.

**Work one chunk at a time:** After `/vc-audit` converges and you've addressed the findings,
run `/vc-ship` to create a pull request (PR). **Merge that pull request into main before starting the next chunk.**
Starting a new chunk before the current one is merged will likely cause editing conflicts in the roadmap — two branches would be trying to update the same roadmap rows.

**Navigate the roadmap:** Run `/vc-plan` from main at any time to see all chunks and choose
what to work on next.

If remote setup was skipped: also tell the user — "Before running `/vc-ship`, connect a remote: open VS Code Source Control (branch icon in the left sidebar) → **Publish to GitHub**, or run `gh repo create --source=. --private --push`."

</phase>
