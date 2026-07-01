---
description: Branch deep-walk code review — orients to the branch, selects lenses, and walks every changed surface with parallel adversarial and test-integrity agents until two clean passes converge.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - Glob
  - AskUserQuestion
---
<!-- AUTO-GENERATED from src/vc-audit.md.tmpl — do not edit directly -->

# /vc-audit — Branch Deep Walk Audit

<!-- version: 2026-07-01.1 -->

Drop `/vc-audit` at the start of any review session. It orients itself to the branch,
selects the right lenses for the code it finds, and walks every changed surface against
every applicable lens. During each pass, two agents run in the background in parallel with
the structured walk: an adversarial subagent that reviews the same diff independently to
find what the structured walk missed, and a test integrity agent that applies a 6-pattern
checklist to all new and modified test files (fixture shape mismatches, sync assertion on
async throw, fireEvent on disabled elements, prototype mutation restorability, implicit ARIA
role vs. explicit attribute, non-discriminating assertions). Both are collected at the end
of the pass.

The skill loops until you declare convergence (two consecutive clean passes with zero open findings). Each session
produces one artifact (scoped runs get their own separate artifact) that accumulates all
findings across passes — what was checked, found, fixed, deferred, and dismissed — so
reviewers have a complete record.

Supports scoped runs (`/vc-audit src/auth/`) for focused sessions, LARGE_DIFF detection
to avoid context exhaustion, automatic resume after compaction, and FILE_READ_MODE — when
used after `/vc-onboard`, automatically scans designated chunk files directly on branches
with no diff.

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

Read the JSON from stdout and check the `vc-audit` entry.

<output-handlers>

**`vc-audit` version matches `2026-07-01.1`**: proceed silently.

**Newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /vc-audit is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue to Phase 0.
If Update now: follow the **Auto-update** steps below, then stop.

**Newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /vc-audit that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed to Phase 0.

**Fetched version is older than `2026-07-01.1`**: proceed silently. (This can happen with CDN caching or a rollback — the local version is already newer.)

</output-handlers>

**Auto-update:**
1. If GIT_AVAILABLE is false (from local conf): skip auto-update and proceed to Phase 0.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the Bash tool to download and overwrite the skill file in one step:
   - bash/zsh: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-audit.md -o "[project-root]/.claude/commands/vc-audit.md"`
   - PowerShell: `curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-audit.md -o "[project-root]/.claude/commands/vc-audit.md"`
   Also refresh the per-stack lens catalog in `.claude/lenses/`. Fetch the manifest, then download each listed file:
   - bash/zsh:
     ```bash
     mkdir -p "[project-root]/.claude/lenses"
     curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt | while read -r f; do
       curl -fsSL "https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$f" -o "[project-root]/.claude/lenses/$f"
     done
     ```
   - PowerShell:
     ```powershell
     New-Item -ItemType Directory -Force -Path "[project-root]\.claude\lenses" | Out-Null
     (curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt) -split "`n" | Where-Object { $_ } | ForEach-Object {
       curl.exe -fsSL "https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$_" -o "[project-root]\.claude\lenses\$_"
     }
     ```
4. If curl exits 0: tell the user "Updated to the latest version — reloading and resuming." Then use the Read tool to read `[project-root]/.claude/commands/vc-audit.md`. Proceed to Phase 0 of the updated skill, following the instructions just read. Do not re-run the version check — the update is already complete. Do NOT stop, do NOT ask the user to re-run the skill — continue executing from Phase 0 immediately.
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

## Phase 0 — Orient to the branch

**Optional path scope:** `/vc-audit` can be scoped to a subset of the diff by passing paths as `$ARGUMENTS`. Three forms are supported:
- A single directory: `/vc-audit src/auth/`
- A single file: `/vc-audit src/auth/session.ts`
- A space-separated list of files or directories: `/vc-audit src/auth/session.ts src/middleware/`

If `$ARGUMENTS` was provided, append all paths to every `git diff` command as trailing path filters after the sensitive file exclusions — e.g. `git diff BASE...HEAD -- ':!...' src/auth/session.ts src/middleware/`. A scoped audit gets its own artifact — separate from the full-branch audit — so focused sessions never overwrite each other or the full audit. See Phase 3 for artifact naming.

Run the following to understand what this branch actually changes:

```bash
git branch --show-current
git for-each-ref --format='%(refname:short)' refs/heads/
git rev-parse HEAD~1
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null
```

<gate>Do not proceed past this block until you have command output. Determine BASE_BRANCH and handle all edge cases before continuing:</gate>

<output-handlers>

- **Multiple default branches detected** (e.g. both `main` and `master` exist in the refs list): call AskUserQuestion — "Multiple base branches were found: [list them]. Which one will this branch be merged into?" — list each detected default branch as its own option. Use the user's answer as BASE_BRANCH in all subsequent commands.
- **No `main`, `master`, or `develop` in the refs list**:
  <mandatory>Call AskUserQuestion with:
  - Question: "What is the name of the base branch this branch will be merged into?"
  - Options:
    - "main"
    - "master"
    - "develop"
  </mandatory>
  (Use Other to type a custom branch name.) Use the user's answer as BASE_BRANCH in all subsequent commands.
- **Current branch name matches a default branch name**: call AskUserQuestion — "You're on `[branch]`, which is the base branch. The audit is designed for feature branches. Would you like to audit recent commits on this branch, or switch to a different branch first?"
  - Options: "Audit recent commits on this branch" / "Switch to a different branch first — I'll come back"
  - If "Switch to a different branch first": stop and wait.
  - If "Audit recent commits": call a second AskUserQuestion — "How many recent commits should be included in this audit?"
    - Options: "Last 1 commit" / "Last 5 commits" / "Last 10 commits" (Other for custom value)
    - Use the selected number as N. Run `git rev-parse HEAD~N` to validate it exists. If the command succeeds, set BASE_BRANCH to `HEAD~N`. If it errors (repo has fewer than N commits), set BASE_BRANCH to `4b825dc642cb6eb9a060e54bf8d69288fbee4904` (the git empty tree hash) and tell the user: "The repo has fewer than N commits — auditing all available commits instead."
- **`git rev-parse HEAD~1` returned an error**: this is the initial commit. Use `4b825dc642cb6eb9a060e54bf8d69288fbee4904` (the git empty tree hash) as BASE_BRANCH in all subsequent commands. The entire commit is the diff; all files are new.
- **`git branch --show-current` returned empty**: the repo is in detached HEAD state. Run `git branch` to list all local branches.
  <mandatory>Call AskUserQuestion with:
  - Question: "The repo is in detached HEAD state — no branch is currently checked out. Which branch are you working on?"
  - Options: list each local branch as its own option, plus "Enter the branch name above ↑" as a final option (ensures at least 2 options even if only 1 local branch exists).
  </mandatory>
  - Run `git checkout [selected branch name]` to switch to that branch.
  - Re-read `git branch --show-current` to confirm CURRENT_BRANCH, then continue normally.
- **Otherwise**: derive BASE_BRANCH using this priority chain:
  1. From the `git symbolic-ref refs/remotes/origin/HEAD` output: if it returned a value, strip the `refs/remotes/origin/` prefix directly — do not use shell utilities. Use the result as BASE_BRANCH.
  2. If step 1 returned nothing: run `git remote set-head origin -a 2>/dev/null` to fetch the remote HEAD, then re-run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null`. If it now returns output: strip the prefix and use as BASE_BRANCH. (Repos created with `git init` + push rather than `git clone` do not have this reference set locally — this step populates it.)
  3. If no value yet: look for a branch in the `git for-each-ref` output whose name is exactly `main`, `master`, or `develop` — partial matches do not count. Use the first match as BASE_BRANCH.

**In all subsequent git commands, substitute BASE_BRANCH with the value determined above.**

</output-handlers>

Now run the analysis commands to understand what the branch changes:

First, identify any tracked files that are gitignored (e.g., dependencies committed before `.gitignore` was added):

```bash
git ls-files --cached --ignored --exclude-standard 2>/dev/null
```

Note any paths returned. If many files share a common directory (e.g., `node_modules/lodash/index.js`), consolidate to a directory-level exclusion (`:!node_modules/**`). Add these as additional `:!path` exclusions in the commands below.

```bash
git log BASE_BRANCH...HEAD --oneline
git diff BASE_BRANCH...HEAD --stat
git diff BASE_BRANCH...HEAD --name-only -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!.claude/**' ':!.vibe-check/**' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' ':!package-lock.json' ':!yarn.lock' ':!pnpm-lock.yaml' ':!npm-shrinkwrap.json' ':!composer.lock' ':!Gemfile.lock' ':!poetry.lock' ':!Pipfile.lock' ':!Cargo.lock' ':!go.sum' ':!go.work.sum' ':!package.json' ':!vite.config.*' ':!webpack.config.*' ':!rollup.config.*' ':!esbuild.config.*' [gitignored tracked files as :!path exclusions] [scope paths if $ARGUMENTS provided]
git diff BASE_BRANCH...HEAD --shortstat -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!.claude/**' ':!.vibe-check/**' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' ':!package-lock.json' ':!yarn.lock' ':!pnpm-lock.yaml' ':!npm-shrinkwrap.json' ':!composer.lock' ':!Gemfile.lock' ':!poetry.lock' ':!Pipfile.lock' ':!Cargo.lock' ':!go.sum' ':!go.work.sum' ':!package.json' ':!vite.config.*' ':!webpack.config.*' ':!rollup.config.*' ':!esbuild.config.*' [gitignored tracked files as :!path exclusions] [scope paths if $ARGUMENTS provided]
git status --porcelain
```

<gate>Do not proceed past this block until you have command output.</gate>

From the output above:
- Scan the `--name-only` file list for stack indicators (package managers, config/infra files, Supabase paths, scripts, ETL patterns, AI/MCP patterns) — these drive lens selection in Phase 1.
- Parse `git status --porcelain` output: filter out any line whose path starts with `.vibe-check/` or `.claude/`. From the remaining lines store:
  - UNCOMMITTED_TRACKED: paths from lines with `M`, `A`, or `R` prefix (staged or unstaged tracked changes). Apply the same sensitive file exclusions as the `--name-only` command above.
  - UNTRACKED_FILES: paths from `??` lines, applying the same sensitive file exclusions. These are new files never added to git — no diff exists; the walk will use the Read tool for them.
- **`--name-only` returned zero files but `git diff BASE_BRANCH...HEAD --stat` (unfiltered, run above) showed files**: all changed files on this branch were excluded from audit (sensitive credentials, build artifacts, or gitignored paths). Run `git diff BASE_BRANCH...HEAD --name-only` (no exclusions) to get the full list. Then:
  1. Create a high-severity finding for each file returned: `F-NNN | high (9/10) | [filename] — sensitive or excluded file modified on this branch; contents not audited; review manually before shipping.`
  2. Write these findings to the audit artifact (create it first if it doesn't exist, using the Phase 3 template).
  3. Tell the user: "All changes on this branch are in files excluded from audit (sensitive credentials or build artifacts). Review the files listed in the artifact manually before shipping." Stop.
- **`--shortstat` is empty** (zero committed files changed vs BASE_BRANCH) **AND current branch is not the default branch**:
  - If UNCOMMITTED_TRACKED or UNTRACKED_FILES is non-empty: real work is in progress. Run `git diff BASE_BRANCH --shortstat -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!.claude/**' ':!.vibe-check/**' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' ':!package-lock.json' ':!yarn.lock' ':!pnpm-lock.yaml' ':!npm-shrinkwrap.json' ':!composer.lock' ':!Gemfile.lock' ':!poetry.lock' ':!Pipfile.lock' ':!Cargo.lock' ':!go.sum' ':!go.work.sum' ':!package.json' ':!vite.config.*' ':!webpack.config.*' ':!rollup.config.*' ':!esbuild.config.*'` to get the tracked-change insertion count (excluding .claude/ and .vibe-check/). For untracked files (UNTRACKED_FILES): run `wc -l` on each file and sum the counts — add this to the insertion total. Add the number of UNTRACKED_FILES to the file count. Tell the user: "No commits on this branch yet — [N] uncommitted file(s) detected (plus [U] untracked). Auditing working tree changes vs [BASE_BRANCH]." Proceed.
  - If both are empty: check whether a plan stub exists at `.vibe-check/vc-plan/[branch-slug].md` and contains a `## Chunk files` section.
    - If plan stub with `## Chunk files` found and the section lists at least one file path: set FILE_READ_MODE = true. Note the file list from that section — this branch was set up by `/vc-onboard` and the audit will scan those files directly rather than a diff. Tell the user: "No changes detected vs [BASE_BRANCH]. A chunk file list was found in the plan stub — scanning chunk files directly instead of a diff." Proceed directly to Phase 1 using the chunk file extensions and paths for stack detection — skip the diff read and plan context check below.
    - If plan stub with `## Chunk files` found but the section is empty (no file paths listed): tell the user "The `## Chunk files` section in the plan stub is empty — nothing to audit in FILE_READ_MODE. Check the plan stub at `.vibe-check/vc-plan/[branch-slug].md` and ensure the section lists the files this branch covers." Stop.
    - If no plan stub or no `## Chunk files` section: tell the user "No changes detected vs [BASE_BRANCH] and no chunk file list was found. There is nothing to audit on this branch yet — make some changes first, then re-run /vc-audit." Stop.
- LARGE_DIFF check: if committed shortstat was empty but uncommitted/untracked files exist, use the filtered `git diff BASE_BRANCH --shortstat` (excluding `.claude/**` and `.vibe-check/**`) file count plus UNTRACKED_FILES count as total files, and the filtered shortstat insertion count plus the sum of `wc -l` over untracked files as total insertions. If total files > 15 or total insertions > 800, this is a **LARGE_DIFF** — call AskUserQuestion: "This branch touches N files / ~M lines, which may be too large to fully audit in one context window. How would you like to proceed?"
- Options:
  - "Scope to a directory — re-run as `/vc-audit src/some-dir/`"
  - "Scope to specific files — re-run as `/vc-audit file1.ts file2.ts`"
  - "Proceed anyway — accept that some surfaces may need re-auditing if context compacts mid-pass"

Respect the user's choice before continuing.

If the user chooses **option 1 ("Scope to a directory")**: stop here and give them these instructions:

"To audit just one directory:

1. Find the directory path you want to focus on. Run `git diff [BASE_BRANCH]...HEAD --name-only` to see all changed files — look for a folder where most of the changes are grouped (e.g. `src/auth/`, `app/api/`, `lib/payments/`).

2. Re-run the audit scoped to that directory:
   ```
   /vc-audit src/auth/
   ```
   Replace `src/auth/` with your chosen directory path.

3. The audit will only review changes inside that directory. When you're done with one area, run `/vc-audit` again with a different directory to cover the rest."

Stop. Do not continue the audit.

If the user chooses **option 2 ("Scope to specific files")**: stop here and give them these instructions:

"To audit specific files only:

1. Find the files you want to focus on. Run `git diff [BASE_BRANCH]...HEAD --name-only` to see the full list.

2. Re-run the audit with the files you care about most:
   ```
   /vc-audit src/auth/login.ts src/auth/session.ts
   ```
   List as many files as you want, separated by spaces.

3. When you're done with those files, run `/vc-audit` again with a different set to cover the rest."

Stop. Do not continue the audit.

### Stack detection

From the file list (`--name-only` output above), identify which of the following stacks are in play. Per-surface diffs are read in Phase 4 — do not read the full diff here.
**More than one can apply.**
**If FILE_READ_MODE is true:** substitute the chunk file paths and their extensions for "the file list" — no diff is available; derive stack indicators from filenames and directory names only.
**If UNTRACKED_FILES is non-empty:** include those paths and their extensions in the file list for stack detection.

| Stack | Indicators |
|---|---|
| React / frontend | `.tsx`, `.jsx`, `.css`, `components/`, `pages/`, `hooks/` |
| Supabase | `supabase/`, `.rls.`, RPC functions, `createClient`, `auth.uid()`, `storage.` |
| PostgreSQL / SQL | `.sql`, `migrations/`, stored procedures, `CREATE TABLE`, `ALTER TABLE` |
| Node / Express API | `routes/`, `controllers/`, `middleware/`, `.ts`/`.js` server files |
| Shell / bash scripts | `.sh`, `.bash`, `#!/bin/`, cron entries, Makefile targets |
| ETL / data pipeline | pipeline files, `ingest`, `transform`, `load`, `seed`, pandas/dbt/Airflow |
| Native app (iOS/Android/desktop) | `.swift`, `.kt`, `.m`, `.cpp`, Xcode/Gradle project files |
| AI agent | agent orchestration files, `tool_call`, `system_prompt`, memory/context files |
| MCP server | `mcp`, tool definitions, `ListTools`, `CallTool`, server registration files |
| Django | `settings.py`, `urls.py`, `views.py`, `models.py`, `serializers.py`, `manage.py`, `apps.py` |
| React Native | `.ios.tsx`, `.android.tsx`, `react-native`, `AppRegistry`, `metro.config.js`, `Expo`, `app.json` |
| Browser extension | `manifest.json` with `manifest_version`, `content_scripts`, `background` service worker |
| Serverless / edge | `vercel.json`, `netlify.toml`, `wrangler.toml`, `functions/`, Lambda `handler.ts`, `export default { fetch }` |
| Firebase | `firebase.json`, `firestore.rules`, `initializeApp`, `getFirestore`, `functions/index.js` |
| GraphQL | `.graphql`, `schema.graphql`, `resolvers/`, `typeDefs`, `gql`, Apollo, Pothos, Nexus |
| Webhooks | webhook handler files, `stripe.webhooks`, `X-Hub-Signature`, `svix`, `constructEvent` |
| Stripe / payments | `stripe`, `Stripe(`, `loadStripe`, `paymentIntents`, `checkout.sessions`, `subscriptions` |
| Discord / Slack / Telegram bots | `discord.js`, `@slack/bolt`, `telegraf`, `bot.on(`, `InteractionCreate`, `client.login` |
| Electron | `electron`, `BrowserWindow`, `ipcMain`, `ipcRenderer`, `contextBridge`, `app.on('ready')` |
| Config / infra | `.tf`, `.yaml`, `.env`, Dockerfile, Kubernetes manifests |

### Plan context

Check whether a vc-plan artifact exists for this branch:

1. Slugify the current branch name: lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens.
2. Use the Read tool to check for `.vibe-check/vc-plan/[branch-slug].md`.

<output-handlers>

**If the plan artifact exists:** Read it. Extract and note:
- The selected approach and its stated reversibility
- The "Not in scope" items — any diff changes touching these are scope drift findings
- The definition of done criteria — use these to inform what to look for in the walk
- The identified risks — check whether any have materialized as code problems

Summarise the plan context in 2–3 sentences before continuing to Phase 1. This context
informs lens selection and shapes what counts as a finding in Phase 4.

**If the plan artifact does not exist:**
<mandatory>Call AskUserQuestion with:
- Question: "No vc-plan artifact was found for this branch. Running vc-plan before vc-audit gives the audit important context: what approach was chosen, what is explicitly out of scope, and what risks were identified. You can pause now and run /vc-plan first, or continue the audit without plan context. Recommendation: continue if the branch is small or well-understood; pause if this is a larger feature."
- Options:
  - "Continue without plan context — proceed with the audit"
  - "Pause — I will run /vc-plan first"
</mandatory>

If the user pauses: stop here. Do not continue to Phase 1.
If the user continues: note "No plan artifact — scope drift and done-criteria checks will be skipped." and proceed to Phase 1.

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
| `local_settings.py`, `settings.py` | Django local settings — DATABASE_URL, SECRET_KEY |
| `database.yml` | Rails database config — connection strings and credentials |
| `application_default_credentials.json` | GCP auth token written by gcloud auth application-default login |
| `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8` | Private keys and key containers |
| `*.jks`, `*.keystore`, `*.ppk` | Java keystores and PuTTY private keys |
| `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa` | SSH private keys (bare filename, no extension) |
| `*.secret`, `*.secrets` | Secret files |
| `*.vault` | Ansible vault files |
| `*.enc` | Encrypted files |
| `*secrets*`, `*password*`, `*passwd*` | Generic secrets, password, and credential files |
| `.netrc` | Network credentials |
| `*credentials.json`, `*service-account*.json`, `*-key.json` | GCP/service account keys |
| `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc` | Package registry auth tokens |
| `*.tfstate`, `*.tfstate.backup` | Terraform state — always contains passwords, connection strings, API keys |
| `*.tfvars`, `*.tfvars.json` | Terraform variable files — commonly contain secrets |
| `kubeconfig`, `*.kubeconfig` | Kubernetes cluster credentials, client certs, tokens |
| `google-services.json` | Firebase Android config — contains API keys |
| `GoogleService-Info.plist` | Firebase iOS config — contains API keys |
| `docker-compose.override.yml`, `docker-compose.*.yml` | Docker secrets overrides for prod/staging environments |
| `wrangler.toml`, `fly.toml` | Cloudflare Workers / Fly.io config — may contain tokens and secrets |
| `.htpasswd`, `htpasswd` | Apache/nginx password files |

**SSH public keys** (`.pub` extension) are safe to read — they are not sensitive.

**If a blocked file appears in `git diff --name-only`** (it was modified on this branch),
create a finding without reading its contents:
`F-NNN | high (9/10) | [filename] — sensitive file modified on this branch; review
whether secrets were added, rotated, or accidentally committed`

**If blocked file content appears in diff output despite the exclusions** (e.g., a
filename variant the glob didn't catch), do not quote, reproduce, or process the
contents. Note the filename only.

</protected>

<artifact-write-rules>

Shell and interpreter scripts may never write to `.vibe-check/**`. Use the Edit or Write tool only.

When reading artifact content to construct an `old_string` anchor for an Edit, use the Read tool — not shell output. Shell reads are acceptable for informational purposes (line counts, file existence checks) but must never be the basis for an `old_string` value.

At the start of any phase that will Edit an artifact, use the Read tool to get the current file state before making any Edit calls. Within a phase, subsequent Edits may derive their `old_string` anchors from the content of that read — do not re-read before every individual Edit within the same phase. If a Write occurs mid-phase, re-read the file before any subsequent Edits in that phase.

</artifact-write-rules>


<edit-failure-protocol>

If the Edit tool returns "String to replace not found":

1. **Do not diagnose. Do not switch to a shell script or interpreter.** Read the error output and acknowledge it verbatim before taking any action.
2. Use the Read tool to get the current exact text of the file. Construct the shortest unique anchor (1–2 lines) from what you just read. Retry the Edit once.
3. If the retry fails: use the Read tool to read the **entire file** fresh. Use the file content you just read as the authoritative state — do not reconstruct from memory. Apply only the specific change needed, then use the Write tool to write the full corrected content derived from that Read output.
4. If the Write tool also fails: stop. Give the user the exact intended content to apply manually. Do not continue until the user confirms the file is correct.

This ladder is mandatory. Do not improvise a recovery path not in this list.

</edit-failure-protocol>


---

<phase id="1" name="select-lenses">

## Phase 1 — Select lenses

The lens catalog is split into per-stack files under `.claude/lenses/`. **Load only the
lenses for the stacks you actually detected** — this keeps the catalog out of context for
stacks that don't apply. Never exclude a lens for a stack that IS in play because "we're
not focusing on that" — if a detected stack's lens could catch something, it loads.

<mandatory>Read the lens files for this audit now, using the Read tool, before selecting:

1. **Always** read `.claude/lenses/universal.md` — the universal lenses apply to every audit.
2. For **each stack you detected in Phase 0**, read its lens file from this manifest:

| Stack (detected in Phase 0) | Lens file to read |
|---|---|
| React / frontend | `.claude/lenses/react-frontend.md` |
| React Native | `.claude/lenses/react-native.md` |
| Browser extension | `.claude/lenses/browser-extension.md` |
| Node / Express API | `.claude/lenses/node-express-api.md` |
| Django | `.claude/lenses/django.md` |
| Serverless / edge | `.claude/lenses/serverless-edge.md` |
| Supabase | `.claude/lenses/supabase.md` |
| Firebase | `.claude/lenses/firebase.md` |
| PostgreSQL / SQL | `.claude/lenses/postgresql-sql.md` |
| GraphQL | `.claude/lenses/graphql.md` |
| Webhooks | `.claude/lenses/webhooks.md` |
| Stripe / payments | `.claude/lenses/stripe-payments.md` |
| Shell / bash scripts | `.claude/lenses/shell-bash-scripts.md` |
| ETL / data pipeline | `.claude/lenses/etl-data-pipeline.md` |
| Discord / Slack / Telegram bots | `.claude/lenses/discord-slack-telegram-bots.md` |
| Native app (iOS/Android/desktop) | `.claude/lenses/native-app-ios-android-desktop.md` |
| Electron | `.claude/lenses/electron.md` |
| AI agent | `.claude/lenses/ai-agent.md` |
| MCP server | `.claude/lenses/mcp-server.md` |
| Config / infra | `.claude/lenses/config-infra.md` |

   (Paths are relative to the project root. Every stack in the Phase 0 detection table has a
   matching lens file in the manifest above. If you somehow detected a stack that is not
   listed here, the universal lenses cover it — do not invent a filename.)

If a lens file you need does not exist on disk, refresh the catalog first, then re-read:
- bash/zsh:
  ```bash
  mkdir -p "[project-root]/.claude/lenses"
  curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt | while read -r f; do
    curl -fsSL "https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$f" -o "[project-root]/.claude/lenses/$f"
  done
  ```
- PowerShell:
  ```powershell
  New-Item -ItemType Directory -Force -Path "[project-root]\.claude\lenses" | Out-Null
  (curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt) -split "`n" | Where-Object { $_ } | ForEach-Object {
    curl.exe -fsSL "https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$_" -o "[project-root]\.claude\lenses\$_"
  }
  ```

The selected lens files must be in context before you select. State your selection in the
audit artifact before walking anything.</mandatory>

</phase>

---

<phase id="2" name="map-surfaces">

## Phase 2 — Generate the surface map

Before walking, explicitly enumerate every system surface in scope for this branch.
Derive the list from the issue description and the diff — do not use a fixed template.

**If FILE_READ_MODE is true:** derive the surface map from the chunk file list in the plan stub. Use the file paths, extensions, and directory names — no diff is available. Create one surface entry per chunk file (or per logical unit within a file if it has multiple distinct responsibilities).
**If UNTRACKED_FILES is non-empty:** include each untracked file as a surface entry. Mark it as `(untracked — Read tool)` so the walk step knows to read it rather than diff it.

Write the surface map as a markdown table with exactly this header:

```
| # | Surface | Category | Entry points | What it trusts |
|---|---|---|---|---|
```

For each row:
- **#** — sequential number starting at 1
- **Surface** — a specific name (e.g., "user profile RPC function", "nightly CSV export script", "MCP file-read tool", "checkout ETL pipeline")
- **Category** — one of: auth boundary / data store / IPC channel / file system path / network endpoint / process boundary / config source / LLM interface / tool surface
- **Entry points** — how does a caller (adversarial or faulty) reach it? what arguments or inputs does it accept?
- **What it trusts** — what does it assume about its inputs that isn't enforced?

This table drives the walk. Every row must be walked in every pass. If you discover a
surface mid-walk, add a row to the table and walk it before completing the pass.

**Minimum granularity:** one row per changed file or logical unit. A single row for
"the auth layer" that covers ten changed files is not sufficient. Vague surface map entries
produce vague walks and make it impossible to verify coverage. If a file has multiple
distinct responsibilities, split it into multiple rows.

**Test files** (`*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`): include as surfaces if they
appear in the diff. Walk them for test *correctness* only — wrong assertions, bad async handling
(`setTimeout` instead of `act()`), missing teardown causing test pollution, mocks that hide real
production behavior. Do NOT enumerate missing test scenarios or coverage gaps; vc-ship's quality
gate handles coverage.

</phase>

---

<phase id="3" name="initialize-artifact">

## Phase 3 — Initialize or continue the audit artifact

Check for an existing artifact for this branch:

```bash
git branch --show-current
```

<gate>Do not proceed past this step until you have computed the artifact path and checked whether it exists.</gate>

Compute the artifact path from the branch name:
1. Take the branch name output above. Slugify it: lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens. This is the branch slug.
2. If `$ARGUMENTS` was provided:
   - **Single path**: strip any trailing `/`, then apply the same rule (lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens) to produce the path slug.
   - **Multiple paths**: derive a suggested name from the shared context — use the common ancestor directory if the paths share one, or combine the first two filenames without extensions (e.g. `session-middleware`). Then:
     <mandatory>Call AskUserQuestion with:
     - Question: "Multiple paths were provided. What should this scoped audit be called? This becomes part of the artifact filename. Select the suggestion or type a custom name in the Other box."
     - Options:
       - "[suggested name based on context]" (Recommended)
       - "Enter a custom name above ↑"
     </mandatory>
     Use the chosen or typed name as the path slug (apply the same slugification rule above).
   - Artifact path: `.vibe-check/vc-audit/[branch-slug]--[path-slug].md`
3. Otherwise: artifact path is `.vibe-check/vc-audit/[branch-slug].md`

Use the Read tool to check whether the artifact exists at that path.

**The artifact is the source of truth.** Always read the artifact at the start of each pass
to derive the current pass number, all existing finding numbers, and clean pass history.
Never reconstruct these from memory — context grows and degrades across passes; the file
does not.

**If the artifact exists:** Read it using the Read tool. Check the `**Status:**` field in the artifact header.

**If Status is `STOPPED`:**
<mandatory>Call AskUserQuestion with:
- Question: "This audit was previously stopped. Would you like to continue from where you left off, or start a new audit for this branch?"
- Options:
  - "Continue from where I stopped"
  - "Start a new audit (replaces the existing artifact)"
</mandatory>
If "Start a new audit": use the Write tool to overwrite the existing artifact with a fresh header (follow the "artifact does not exist" path below — create the artifact). Do not continue until the new artifact exists on disk.
If "Continue from where I stopped": proceed as if Status were IN PROGRESS.

**If Status is `IN PROGRESS` (or "Continue from where I stopped" was chosen):** Note the current pass number and all rows with Status = Open in the findings table. Continue from where the last pass left off — re-walk every surface from scratch, but use prior finding numbers for known issues.

**If the artifact does not exist:** Create the artifact with the header below, setting `**Subagents:** enabled`. Write it to the computed artifact path using the Write tool. The Write tool creates parent directories automatically. Do not continue until the file exists on disk.

<mandatory>The `## Findings` section must be a flat table — exactly as shown in the template below. Do NOT use `### Open`, `### Deferred`, `### Dismissed`, or `### Resolved` subsections when creating a new artifact. Those grouped sections are only written at terminal states (STOPPED or CONVERGED). A new artifact has an empty table with only the header row.</mandatory>

After writing, use the Read tool to verify the artifact exists and that `## Findings` is followed by the table header `| ID | Pass | Severity | Location | Description | Status |`, not by `### Open` or any other subsection header. If the file contains `### Open` or `### Deferred` under `## Findings`, immediately overwrite it with the correct template.

### Numbering convention

All findings use the `F-NNN` prefix. The counter starts at 001 when the artifact is first created, pads to three digits, and is per-artifact not per-pass — if pass 1 ends with F-003, pass 2 continues from F-004. Never reset or reuse a number. A finding's ID never changes once assigned — status changes are recorded in the Status column of the findings table, not by reassigning a new ID.

```markdown
# Audit: [branch name]
**Repo:** [repo name]  
**Created:** [date]  
**Scope:** [full branch | path: src/auth/]  
**Base branch:** [BASE_BRANCH]  
**Status:** IN PROGRESS  
**Passes completed:** 0  
**Subagents:** enabled

## Branch summary
[1–3 sentences: what this branch does, what it changes, why it exists]

## Stack detected
[list stacks from Phase 0]

## Lenses applied
[list selected lenses from Phase 1]

<!-- SURFACE_MAP_START -->
## Surface map
[table from Phase 2]
<!-- SURFACE_MAP_END -->

---

## Findings

| ID | Pass | Severity | Location | Description | Status |
|---|---|---|---|---|---|

---

## Pass log
```

</phase>

---

<phase id="4" name="walk">

## Phase 4 — Walk (non-negotiable rules)

<mandatory>**Pass authorization gate.** Before doing anything else in Phase 4, check the pass number you are about to run (call it N):

- If N = 1: proceed. Pass 1 is always authorized by the user running /vc-audit.
- If N ≥ 2: authorization is proven by a token written to the artifact — not by looking at conversation history.

  **Resume check first:** if `## Pass N progress` is already present in the artifact (this exact pass is in-progress from a previous session), you may proceed — it was authorized before the session ended.

  **If this is NOT a resume** (no `## Pass N progress` for pass N exists): run:
  ```bash
  grep -c "^\*\*Next pass:\*\* Authorized" [artifact-path]
  ```
  - If **0**: no authorization exists. Do not start the walk. Instead, run Phase 6 now — fix any open findings, run the convergence check, and call the AskUserQuestion pass checkpoint.
  - If **1**: authorized. Edit the artifact to delete the `**Next pass:** Authorized` line before doing anything else. Then proceed.

**Rationalizing is not allowed.** "The user probably wants me to continue" is not authorization. The grep result is the only valid proof.</mandatory>

<recovery>

**If this is a resumed session (after context compaction or restart):**
0. Determine the artifact path: run `git branch --show-current` to get the current branch name. If it returns empty (detached HEAD state): run `git branch` to list all local branches. Call AskUserQuestion — "The repo is in detached HEAD state — no branch is currently checked out. Which branch were you auditing?" — list each local branch as its own option (use Other to type a branch name manually). Use the confirmed branch name. Slugify the branch name (lowercase, replace non-alphanumeric characters with `-`, collapse consecutive hyphens to one, strip leading/trailing hyphens). If $ARGUMENTS is set (scoped audit), apply the same slugification to the scope path and append `--[path-slug]` to form `[branch-slug]--[path-slug].md`. Otherwise the path is `[branch-slug].md`. Read the artifact at `.vibe-check/vc-audit/[computed-path]` to restore full state.
1. Determine BASE_BRANCH using this priority order — stop at the first that succeeds:
   - **Audit artifact**: read `**Base branch:**` from the artifact header. Use that value.
   - **Roadmap**: use the Read tool to check `.vibe-check/vc-plan/roadmap.md`. If it exists and has a `**Base branch:**` line, use that value.
   - **Derive**: run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null`. If it returns a value, strip the `refs/remotes/origin/` prefix directly — do not use shell utilities. If it returns nothing: run `git remote set-head origin -a 2>/dev/null`, then re-run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null`. If it now returns a value, strip the prefix. If still nothing: run `git for-each-ref --format='%(refname:short)' refs/heads/` and identify the default branch (priority: `main` > `master` > `develop`). Then call AskUserQuestion — "I derived `[branch]` as the base branch for this audit. Is that correct?" — Options: "Yes — use [branch]" / "No — use a different branch (Other)". Use the confirmed or entered value as BASE_BRANCH.
2. If the most recent pass entry in the pass log shows `— in progress`, that pass did not complete — most likely due to context compaction. Check the artifact for a `## Pass N progress` section immediately following that marker (N = the in-progress pass number). If found: read the `[x]`/`[ ]` markers — `[x]` surfaces were already walked and their findings are already written to the artifact; `[ ]` surfaces were not. Store the `[ ]` surfaces as REMAINING_SURFACES. Note whether `subagent:` shows `dispatched` or `pending`, and whether `test-agent:` shows `dispatched` or `pending`. If `## Pass N progress` is not found (compaction happened before the section was written): restart the pass from the beginning.
3. Derive the current pass number, all Open-status findings, and the clean pass count from the artifact. Do not rely on conversation memory. Scan the ID column of the findings table for the highest F-NNN number. Store this value as NEXT_F_NUM. All new findings in this pass must be numbered starting from NEXT_F_NUM + 1. Re-read the full surface map section from the artifact and store every surface listed. If resuming from a `## Pass N progress` section (step 2 above), only the `[ ]` surfaces (REMAINING_SURFACES) need to be walked this session — `[x]` surfaces are already complete.
4. The adversarial subagent always runs — no configuration check needed.
5. Re-derive FILE_READ_MODE and UNTRACKED_FILES: run `git diff BASE_BRANCH...HEAD --shortstat -- ':!.claude/**' ':!.vibe-check/**' ':!package-lock.json' ':!yarn.lock' ':!pnpm-lock.yaml' ':!npm-shrinkwrap.json' ':!composer.lock' ':!Gemfile.lock' ':!poetry.lock' ':!Pipfile.lock' ':!Cargo.lock' ':!go.sum' ':!go.work.sum' ':!package.json' ':!vite.config.*' ':!webpack.config.*' ':!rollup.config.*' ':!esbuild.config.*'`. If non-empty: normal diff mode. If empty: run `git status --porcelain`, filter out `.vibe-check/` and `.claude/` paths. If any M/A/R entries remain: working tree changes exist, proceed in normal diff mode. Store `??` entries (filtered by sensitive exclusions and excluding `.claude/` and `.vibe-check/` paths) as UNTRACKED_FILES. If both committed shortstat and filtered status are empty AND the plan stub at `.vibe-check/vc-plan/[branch-slug].md` contains a `## Chunk files` section: FILE_READ_MODE = true.

</recovery>

<mandatory>

**Write a pass-start marker to the artifact before doing anything else.** Append the following block to the pass log section:

```
### Pass N — in progress

**Surface walk receipts:**
```

Surface receipts are appended here during the walk (Step 4b). The `— in progress` marker is replaced by Phase 5 when the pass completes. If the session ends before the pass completes, this marker signals that the pass must be restarted on resume.

</mandatory>

**If this is a new pass** (no `## Pass N progress` section was found in the recovery step): append a `## Pass N progress` section at the **end of the artifact** (after all existing content — it is a top-level `##` section separate from the pass log). List every surface from the surface map, one line each, in the same order. Use this format:

```markdown
## Pass N progress
subagent: pending
test-agent: pending
- [ ] [Surface name] — [file1.ts file2.ts ...]
- [ ] [Surface name] — [file3.ts]
```

For each surface, list the file paths associated with it from the surface map (space-separated after `—`). If FILE_READ_MODE is true, list the chunk file path instead. Set `subagent:` to `pending`.

<mandatory>The `## Pass N progress` section is always at the END of the artifact, never embedded inside the `### Pass N — in progress` pass log entry. The pass log entry contains only the two-line block written above (header + `**Surface walk receipts:**`). Never add checklist lines or any other content to the pass log entry during Phase 4 — the checklist lives in `## Pass N progress`, receipts are added to the pass log via Step 4b.</mandatory>

**If this is a resumed pass** (REMAINING_SURFACES loaded from `## Pass N progress` in the recovery step): do not rewrite it. Use the existing section as-is.

**Dispatch the adversarial subagent** when the `subagent:` line in `## Pass N progress` shows `pending`: dispatch now using the Agent tool with `run_in_background: true`. Use the subagent prompt from the Adversarial pass section below, omitting the "do not repeat open findings" instruction — the subagent reads the full branch diff itself; deduplication happens at Phase 6 when results are collected. Immediately update the `subagent:` line in `## Pass N progress` to `dispatched`.

**Dispatch the test integrity agent** when the `test-agent:` line in `## Pass N progress` shows `pending`: dispatch now using the Agent tool with `run_in_background: true`. Use the test integrity prompt from the Test integrity pass section in Phase 5. Immediately update the `test-agent:` line in `## Pass N progress` to `dispatched`.

**Walk each surface one at a time.** For each `[ ]` surface in `## Pass N progress` (in order from top to bottom):

<mandatory>**Newly discovered surfaces.** If, while walking a surface, you identify a file or component that (a) appears in the diff or Read output AND (b) is not already listed in `## Pass N progress`, it is a new surface that must be registered before it is walked:

1. Use the Edit tool to add a new row to the surface map table (between `<!-- SURFACE_MAP_START -->` and `<!-- SURFACE_MAP_END -->`).
2. Run immediately:
   ```bash
   grep -c "[new surface name]" .vibe-check/vc-audit/[artifact-filename]
   ```
   If count is **0**: the Edit failed — re-attempt before continuing.
3. Use the Edit tool to append `- [ ] [Surface name] — [file path]` to `## Pass N progress`.
4. Only then walk the new surface using Steps 1–4c.

A surface that is walked but never added to the surface map table is invisible to all future passes — it will not appear in the next `## Pass N progress` section and will be silently skipped forever.</mandatory>

<mandatory>**Do not narrate surface status before running Step 2.** Writing any text output to the user about a surface — e.g., "Surface 1: spotifyFetch — CLEAN", "no changes since pass N", "unchanged", "same as last pass" — before completing Steps 2–3 for that surface is prohibited. Run the diff or Read command first; report only after you have the output in context. The first thing you do for each `[ ]` surface is Step 1 (sensitive file check), then Step 2 (diff or Read) — not announcing its status.</mandatory>

**Step 1 — Sensitive file check.** If the surface file(s) match any pattern in the Sensitive File Protection section, skip the diff and record a finding per the Sensitive File Protection rules. Use the Edit tool to mark the surface `[x]` in `## Pass N progress`. Move to the next surface.

**Step 2 — Load only this surface's scope:**

If FILE_READ_MODE is false:
- If this surface is marked `(untracked — Read tool)`: use the Read tool to read each file. Skip the diff — untracked files have no diff.
- Otherwise (tracked file — committed, staged, or unstaged):
```bash
git diff BASE_BRANCH -- [file paths for this surface]
```
Substitute BASE_BRANCH. For an initial commit session, substitute `4b825dc642cb6eb9a060e54bf8d69288fbee4904`. This captures committed changes AND any uncommitted staged/unstaged changes vs the base branch. If `$ARGUMENTS` was provided, verify the surface files fall within the requested scope — if a surface file is outside the requested scope, mark it `[x]` and skip it.

<mandatory>Run the bare `git diff` command only — do NOT pipe the output through `head`, `tail`, `grep`, or any other filter. Specifically forbidden: `git diff ... | head -N`, `git diff ... | tail -N`, `git diff ... | grep ...` (in any form, including `grep -A N`, `grep -i`, `grep -n`, `grep -c`). These filters silently discard parts of the diff, producing receipts that look evidence-backed while hiding unchecked content. If the diff output is too large to process — use the Read tool on the source file directly with explicit line ranges instead of the diff. A Read with a declared line range is honest about its scope; a filtered diff is not.</mandatory>

If FILE_READ_MODE is true: use the Read tool to read the chunk file for this surface. If the Read tool returns an error, stop and report: "Could not read `[filename]` — verify the file exists. If moved or renamed, update `## Chunk files` in the plan stub and re-run /vc-audit." If the file returns exactly 2000 lines, re-read with increasing offsets (2000, 4000, …) until a read returns fewer than 2000 lines. Concatenate all parts as the complete file content.

<gate>Do not walk this surface until you have its diff output or file content in context. Load only this surface — not the full branch diff.</gate>

**Step 3 — Walk all selected lenses** against this surface. Follow the walk rules below. Follow dependencies into other files using the Read tool as required by the threat model.

<mandatory>**Step 4 — After completing this surface, perform BOTH of the following writes before moving to the next surface:**

**Step 4a — Update the progress checklist.** Use the Edit tool to replace `- [ ] [Surface name]` with `- [x] [Surface name]` in `## Pass N progress`. Do not move to the next surface until this edit has succeeded. This is the resume record — skipping it makes compaction recovery impossible.

<!-- RECEIPT_FORMAT_START -->
**Receipt format** — every surface walked in Phase 4 must produce a receipt in this exact format:

```
- Surface: [name from surface map]
  Verdict: CLEAN | NEW FINDINGS (F-NNN)
  Evidence: file:line — `[verbatim line from diff or Read output]` — [observation]
```

**Evidence rules (re-read after any compaction):**
- The `Evidence:` line MUST contain at least one backtick-quoted verbatim string from Step 2 tool output in this pass
- For a diff surface: quote a `+` or `-` line (e.g., `` `+const x = Object.create(null);` ``)
- For a Read surface (untracked file or FILE_READ_MODE): quote an exact code line from the Read result at the cited line number
- If `git diff` returns no output for this surface: run the Read tool on the source file and quote a line — `diff empty` alone is NOT valid Evidence
- Forbidden phrases (prove no fresh tool call was made — invalid regardless of diff result): "No changes since pass N" · "Unchanged from pass N" · "Confirmed from pass N" · "Same as pass N" · "Already confirmed" · "No logic changes since" · "Unchanged" (with no file:line citation)
- A receipt where `Evidence:` does not contain at least one backtick-enclosed string has the same standing as no receipt at all
<!-- RECEIPT_FORMAT_END -->

**Step 4b — Write this surface's receipt into the pass log.** Use the Edit tool with:
- `old_string`: `\n\n## Pass N progress` (the two newlines immediately before the `## Pass N progress` section header — substitute the actual pass number for N)
- `new_string`: the receipt entry followed by `\n\n## Pass N progress`:

```
- Surface: [name from surface map]
  Verdict: CLEAN | NEW FINDINGS (F-NNN)
  Evidence: file:line — `[verbatim line from diff output or Read result]` — [observation]

## Pass N progress
```

This inserts the receipt into the pass log just before the progress section. Each subsequent surface uses the same anchor — the `\n\n## Pass N progress` text is always present at the end of the new_string, so the anchor remains valid for the next surface.

Do NOT write `Verdict: CLEAN` with no `Evidence:` citation, and do NOT write `Evidence:` without a real `file:line` reference from a tool call you made in Step 2 of **this surface in this pass**. "CLEAN. No issues." is not a valid receipt. Do NOT defer receipt writing to Phase 5 — write it now while the evidence is in your context.

<mandatory>The Evidence line must include at least one verbatim line copied directly from your Step 2 tool output, enclosed in backticks:
- For a diff-based surface: quote a `+` or `-` line from the `git diff` output (e.g., `` `+const artistCounts = Object.create(null);` ``).
- For a Read-based surface (untracked file or FILE_READ_MODE): quote an exact code line from the Read result at the cited line number (e.g., `` `signal: undefined` for existing callers ``).

A summary, paraphrase, or description of what the code shows — even an accurate one derived from prior pass receipts in this artifact — is NOT valid Evidence. The verbatim quote is the only proof that Step 2 was actually executed for this surface in this pass.

There is no exception for surfaces you believe are unchanged from prior passes. A surface that has been CLEAN for eight consecutive passes must still produce a fresh verbatim quote in the current pass. The verbatim quote is not evidence that something changed — it is evidence that you looked.

**When `git diff` returns no output (empty diff) for this surface:** the empty diff is NOT evidence and does NOT satisfy the Evidence requirement. You MUST run the Read tool on the source file(s) for this surface and quote a specific line from the Read result. Receipt format for an empty-diff surface:
```
  Evidence: src/spotify.ts:12 — `async function spotifyFetch(url: string)` — diff empty; file confirmed by fresh Read
```
A receipt that says "no diff", "no changes", "no changes since pass N", "unchanged", or any variant without a backtick-quoted line from a Read tool call is invalid regardless of the diff result. If git diff returns empty: run Read now, then write the Evidence.

Before writing this receipt: ask yourself "Can I paste a specific `+` or `-` line from the diff output, or a backtick-quoted line from a Read result, that I received in my tool output THIS pass?" If the answer is no, you have not completed Step 2 for this surface. Run the `git diff` command (or the Read tool for FILE_READ_MODE or empty-diff surfaces) now and return to Step 4b with actual output to quote.</mandatory>

The following phrases in a receipt are **forbidden** because they prove no fresh tool call was made — the receipt is citing memory or a prior pass instead of this pass's Step 2 output:
- "No changes since pass N"
- "Unchanged from pass N"
- "Confirmed from pass N" / "Confirmed from prior read"
- "Same as pass N"
- "Already confirmed"
- "No logic changes since"
- "Unchanged" (with no file:line citation following)

If you find yourself writing any of these phrases, stop — you have not performed Step 2 for this surface. Go back, run the git diff or Read tool call for this surface now, and write the Evidence from that output.

When using the Read tool with a line range (e.g., Read lines 421-494), your Evidence citations must only reference content visible within that range. If you find yourself citing a line number, a function, a count, a method name, or any characteristic of the file that falls OUTSIDE the range you actually read — stop. You have used memory. Either re-read with a range that covers that content, or remove the citation. A receipt that cites content from outside the read window is a memory receipt, not a tool-call receipt — it has the same standing as no receipt at all.</mandatory>

<mandatory>**Step 4b-verify — Confirm the receipt is in the correct format.** Immediately after the Step 4b Edit succeeds, run:

```bash
grep -B 3 "^## Pass N progress" .vibe-check/vc-audit/ARTIFACT | grep -c "^Evidence:"
```

Substitute the actual pass number and artifact filename. The count must be **1**.

If the count is **0**: the receipt was written in abbreviated format — it is missing the `Evidence:` line (e.g., `Surface N — CLEAN. No changes since pass X.`). Do NOT proceed to Step 4c. First reload the required format:

```bash
sed -n '/RECEIPT_FORMAT_START/,/RECEIPT_FORMAT_END/{/<!--/d;p}' .claude/commands/vc-audit.md
```

Then run Edit to replace the abbreviated receipt text with a correctly formatted 3-line receipt. Re-run the `grep -B 3 | grep -c "^Evidence:"` command and confirm count = 1 before continuing.

This step runs after every surface receipt regardless of whether compaction has occurred — it is the mechanical guard against gradual format drift in long uninterrupted sessions.</mandatory>

<mandatory>**Step 4c — Verify any new findings are in the findings table.** If this receipt shows `Verdict: NEW FINDINGS`, run a grep for each F-NNN mentioned in the receipt:

```bash
grep -c "| F-NNN |" .vibe-check/vc-audit/[artifact-filename]
```

Substitute the actual finding ID and artifact filename (e.g., `grep -c "| F-007 |" playlist-insights.md`). If the count is **0**: the finding was written to the pass log receipt but was never appended as a row to the `## Findings` table — it is invisible to Phase 6 and will never be tracked, acted on, or counted toward convergence. Write the missing row now:

`| F-NNN | pass N | severity (conf) | file:line | description | Open |`

Do NOT update the progress checklist (Step 4a) and do NOT move to the next surface until every F-NNN cited in this receipt returns a count ≥ 1 from the grep above. A finding that exists only in the pass log narrative has the same standing as no finding.</mandatory>

<walk-rules>

Walk every surface in the surface map against every selected lens. These rules apply to
every pass, every time. **If FILE_READ_MODE is true, substitute "the chunk file contents"
for all references to "the diff" or "the branch diff" in these rules** — the chunk files
are the audit surface, not a diff.

**Permitted tools during the walk:** Read (for following dependencies), Edit/Write (for writing findings to the artifact and updating `## Pass N progress`), AskUserQuestion (for user decisions), and Agent (for the adversarial subagent). The only Bash commands permitted are the `git diff` surface-scoping commands specified above, and `git ls-files` if needed to resolve gitignored exclusions.

Do not invoke interpreters. Specifically forbidden: `node -e`, `python -c`, `ruby -e`, `php -r`, or any equivalent one-liner form. A script the model authors to "simulate" or "verify" a logic path executes the model's own reasoning, not the actual source under test — its output is not valid evidence even when the interpreter returns non-zero content. All analysis happens in Claude's reasoning, not in a shell.

<mandatory>Do NOT use Bash calls as a reasoning scratchpad. The specific pattern to avoid: a Bash call whose body consists of `# Check: ...` comments (shell comments narrating your reasoning) and concludes with `echo "done"`, `echo "checks complete"`, `echo "[finding] confirmed"`, or any terminal echo that produces no verifiable output. These calls return nothing checkable and cannot serve as Evidence — `echo "done"` proves only that bash ran. A Bash call is only valid evidence if it returns meaningful command output you can quote verbatim in the receipt (e.g., a grep line, a file count, a diff line). Shell comments inside a Bash call are private reasoning and have no evidential standing regardless of how detailed they are.</mandatory>

- Walk **attack vectors and failure paths end-to-end**, not files in isolation. For each
  surface ask: what does a caller with no elevated privilege get to do through each interface?
  what happens when this fails partway through? what invariant is assumed here that isn't
  actually enforced?
- **No surface scans. No delta-only checks. No "I already covered this."** Every pass starts
  fresh from the surface map. Prior passes do not grant permission to skip. Do not write
  "same as pass N" for any surface — show your reasoning or you have not walked it.
- **Every surface in every pass requires a Read tool call or diff output as the evidence source.** In-context memory of prior reads does not count — it is equivalent to skipping the surface. Even if you read a file two minutes ago in this same conversation, you must call the Read tool again for that surface in the current pass. Evidence must come from a tool call made during this pass, not from recall.
- **The surface map is where you start, not where you stop.** If a surface map file imports,
  extends, or calls into another file and understanding that relationship is necessary to
  evaluate an attack vector or failure path, use the Read tool to pull in that file. Do this
  only when the analysis requires it — not as a blanket rule. A changed file calling an
  unchanged function inherits that function's bugs; follow the chain as far as the threat
  model demands, then stop. Do not expand scope into files that are unrelated to the
  surfaces under review.
- **Before recording any finding, quote the specific lines of code that motivate it.**
  If you cannot quote the lines directly from the diff or from a Read tool result, the finding
  is unverified and must be assigned confidence ≤4 (not added to Open). Do not work around
  this by assigning 5–6 to unquoted findings. Do not run code to simulate or verify a finding — if the issue is not evident from reading the code, use the Read tool to pull in more context, not a shell interpreter.
- **Record each finding in the artifact immediately when discovered.** Do not accumulate
  findings in memory and batch them for Phase 5. For each finding: use the Read tool to read
  the current findings table and identify the last row (or the header separator line
  `|---|---|---|---|---|---|` if the table has no data rows yet). Use that as the `old_string`
  anchor in the Edit tool to append the new F-NNN row after it. New rows always have
  Status = Open. Row format:
  `| F-NNN | pass N | severity (conf) | file:line | description | Open |`
  Never use a cached anchor from a previous write — always re-read the table before each
  append. After each write, use the Read tool to verify the row appears in the artifact. If
  it does not, re-attempt once. If it still fails, tell the user and provide the exact row to
  add manually: "Could not write [F-NNN] to the artifact — please add this row to the findings
  table manually: `| F-NNN | pass N | severity (conf) | file:line | description | Open |`"
- **If a finding predates this branch** (the issue exists in code not changed by this diff),
  add `[pre-existing]` inline to the finding entry. Pre-existing issues are still surfaced
  and still require action.
- When you find something previously dismissed as "pre-existing," "out of scope," "by design,"
  or "behavioral limit" — surface it. Do not re-dismiss silently. If it is a real finding,
  fix it. If you genuinely believe it is not actionable, list it explicitly under
  "Want to skip — awaiting approval" and **wait for approval before deferring**.
- **Severity labels do not grant automatic deferral.** A P3 or "informational" finding still
  goes under "Want to skip" — the label is your reasoning, not permission to skip asking.
- **Your reasoning is not private.** If you noticed something during analysis and dismissed
  it, weighed it, or concluded it was acceptable — it must appear in the report under
  Dismissed or Want to skip. A finding that lives only in your thinking is a methodology
  violation, not a judgment call.
- If something looks wrong and does not fit any lens category, surface it anyway. The lenses
  help you start — they do not define the scope.

</walk-rules>

**Coverage gate:** Before proceeding to Phase 5, run all three of these bash commands:

```bash
grep -c "- \[ \]" .vibe-check/vc-audit/[artifact-filename]
grep -c "^  Verdict:" .vibe-check/vc-audit/[artifact-filename]
grep -c "Evidence:.*\`" .vibe-check/vc-audit/[artifact-filename]
```

<mandatory>
1. **Unchecked surfaces (first grep):** If the count of `- [ ]` is greater than 0, there are unchecked surfaces. Return to Phase 4 and walk the remaining surfaces (Steps 1–4). The Phase 5 `grep -c "- \[ \]"` gate will also catch this — this check here is a preview gate.

2. **Missing receipts (second grep):** The second grep counts `Verdict:` lines across all passes in the artifact. The expected count is SURFACE_COUNT × PASS_NUMBER — where SURFACE_COUNT is the number of rows in the surface map table from Phase 2, and PASS_NUMBER is the current pass number. If the actual count is less than SURFACE_COUNT × PASS_NUMBER, at least one surface in the current pass is missing a receipt. To find the gap: read the `### Pass N — in progress` block in the artifact and identify which surface names from the surface map do NOT appear as `- Surface: [name]` receipt entries. For each missing receipt: go back to Step 2 for that surface (run the diff or Read), then write the receipt via Step 4b now. Do not write the receipt from memory.

3. **Missing verbatim evidence (third grep):** The third grep counts `Evidence:` lines that contain a backtick-quoted verbatim string. The expected count is ≥ SURFACE_COUNT × PASS_NUMBER. If the actual count is less: one or more receipts are missing a backtick-quoted verbatim line — they contain only narrative descriptions like "no changes since pass N", "diff empty", or "unchanged". These are NOT valid evidence. For each receipt missing a backtick quote: return to Step 2 for that surface, run `git diff` or the Read tool now, and rewrite the Evidence line with a backtick-quoted line from the tool output. A receipt where Evidence does not contain at least one backtick-enclosed string has the same standing as no receipt at all.

Do not proceed to Phase 5 until: `grep -c "- \[ \]"` = 0 AND `grep -c "^  Verdict:"` ≥ SURFACE_COUNT × PASS_NUMBER AND `grep -c "Evidence:.*\`"` ≥ SURFACE_COUNT × PASS_NUMBER. A `[x]` mark without a backtick-evidence receipt is not a walked surface.
</mandatory>

</phase>

---

<!-- COMPACT_HOOK_START -->
<phase id="5" name="report">

## Phase 5 — Report and update the artifact

After each pass, update the artifact in place. The artifact accumulates across passes —
do not create a new file per pass.

**First: remove the `## Pass N progress` section.** Run:

```bash
grep -c "- \[ \]" .vibe-check/vc-audit/[artifact-filename]
```

<mandatory>If the grep count is greater than 0: there are unchecked surfaces. Do NOT delete the section and do NOT continue to "Second". Return to Phase 4 and walk the remaining `[ ]` surfaces (Steps 1–4). Do NOT verify by reading adjacent lines or a line range that does not include the `## Pass N progress` section — the grep count is the only valid check. "All surfaces are complete" is not a valid reason to skip this grep. Run it every time.

Only when `grep -c "- \[ \]"` returns 0: use the Edit tool to replace the entire `## Pass N progress` section (from `## Pass N progress` through the last `- [x]` line) with an empty string. Then immediately run:

```bash
grep -c "## Pass.*progress" .vibe-check/vc-audit/[artifact-filename]
```

Quote the output verbatim. If the count is greater than 0: one or more `## Pass.*progress` sections remain — this includes any stale sections left by prior passes. Delete each one with a separate Edit call, then re-run the grep. Repeat until the grep returns **0**. Only when this grep returns **0** may you proceed to "Second". Do NOT move to "Second" before quoting a 0 from this grep.
</mandatory>

<mandatory>**Second: finalize the pass log header.** Use the Edit tool to replace `### Pass N — in progress` with `### Pass N — YYYY-MM-DD` where YYYY-MM-DD is today's date (example: `### Pass 11 — 2026-06-19`). Do NOT write `— complete`, `— done`, `— finished`, or any word other than the ISO date. The surface walk receipts are already written in the pass log from Phase 4 Step 4b — do NOT rewrite or reconstruct them. Do NOT add any new content between the updated header and the first receipt line. This is a one-line header edit only.

Then immediately run:

```bash
grep -c "^### Pass .* — in progress" .vibe-check/vc-audit/[artifact-filename]
```

Quote the output verbatim. If the count is 1: the Edit did not run — run it now, then re-grep. Only when this grep returns **0** may you proceed to append the pass fields below. Do NOT append any pass fields before quoting a 0 from this grep.</mandatory>

Then append the following fields after the last receipt entry in the `### Pass N` block (use the Edit tool, anchoring on the last `Evidence:` line of the final receipt):

```markdown
**Acting on** (F-NNN being fixed this pass):
- F-003 | pass 1 | high (9/10) | src/export.ts:47 — CSV row written before checksum verified

**Dismissed** (must be filled; "none" requires explicit statement):
- F-004 | src/config.ts:12 — hardcoded timeout is intentional per README, not a secret
  _(or: none — nothing noticed that warranted dismissal this pass)_

**Want to skip** (real findings, requesting deferral approval):
- [F-NNN — describe the finding and state reasoning for deferral]
  _(or: none)_

**Remaining surface area**:
- [honest account of what has not been fully walked yet]
  _(or: none — full coverage achieved this pass)_
```

<mandatory>The pass log entry ends at "Remaining surface area". Do NOT add any fields after it — no "CONVERGENCE DECLARED", no "CLEAN", no terminal status, no summary sentence. The convergence decision is made in Phase 6 using AskUserQuestion. Writing any convergence conclusion in the pass log is a protocol violation regardless of how clean the pass was.</mandatory>

A surface with no evidence entry is not considered walked. A pass is not clean unless
every surface in the surface map has a receipt entry with at least one file:line citation.

**Every finding description must include three things:**
1. What the problem is (specific to this code, not a category label)
2. What it allows or causes (the concrete consequence)
3. The fix direction (what change would address it)

Example row: `| F-004 | pass 2 | medium (7/10) | src/api/users.ts:83 | [pre-existing] user lookup does not validate that the returned row belongs to the authenticated tenant; a logged-in user from tenant A can read tenant B's user records by guessing IDs; fix: add tenant_id = auth.uid() filter to the query | Open |`

Phase 5 does not update finding statuses. All status transitions (Resolved, Deferred, Dismissed) are applied by Phase 6 as individual Status cell Edits immediately after each user decision.

Severity guide (for junior devs):
- **Critical** — exploitable in production right now; data loss or auth bypass possible
- **High** — likely to cause a real bug or security issue under normal use
- **Medium** — causes incorrect behavior in edge cases or degrades over time
- **Low** — code smell, missing best practice, or technical debt
- **Info** — observation worth recording; no action required unless patterns emerge

Confidence guide (include as `(N/10)` next to severity on every F-NNN finding):
- **9–10** — you can quote the specific lines of code that prove this is a real issue
- **7–8** — strong pattern match; very likely correct
- **5–6** — possible false positive; state in the finding what would confirm it
- **≤4** — do not add to Open; log briefly in the pass narrative or omit entirely

### Adversarial pass

<mandatory>**Pre-adversarial gate.** Before collecting the subagent result, verify Phase 5 "First" completed — run:

```bash
grep -c "^## Pass [0-9]* progress" .vibe-check/vc-audit/[artifact-filename]
```

Count must be **0**. If **> 0**: the `## Pass N progress` section still exists — the surface walk is incomplete or Phase 5 "First" was skipped. Return to Phase 5 "First" now: check `grep -c "- \[ \]"`, walk any remaining surfaces, then complete Phase 5 "First" before returning here. Do not collect the subagent result until this grep returns 0.</mandatory>

The adversarial subagent always runs. Collect its result now:

<mandatory>Collect the background subagent result dispatched at the start of Phase 4. The subagent ran in parallel while the main walk executed — its findings should now be available. If it has not yet completed, wait for it now.

The subagent prompt used was the one below (for reference — do not re-dispatch). Process the returned output: for each finding, check whether the same issue is already recorded as a row with Status = Open in the findings table. If a duplicate exists, skip it. Add any non-duplicate findings to the findings table using the same F-NNN numbering sequence.

The subagent prompt (for reference only — already dispatched):

**If FILE_READ_MODE is false** (normal diff-based audit): substitute BASE_BRANCH, artifact path, and scope paths into this prompt. If this is a scoped audit, read the `**Scope:**` field from the artifact header and append the scope path(s) as trailing arguments after the sensitive file exclusions in the git diff command (e.g. `-- ':!...' src/auth/`). If this is a full audit, omit the trailing path arguments entirely. Use `git diff [BASE_BRANCH]` (not `...HEAD`) to capture both committed and uncommitted tracked changes.

"Before reading any file, skip it if its filename or path matches any of these sensitive file patterns:
`.env`, `.env.*`, `.envrc`, `.envrc.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8`,
`*.jks`, `*.keystore`, `*.ppk`, `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa`, `*.secret`,
`*.secrets`, `*.vault`, `*.enc`, `.netrc`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc`,
`*credentials.json`, `*service-account*.json`, `*-key.json`, `*.tfstate`, `*.tfstate.backup`,
`*.tfvars`, `*.tfvars.json`, `google-services.json`, `GoogleService-Info.plist`, `kubeconfig`,
`*.kubeconfig`, `docker-compose.override.yml`, `docker-compose.*.yml`, `local_settings.py`,
`settings.py`, `application_default_credentials.json`, `.htpasswd`, `htpasswd`, `database.yml`,
`wrangler.toml`, `fly.toml`, `*secrets*`, `*password*`, `*passwd*`

Run this git command and read the full output:

git diff [BASE_BRANCH] -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' [scope paths if scoped audit]

Then use the Read tool to read the audit artifact at [artifact path].

From the artifact, find the surface map table. It is between `<!-- SURFACE_MAP_START -->` and `<!-- SURFACE_MAP_END -->` if those markers exist, otherwise it is under the `## Surface map` header. For each row, extract the file paths listed in the Entry points column. Use the Read tool to read each of those files directly (skip any that match the sensitive file patterns above, and skip files that are not present on disk — deleted files appear only in the diff).

Your task: find failure modes, bugs, and security issues by reading the source files directly and cross-referencing with the diff. Think like an attacker and a chaos engineer. No compliments — only problems.

Rules:
1. Before reporting any finding, quote the specific lines from the file or diff that motivate it. If you cannot quote specific lines, do not report it.
2. Do not repeat findings already listed as Open in the artifact — check that section before reporting.
3. Classify each finding as FIXABLE (you can state the fix direction) or INVESTIGATE (needs human judgment to resolve).
4. For test files (`*.test.*`, `*.spec.*`): report only test *correctness* issues (wrong assertions, bad async handling, missing teardown, mocks that hide real production behavior). Do NOT report missing test scenarios or coverage gaps — test coverage is handled by vc-ship.
5. For every non-obvious operation in new code, check whether an inline comment explains the WHY (ELI10 standard per CLAUDE.md — comments must explain why, not what). Flag any new function or control flow branch where the behavior is not self-evident from the identifier name alone and has no accompanying comment.
6. For every bug class fixed in function A, check if any structurally parallel function B in the same file or module has the identical bug class. Sibling functions with the same pattern are the most common missed finding.
7. For every modified file, check pre-existing adjacent code (not just the diff lines) that touches the same data paths for the same class of issue found in the diff.
8. In new or modified CSS: flag `:focus` where `:focus-visible` is appropriate; `overflow: hidden` on fixed-width flex containers that may clip dynamic content; missing `min-width: 0` on flex children that need to shrink.
9. For any element that appears or disappears dynamically (conditional render, toggle, loading state), verify its container has `aria-live="polite"` so screen readers announce the change.

Output one finding per line in this format:
[FIXABLE|INVESTIGATE] | [critical|high|medium|low] | file:line — what the problem is; what it allows or causes; fix direction or what to investigate

If you find nothing new, output exactly: NO ADDITIONAL FINDINGS"

**If FILE_READ_MODE is true** (chunk branch — no diff): substitute the artifact path into this prompt:

"Before reading any file, skip it if its filename or path matches any of these sensitive file patterns:
`.env`, `.env.*`, `.envrc`, `.envrc.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8`,
`*.jks`, `*.keystore`, `*.ppk`, `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa`, `*.secret`,
`*.secrets`, `*.vault`, `*.enc`, `.netrc`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc`,
`*credentials.json`, `*service-account*.json`, `*-key.json`, `*.tfstate`, `*.tfstate.backup`,
`*.tfvars`, `*.tfvars.json`, `google-services.json`, `GoogleService-Info.plist`, `kubeconfig`,
`*.kubeconfig`, `docker-compose.override.yml`, `docker-compose.*.yml`, `local_settings.py`,
`settings.py`, `application_default_credentials.json`, `.htpasswd`, `htpasswd`, `database.yml`,
`wrangler.toml`, `fly.toml`, `*secrets*`, `*password*`, `*passwd*`

Use the Read tool to read the audit artifact at [artifact path].

From the artifact, find the surface map table. It is between `<!-- SURFACE_MAP_START -->` and `<!-- SURFACE_MAP_END -->` if those markers exist, otherwise it is under the `## Surface map` header. For each row, extract the file paths listed in the Entry points column. Use the Read tool to read each of those files directly (skipping any that match the sensitive file patterns above, and skipping files that are not present on disk).

Your task: find failure modes, bugs, and security issues in these files. Think like an attacker and a chaos engineer. No compliments — only problems.

Rules:
1. Before reporting any finding, quote the specific lines from the file that motivate it. If you cannot quote specific lines, do not report it.
2. Do not repeat findings already listed as Open in the artifact — check that section before reporting.
3. Classify each finding as FIXABLE (you can state the fix direction) or INVESTIGATE (needs human judgment to resolve).
4. For test files (`*.test.*`, `*.spec.*`): report only test *correctness* issues (wrong assertions, bad async handling, missing teardown, mocks that hide real production behavior). Do NOT report missing test scenarios or coverage gaps — test coverage is handled by vc-ship.
5. For every non-obvious operation in code, check whether an inline comment explains the WHY (ELI10 standard per CLAUDE.md — comments must explain why, not what). Flag any function or control flow branch where the behavior is not self-evident from the identifier name alone and has no accompanying comment.
6. For every bug class found in function A, check if any structurally parallel function B in the same file or module has the identical bug class. Sibling functions with the same pattern are the most common missed finding.
7. Check pre-existing adjacent code that touches the same data paths for the same class of issue you are reviewing.
8. In CSS: flag `:focus` where `:focus-visible` is appropriate; `overflow: hidden` on fixed-width flex containers that may clip dynamic content; missing `min-width: 0` on flex children that need to shrink.
9. For any element that appears or disappears dynamically (conditional render, toggle, loading state), verify its container has `aria-live="polite"` so screen readers announce the change.

Output one finding per line in this format:
[FIXABLE|INVESTIGATE] | [critical|high|medium|low] | file:line — what the problem is; what it allows or causes; fix direction or what to investigate

If you find nothing new, output exactly: NO ADDITIONAL FINDINGS"
</mandatory>

Process the subagent output and update the artifact:

<mandatory>The subagent uses its own internal labeling — letters (A, B, C…), numbers, or arbitrary identifiers in its output. These labels are **never** used as finding IDs in the artifact. Every finding from the subagent must be renumbered using the artifact's F-NNN counter.

Before adding any finding: read the findings table in the artifact and scan the ID column for the highest existing F-NNN number. Call that value NEXT_F_NUM. The first new finding gets F-(NEXT_F_NUM+1), the second gets F-(NEXT_F_NUM+2), and so on.

Example: the artifact already has F-001 through F-005. The subagent returns findings labeled A, B, C. In the artifact they become F-006, F-007, F-008 — never A-A, A-B, A-C or any other format derived from the subagent's labels.</mandatory>

- For each **FIXABLE** finding: assign the next F-NNN number from the counter above; append a row to the findings table with Status = Open. Include `[adversarial]` in the Description field. Apply the same confidence guide as the main walk — 9/10 if specific lines are quoted, 7/10 for strong pattern match:
  `| F-NNN | pass N | [severity] (N/10) | file:line | [adversarial] description | Open |`
- For each **INVESTIGATE** finding: assign the next F-NNN number from the counter above; append a row to the findings table with Status = Open. Include `[adversarial][INVESTIGATE]` in the Description field:
  `| F-NNN | pass N | [severity] (6/10) | file:line | [adversarial][INVESTIGATE] description | Open |`
  These go through the same fix/defer/dismiss decision protocol in Phase 6 as any other finding.
- If **NO ADDITIONAL FINDINGS**: append to the pass log: `Adversarial pass: no additional findings.`
- If the subagent is **unavailable or errors**: append to the pass log: `Adversarial pass: unavailable.` Proceed to the test integrity pass.

### Test integrity pass

<mandatory>Collect the background test integrity agent result dispatched at the start of Phase 4. If it has not yet completed, wait for it now.

The test integrity agent reads only test files from the diff and checks for correctness issues that the main walk typically misses. Process its output the same way as the adversarial agent: renumber all findings using the next F-NNN from the counter (read the findings table first to get the current highest ID), skip any finding that duplicates an existing Open row.

The test integrity prompt (for reference only — already dispatched):

**If FILE_READ_MODE is false** (normal diff-based audit): substitute BASE_BRANCH, artifact path, and scope paths into this prompt. If this is a scoped audit, append the scope path(s) after the sensitive file exclusions in the git diff command.

"Before reading any file, skip it if its filename or path matches any of these sensitive file patterns:
`.env`, `.env.*`, `.envrc`, `.envrc.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8`,
`*.jks`, `*.keystore`, `*.ppk`, `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa`, `*.secret`,
`*.secrets`, `*.vault`, `*.enc`, `.netrc`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc`,
`*credentials.json`, `*service-account*.json`, `*-key.json`, `*.tfstate`, `*.tfstate.backup`,
`*.tfvars`, `*.tfvars.json`, `google-services.json`, `GoogleService-Info.plist`, `kubeconfig`,
`*.kubeconfig`, `docker-compose.override.yml`, `docker-compose.*.yml`, `local_settings.py`,
`settings.py`, `application_default_credentials.json`, `.htpasswd`, `htpasswd`, `database.yml`,
`wrangler.toml`, `fly.toml`, `*secrets*`, `*password*`, `*passwd*`

Run this git command and read the full output:

git diff [BASE_BRANCH] -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' [scope paths if scoped audit]

Then use the Read tool to read the audit artifact at [artifact path]. From the artifact, check the ## Findings section for any findings already listed as Open.

From the git diff output, identify all test files (paths matching `*.test.*`, `*.spec.*`, `*_test.*`, or `test_*.py`). For each test file that appears in the diff, use the Read tool to read the full current file directly (not just the diff lines). If no test files appear in the diff, output exactly: NO ADDITIONAL FINDINGS

Your task: find test correctness issues — tests that pass when they should fail, or that verify the wrong thing. Think like a QA engineer reviewing whether tests actually catch what they claim to catch.

Check each test file against these six patterns:
1. **Fixture shape mismatch** — does the test fixture match the real data shape the code under test expects? (e.g. `{id, name}` when code expects `{id, name, images: [{url: string}]}`) Quote both the fixture definition and the line in production code that consumes it.
2. **Sync assertion on async throw** — is `.toThrow()` or `.toThrowError()` called without `await`? (Async functions return a Promise — a plain `.toThrow()` always passes because the function returns a Promise instead of throwing; must use `await expect(fn()).rejects.toThrow()`)
3. **`fireEvent` on disabled elements** — is `fireEvent.click` or `fireEvent.change` used on an element with a `disabled` attribute? JSDOM's native `disabled` attribute is not enforced by `fireEvent` (it bypasses the browser event pipeline) — use `userEvent.click` for realistic simulation, or assert via `not.toHaveBeenCalled()` that the handler was blocked.
4. **Direct prototype mutation** — does the test assign directly to a class prototype or global object prototype (e.g. `Navigator.prototype.clipboard = mockClipboard`)? `vi.restoreAllMocks()` and `vi.resetAllMocks()` do not restore these mutations — the original value must be saved before the test and restored in `afterEach`.
5. **Implicit ARIA role vs explicit attribute** — does the test use `getByRole()` when the intention is to verify that a `role` attribute explicitly exists? Native HTML elements have implicit ARIA roles (a `<button>` has role `button` even without `role='button'`), so `getByRole('button')` passes whether or not a `role` attribute is present. To assert the attribute exists: use `element.getAttribute('role')` or `expect(element).toHaveAttribute('role', 'button')`.
6. **Non-discriminating assertion** — would this test pass if the bug it targets were reintroduced? If the assertion only checks that an element exists but not its content, or that a function was called but not with the expected arguments, the test does not prove the behavior is correct.

Rules:
1. Before reporting any finding, quote the specific lines from the test file that motivate it. If you cannot quote specific lines, do not report it.
2. Do not repeat findings already listed as Open in the artifact.
3. Classify each finding as FIXABLE (you can state the fix direction) or INVESTIGATE (needs human judgment).

Output one finding per line in this format:
[FIXABLE|INVESTIGATE] | [critical|high|medium|low] | file:line — what the problem is; what it allows or causes; fix direction or what to investigate

If you find nothing new, output exactly: NO ADDITIONAL FINDINGS"

**If FILE_READ_MODE is true** (chunk branch — no diff): substitute the artifact path into this prompt:

"Use the Read tool to read the audit artifact at [artifact path].

From the artifact, find the surface map table (between `<!-- SURFACE_MAP_START -->` and `<!-- SURFACE_MAP_END -->`, or under the `## Surface map` header). For each row that lists a test file (`*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`), use the Read tool to read the full file. If no test files are listed in the surface map, output exactly: NO ADDITIONAL FINDINGS

From the artifact, check the ## Findings section for any findings already listed as Open.

Apply the same six patterns and three rules as the diff-based prompt above.

Output one finding per line in this format:
[FIXABLE|INVESTIGATE] | [critical|high|medium|low] | file:line — what the problem is; what it allows or causes; fix direction or what to investigate

If you find nothing new, output exactly: NO ADDITIONAL FINDINGS"</mandatory>

Process the test integrity agent output: apply the same renumbering, deduplication, and table-append rules as the adversarial agent. Use `[test-integrity]` instead of `[adversarial]` in the Description field:
- For each **FIXABLE** finding: `| F-NNN | pass N | [severity] (N/10) | file:line | [test-integrity] description | Open |`
- For each **INVESTIGATE** finding: `| F-NNN | pass N | [severity] (6/10) | file:line | [test-integrity][INVESTIGATE] description | Open |`
- If **NO ADDITIONAL FINDINGS**: append to the pass log: `Test integrity pass: no additional findings.`
- If the agent is **unavailable or errors**: append to the pass log: `Test integrity pass: unavailable.`

Continue to Phase 6.

</phase>

---

<phase id="6" name="fix-and-loop">

## Phase 6 — Fix and loop

<mandatory>**Phase 6 entry gate.** Before doing anything else in Phase 6, run:

```bash
grep -c "^### Pass .* — in progress" .vibe-check/vc-audit/[artifact-filename]
```

Quote the output verbatim. If the count is **> 0**: Phase 5 did not complete — the pass log header was never finalized from `— in progress` to a date. Return to Phase 5 now and complete it before continuing. Do not run the auto-fix pass or any other Phase 6 step until this grep returns **0**.</mandatory>

**Auto-fix pass (before decisions):** Use the Read tool to read the current findings table. Scan for every Open row that qualifies for auto-fix:
- Severity is `high` or `critical` — always qualifies, regardless of confidence
- Severity is `low` or `medium` AND confidence is `7/10` or higher (parse the `(N/10)` value from the Severity cell)

For each qualifying finding, in F-NNN order:
1. Attempt to apply the fix directly to the source file using the Edit tool. The fix direction is stated in the finding description. Reference the finding number in an inline code comment if appropriate (e.g., `// fix [F-003]: added null check`).
2. After the Edit, grep for a unique string that the fix introduces to verify it is present in the source file:
   ```bash
   grep -n "[unique string from your fix]" [source-file-path]
   ```
   Choose a string that can only appear if the fix was applied (e.g., for a fix replacing `{}` with `Object.create(null)`, grep for `Object.create(null)`). If grep returns 0 matches, the Edit failed — re-attempt the fix once, then re-grep.
3. **If grep confirms the fix is present:** immediately Edit the finding's Status cell from `Open` to `Resolved (pass N) [auto-fixed]`. Do not ask the user.
4. **If the Edit fails, or grep still returns 0 matches after the retry, or the correct change cannot be determined from the description:** leave Status as `Open`. The finding will be handled in the decision flow below.

After completing the auto-fix pass, tell the user: "Auto-fixed [N] findings: [F-NNN, F-NNN, ...]" (omit this line entirely if N = 0).

After the pass report:
1. For each **Acting on** item (`F-NNN`) that was not already resolved by the auto-fix pass above: apply the fix directly to the source file using the Edit tool. Reference the finding number in an inline code comment if appropriate (e.g., `// fix [F-003]: added null check`). The finding number will be included in the commit message by vc-ship when the branch ships. After the Edit, grep for a unique string the fix introduces to verify it is present in the source file (`grep -n "[unique string]" [source-file-path]`). If grep returns 0 matches, re-attempt the fix once, then re-grep. If it still fails, tell the user: "Could not apply the fix for [F-NNN] — please apply this change manually: [exact old and new text]." Once grep confirms the fix is present, immediately Edit the finding's Status cell in the findings table from `Open` to `Resolved (pass N)`. Do not proceed to the next Acting on item until the Status cell is updated. If the fix cannot be confirmed by grep, leave Status as Open — it will reappear as open on the next pass.
2. For each **Want to skip** item, run the decision protocol below. One AskUserQuestion
   per finding, in order. Do not group them — the question window is small and does not
   render markdown.
   <mandatory>Your ONLY valid action here is to call the AskUserQuestion tool. Do NOT:
   - Write any prose describing the finding, the options, or a recommendation to the user
   - Write "Want me to apply it?", "Here's my recommendation:", "Next step:", or any similar text
   - Present options as a markdown list or numbered list in your text output
   Prose output does not ask the user anything — it just talks at them without giving them a choice. Only AskUserQuestion creates an actual decision point.</mandatory>

   **Build the question text in plain text:**
   ```
   Finding [N] of [total] needs a decision

   [F-NNN] | [SEVERITY] | confidence [X]/10
   [file:line]

   What it is: [1 sentence describing the finding in plain language]

   Why this matters: [1-2 sentences. Describe the worst-case consequence in plain
   language — what bad thing happens, not the code pattern that causes it. Write
   for someone who understands computers but not this specific domain.]
   ```

   **Options:**
   - **Fix now** — Address this finding in the current pass
   - **Defer** — Real issue, I'll come back to it in a later pass
   - **Dismiss** — Not applicable to this project

   **If the user chooses Dismiss**, immediately ask a follow-up question:
   ```
   Why is [F-NNN] not applicable here?

   [F-NNN] | [one-line summary of the finding]
   ```

   Options:
   - **By design** — This behavior is intentional and I can explain why
   - **Wrong stack** — This project doesn't use the affected technology or pattern
   - **Already handled** — A separate mechanism in this project covers this
   - Other (user types a custom reason)

   **Record the outcome immediately:**
   - Fix now → finding stays Open; it moves to "Acting on" in the pass report and gets fixed in step 1 of this phase
   - Defer → immediately Edit the finding's Status cell from `Open` to `Deferred (pass N) — [reason if given]`. If the finding is tagged `[pre-existing]`, append "— create a ticket to address this issue" to the reason. Do not proceed to the next finding until the Status cell is updated.
   - Dismiss → immediately Edit the finding's Status cell from `Open` to `Dismissed (pass N) — [user's stated reason]`. Do not proceed to the next finding until the Status cell is updated.
3. Once fixes are applied and decisions recorded, use the Edit tool to increment `**Passes completed:**` in the artifact header (change `**Passes completed:** N-1` to `**Passes completed:** N` where N is the current pass number). Then run:

   ```bash
   grep "Passes completed:" .vibe-check/vc-audit/[artifact-filename]
   ```

   Quote the output verbatim. If the number shown is not N: re-edit the header now and re-grep to confirm before continuing. Then run the **pass checkpoint**.

   **Before running the pass checkpoint: resolve all open findings.**
   If any rows with Status = Open remain in the findings table, do not proceed to the checkpoint yet.
   For each Open finding: attempt to fix it now, or if fixing requires user judgment, present
   it to the user and request a decision (fix, defer, or dismiss). Do not close the pass with
   unresolved Open findings — work through them first.

   Once all open findings are resolved, count the current pass state from the artifact —
   read the file, do not reconstruct from memory:
   - Findings opened this pass: count findings table rows where Pass column = N (current pass number) — includes all Status values
   - Resolved this pass: count rows where Status contains `Resolved (pass N)`
   - Deferred this pass: count rows where Status contains `Deferred (pass N)`
   - Dismissed this pass: count rows where Status contains `Dismissed (pass N)`
   - Still open: count rows where Status = `Open`

   <definition name="clean-pass">**A pass is clean when:**
   1. Zero F-NNN findings were opened this pass. To verify: search the entire artifact for entries tagged `| pass N |` (where N is this pass number) — count every match, including those in Resolved and Dismissed sections. If the count is greater than zero, the pass is not clean. A finding opened and fixed in the same pass still makes the pass not clean — "opened-and-fixed" is the same as "opened-and-left-open" for this criterion. This definition is fixed and cannot be changed by in-conversation discussion. AND
   2. The pass log contains a surface receipt entry with at least one file:line citation
      for every surface in the surface map.
   A pass with no open findings but incomplete surface coverage is not clean — it is an
   incomplete pass.</definition>

   <mandatory>Run these three Bash commands to count findings rows mechanically. Do NOT compute these values from memory, context, or prior reads — the grep output is the only valid source:

   ```bash
   grep -c "| pass N |" .vibe-check/vc-audit/[artifact-filename]
   grep -c "| pass N-1 |" .vibe-check/vc-audit/[artifact-filename]
   grep -c "| Open |" .vibe-check/vc-audit/[artifact-filename]
   ```

   Substitute N with the current pass number, N-1 with the previous pass number, and [artifact-filename] with the actual filename (e.g. `playlist-insights.md`). If grep returns no output or 0, the count is 0 — not an error.

   The three numbers returned are CURRENT_PASS_FINDINGS, PREV_PASS_FINDINGS, and OPEN_COUNT. Use them exactly as returned. Do not override with narrative reasoning (e.g., "but the findings were fixed" or "I confirmed this earlier in this session"). A finding opened and immediately fixed in the same pass still appears as `| pass N |` in the table and will be counted by grep.</mandatory>

   **Convergence check:**

   1. CURRENT_PASS_FINDINGS = grep count of `| pass N |` rows (all Status values)
   2. PREV_PASS_FINDINGS = grep count of `| pass N-1 |` rows (all Status values)
   3. OPEN_COUNT = grep count of `| Open |` rows

   <mandatory>If OPEN_COUNT > 0: STOP. Do not proceed to the checkpoint. The grep count is authoritative — do not override it with your memory of what was "fixed" earlier in this session. For each finding still showing `| Open |` in the artifact, in order:
   1. Grep for a unique string that the fix should introduce to verify whether the code fix is actually present in the source file:
      ```bash
      grep -n "[unique string from the fix]" [source-file-path]
      ```
      Choose a string that can only appear if the fix was applied (e.g., for a null-prototype fix, grep for `Object.create(null)`). If grep returns 0 matches, the fix is absent.
   2. If the fix is NOT present (grep returned 0 matches): apply it now using the Edit tool on the source file, then re-grep to confirm.
   3. Only after grep confirms the fix is present in the source file: Edit the artifact to change `| Open |` to `| Resolved (pass N) |` for that row.
   Do NOT update the artifact Status to Resolved before step 1. Do NOT skip step 1 because you believe the fix was already applied in this session.
   After processing all Open findings, re-run `grep -c "| Open |" .vibe-check/vc-audit/[artifact-filename]` and confirm the count is 0 before continuing.
   Reaching the checkpoint with any `| Open |` rows in the artifact is a protocol violation.
   </mandatory>

   CONVERGENCE_CONDITIONS_MET = true ONLY if: CURRENT_PASS_FINDINGS = 0 AND PREV_PASS_FINDINGS = 0 AND OPEN_COUNT = 0. If N < 2 (fewer than two passes have run), CONVERGENCE_CONDITIONS_MET = false — convergence requires at least two passes.

   **Critical:** PREV_PASS_FINDINGS counts findings OPENED in pass N-1, regardless of their current Status. A finding opened in pass 1 and immediately fixed still counts toward pass 1's finding total. Example: if pass 1 opened 9 findings (all now Resolved), then after pass 2: PREV_PASS_FINDINGS = 9 → CONVERGENCE_CONDITIONS_MET = false, even if pass 2 is completely clean. In that case, pass 3 would be the earliest possible convergence opportunity (if both pass 2 and pass 3 open zero findings).

   Store CONVERGENCE_CONDITIONS_MET. Do not announce this determination — just store it.

   <mandatory>CONVERGENCE_CONDITIONS_MET = true does NOT authorize convergence. It only unlocks the "Declare convergence" option in the AskUserQuestion checkpoint. You MUST NOT write `**Status:** CONVERGED`, append any convergence text, or take any terminal action before AskUserQuestion returns and the user selects "Declare convergence". The user owns this decision — not you. Proceed directly to the AskUserQuestion call below. Do not write any text output first.</mandatory>

   **If this is a scoped audit** (artifact path contains `--`) AND CONVERGENCE_CONDITIONS_MET is true: run `git diff BASE_BRANCH --name-only` to get the full tracked file list, and check `git status --porcelain` for any UNTRACKED_FILES (filtered). Combine both for the full branch file list. Glob `.vibe-check/vc-audit/[branch-slug]--*.md` to find all other scoped audit artifacts for this branch. Compute which files on this branch are not covered by any scoped audit. If unaudited files remain, set CONVERGENCE_CONDITIONS_MET = false and note the uncovered files.

   **Note for small branches:** On branches with fewer than five changed files, if CONVERGENCE_CONDITIONS_MET is true, verify the surface map has one entry per changed file and that each receipt entry cited actual line numbers. If coverage is superficial, set CONVERGENCE_CONDITIONS_MET = false.

   <mandatory>Your ONLY valid next action is to call AskUserQuestion with the pass checkpoint below. Do NOT:
   - Write any text output to the user about the pass results, findings, next steps, or options (e.g. "Pass 1 found 4 issues…", "Ready to run Pass 2…", "Next step:…")
   - Write anything to the artifact
   - Write a status like CONVERGED, DONE, STOPPED, or any terminal phrase to the artifact header or pass log
   - End your response
   - Take any other action
   until AskUserQuestion has been called and the user has responded. This applies regardless of pass outcome, finding count, or how trivial the findings were. There are no exceptions. The AskUserQuestion tool call is the only valid communication channel for the pass checkpoint.

   Call AskUserQuestion with the pass checkpoint. AskUserQuestion strips line breaks — use ` | ` as a section separator so the text remains readable in a single line. Use this exact format — plain text, no markdown:

   **Question text:**
   ```
   Pass [N] complete | fixed [N] · deferred [N] · dismissed [N] · new [N] | still open: [N][If CONVERGENCE_CONDITIONS_MET: add " | two consecutive clean passes"][If scoped audit with uncovered files: add " | uncovered: [list]"] | [artifact path]
   ```

   Example (pass 22, one finding opened and fixed, nothing open):
   ```
   Pass 22 complete | fixed 1 · deferred 0 · dismissed 0 · new 1 | still open: 0 | .vibe-check/vc-audit/playlist-insights.md
   ```

   **Options — always include these three:**
   - **Continue to pass [N+1]** — Run the next pass now
   - **Pause** — Stop here; resume later by running /vc-audit again
   - **Stop** — Done auditing; I will review and decide on open findings myself

   **Additional option — include only if CONVERGENCE_CONDITIONS_MET is true:**
   - **Declare convergence** — Mark this audit complete (two clean passes, nothing open)
   </mandatory>

   <mandatory>Option labels are fixed strings — transcribe them verbatim into the AskUserQuestion call. Do NOT:
   - Add parenthetical text to any label (e.g., "(converge)", "(one more pass)", "(I'll continue later)")
   - Rename "Stop" to "accept and close now" or any other phrase
   - Rename "Declare convergence" to any other phrase
   - Add "Declare convergence" when CONVERGENCE_CONDITIONS_MET = false
   - Omit "Stop" from any checkpoint

   Offering "Declare convergence" when the grep count of `| pass N |` rows is greater than zero is a protocol violation. The grep counts are authoritative. "The findings were fixed in the same pass" does not change the count — grep still counts them.
   </mandatory>

   **If the user chooses Stop**: use the Read tool to read the entire artifact fresh. If the Read returns exactly 2000 lines, re-read with increasing offsets (2000, 4000, …) until a read returns fewer than 2000 lines — concatenate all parts before writing. Write the artifact back using the Write tool with `**Status:** STOPPED` in the header and the findings table rows grouped under status section headers (see **Grouped findings format** below). After the Write, use the Read tool to verify `**Status:** STOPPED` appears. If it does not, re-attempt once. If it still fails, tell the user: "Could not update the artifact — please change the `**Status:**` line to `**Status:** STOPPED` manually." Then stop. A STOPPED audit will not auto-resume; the user must re-run /vc-audit to start a new session.
   **If the user chooses Pause**: stop immediately without modifying the artifact. Phase 3 detects the IN PROGRESS artifact on the next run and resumes from where this pass left off.
   **If the user chooses Continue**: use the Edit tool to append `**Next pass:** Authorized` as a new line at the end of the current pass log entry in the artifact. This token is required by the Phase 4 authorization gate — without it, the next pass cannot start. Then start Phase 4 from the very beginning — the authorization gate, the pass-start marker, and the `## Pass N progress` section must all be executed before any surface walk begins. Do not jump directly into reading files or running bash commands. The required sequence is:
   1. Pass the Phase 4 authorization gate — grep the artifact for `**Next pass:** Authorized`, confirm count is 1, delete the line, then proceed
   2. Write `### Pass N — in progress` to the artifact pass log
   3. Append a fresh `## Pass N progress` section listing every surface as `[ ]`
   4. Then begin the surface walk, one surface at a time, checking off `[x]` after each one

   Do not skip surfaces because they were clean last pass. Do not skip steps 2 or 3 — without them, a compaction or interruption mid-pass leaves no record of what was completed.

   **If the user selects "Declare convergence"**: First, use the Edit tool to append `**Convergence authorized by user**` as a new line at the end of the current pass log entry. Then run:
   ```bash
   grep -c "Convergence authorized by user" .vibe-check/vc-audit/[artifact-filename]
   ```
   Count must be **1**. If it is **0**: you have reached this step without the user selecting "Declare convergence" from AskUserQuestion — stop, do not write CONVERGED, and call AskUserQuestion with the checkpoint now. Only proceed past this gate when the grep returns 1.

   Then use the Read tool to read the entire artifact fresh. If the Read returns exactly 2000 lines, re-read with increasing offsets (2000, 4000, …) until a read returns fewer than 2000 lines — concatenate all parts before writing. Count findings table rows by Status to get the final totals (Open, Resolved, Deferred, Dismissed). Write the artifact using the Write tool with:
   - `**Status:** CONVERGED` in the header
   - `**Converged:** [date]` on the next line after Status
   - `**Findings:** [N] open | [N] resolved | [N] deferred | [N] dismissed` on the line after that
   - The findings table rows grouped under status section headers (see **Grouped findings format** below)
   Do not add a new `**Passes completed:**` line — it already exists in the header and must not be duplicated. After the Write, use the Read tool to verify `**Status:** CONVERGED` and `**Converged:**` appear in the header. If they do not, re-attempt once. If it still fails, tell the user: "Could not update the artifact — please change the `**Status:**` line to `**Status:** CONVERGED` and add `**Converged:** [date]` and `**Findings:** [N] open | [N] resolved | [N] deferred | [N] dismissed` manually."

   Once the artifact is verified CONVERGED, run this Bash command to notify the user:
   ```
   afplay /System/Library/Sounds/Ping.aiff 2>/dev/null || powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Runtime.WindowsRuntime; [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null; [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null; \$xml = [Windows.Data.Xml.Dom.XmlDocument]::new(); \$xml.LoadXml('<toast><visual><binding template=\"ToastText01\"><text id=\"1\">vc-audit converged</text></binding></visual></toast>'); [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show([Windows.UI.Notifications.ToastNotification]::new(\$xml))" 2>/dev/null || notify-send 'Claude Code' 'vc-audit converged' 2>/dev/null || true
   ```

   **If the user chooses Pause**, stop immediately — do not run another pass. Phase 3 will detect the existing artifact on the next run and resume from where this pass left off.

   **If the user chooses Continue or Run one more pass**, loop back to Phase 4 and
   run a full pass from scratch. Do not skip surfaces because they were clean last pass.

### Grouped findings format

Used when writing the artifact at Stop or Declare convergence. Replace the flat `## Findings` table with rows grouped under status section headers:

```markdown
## Findings

### Open

| ID | Pass | Severity | Location | Description | Status |
|---|---|---|---|---|---|
| F-NNN | ... | ... | ... | ... | Open |

### Resolved

| ID | Pass | Severity | Location | Description | Status |
|---|---|---|---|---|---|
| F-NNN | ... | ... | ... | ... | Resolved (pass N) |

### Deferred

| ID | Pass | Severity | Location | Description | Status |
|---|---|---|---|---|---|
| F-NNN | ... | ... | ... | ... | Deferred (pass N) — reason |

### Dismissed

| ID | Pass | Severity | Location | Description | Status |
|---|---|---|---|---|---|
| F-NNN | ... | ... | ... | ... | Dismissed (pass N) — reason |
```

If a group has no rows, replace its table with `_none_`. Derive the grouped content from the Read output — do not reconstruct from memory.

</phase>
<!-- COMPACT_HOOK_END -->

---

## Artifact location

Artifacts live at `.vibe-check/vc-audit/` in the repo root. Naming convention:

- Full audit: `.vibe-check/vc-audit/[branch-slug].md`
- Scoped to a directory: `.vibe-check/vc-audit/[branch-slug]--src-auth.md`
- Scoped to a file: `.vibe-check/vc-audit/[branch-slug]--src-auth-session-ts.md`
- Scoped to multiple paths: `.vibe-check/vc-audit/[branch-slug]--[user-chosen-name].md`

The audit artifact will be committed automatically when you run `/vc-ship` — it commits all `.vibe-check/` changes before pushing so the artifact travels with the PR.

Reviewers reading the artifact should be able to answer:
- What surfaces were walked?
- What was found, what was fixed, and in which pass?
- What was explicitly dismissed and why?
- What was deferred and is it still open?
- Has the audit actually converged, or did the author stop early?
