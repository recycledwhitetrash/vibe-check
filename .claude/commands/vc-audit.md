---
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - Glob
---
<!-- AUTO-GENERATED from src/vc-audit.md.tmpl — do not edit directly -->

# /vc-audit — Branch Deep Walk Audit

<!-- version: 2026-06-19.13 -->

Drop `/vc-audit` at the start of any review session. It orients itself to the branch,
selects the right lenses for the code it finds, and walks every changed surface against
every applicable lens. During each pass an optional adversarial subagent runs in the
background in parallel with the structured walk and is collected at the end of the pass.

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

**`vc-audit` version matches `2026-06-19.13`**: proceed silently.

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

**Fetched version is older than `2026-06-19.13`**: proceed silently. (This can happen with CDN caching or a rollback — the local version is already newer.)

</output-handlers>

**Auto-update:**
1. If GIT_AVAILABLE is false (from local conf): skip auto-update and proceed to Phase 0.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the Bash tool to download and overwrite the skill file in one step:
   - bash/zsh: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-audit.md -o "[project-root]/.claude/commands/vc-audit.md"`
   - PowerShell: `curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-audit.md -o "[project-root]/.claude/commands/vc-audit.md"`
4. If curl exits 0: tell the user "Updated to the latest version — reloading skill from disk." Then use the Read tool to read `[project-root]/.claude/commands/vc-audit.md`. Proceed to Phase 0 of the updated skill, following the instructions just read. Do not re-run the version check — the update is already complete.
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
git diff BASE_BRANCH...HEAD --name-only -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' [gitignored tracked files as :!path exclusions] [scope paths if $ARGUMENTS provided]
git diff BASE_BRANCH...HEAD --shortstat -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' [gitignored tracked files as :!path exclusions] [scope paths if $ARGUMENTS provided]
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
  - If UNCOMMITTED_TRACKED or UNTRACKED_FILES is non-empty: real work is in progress. Run `git diff BASE_BRANCH --shortstat [same exclusions]` to get the tracked-change count. Add the number of UNTRACKED_FILES to the file count for the LARGE_DIFF check — untracked files have no diff but still require a full Read and must be counted. Tell the user: "No commits on this branch yet — [N] uncommitted file(s) detected (plus [U] untracked). Auditing working tree changes vs [BASE_BRANCH]." Proceed.
  - If both are empty: check whether a plan stub exists at `.vibe-check/vc-plan/[branch-slug].md` and contains a `## Chunk files` section.
    - If plan stub with `## Chunk files` found and the section lists at least one file path: set FILE_READ_MODE = true. Note the file list from that section — this branch was set up by `/vc-onboard` and the audit will scan those files directly rather than a diff. Tell the user: "No changes detected vs [BASE_BRANCH]. A chunk file list was found in the plan stub — scanning chunk files directly instead of a diff." Proceed directly to Phase 1 using the chunk file extensions and paths for stack detection — skip the diff read and plan context check below.
    - If plan stub with `## Chunk files` found but the section is empty (no file paths listed): tell the user "The `## Chunk files` section in the plan stub is empty — nothing to audit in FILE_READ_MODE. Check the plan stub at `.vibe-check/vc-plan/[branch-slug].md` and ensure the section lists the files this branch covers." Stop.
    - If no plan stub or no `## Chunk files` section: tell the user "No changes detected vs [BASE_BRANCH] and no chunk file list was found. There is nothing to audit on this branch yet — make some changes first, then re-run /vc-audit." Stop.
- LARGE_DIFF check: if committed shortstat was empty but uncommitted/untracked files exist, use the `git diff BASE_BRANCH --shortstat` file+insertion counts plus the UNTRACKED_FILES count as the total. If total files > 15 or insertions > 800, this is a **LARGE_DIFF** — call AskUserQuestion: "This branch touches N files / ~M lines, which may be too large to fully audit in one context window. How would you like to proceed?"
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

Read the actual diff of every changed file — not just the stat. You need to understand
what each file does and how the changes interact before selecting lenses.
Sensitive files are excluded from the diff automatically (see Sensitive File Protection).

```bash
git diff BASE_BRANCH -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' ':!node_modules/**' ':!**/node_modules/**' ':!dist/**' ':!build/**' ':!.next/**' ':!.nuxt/**' ':!vendor/**' ':!*.pyc' ':!.venv/**' ':!venv/**' ':!target/**' ':!out/**' ':!.gradle/**' [gitignored tracked files as :!path exclusions — from `git ls-files --cached --ignored --exclude-standard` above]
```

Substitute BASE_BRANCH with the value determined above. For an initial commit session, substitute `4b825dc642cb6eb9a060e54bf8d69288fbee4904`. This command (`git diff BASE_BRANCH`) captures committed changes, staged changes, and unstaged tracked changes in one shot. If UNTRACKED_FILES is non-empty, use the Read tool to read those files separately — no diff exists for files never added to git.

<gate>Do not proceed past this block until you have the diff output (and have read any UNTRACKED_FILES). The code in this diff is what you will walk in Phase 4 — it must be in your context before you select lenses.</gate>

### Stack detection

From the file list and diff, identify which of the following stacks are in play.
**More than one can apply.**
**If FILE_READ_MODE is true:** substitute the chunk file paths and their extensions for "the file list and diff" — no diff is available; derive stack indicators from filenames and directory names only.
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

Based on the stack(s) detected, select applicable lenses from the list below.
**Universal lenses always apply.** Stack-specific lenses apply when that stack is in play.
Never exclude a lens because "we're not focusing on that" — if it could catch something,
include it. The selection is to avoid wasting time on lenses that are structurally
inapplicable (e.g., don't walk RLS bypass patterns in a bash-only change).

State your selection in the audit artifact before walking anything.

### Universal lenses — always apply

- **Correctness**: off-by-one, wrong branch taken, illegal state transitions, NULL/nil
  handling, comparison operators, ordering, default values that violate invariants,
  logic errors in conditions; integer overflow/underflow on arithmetic involving user-
  supplied values (amounts, counts, offsets); type confusion where the same variable holds
  different types across branches; boundary conditions on empty collections and single-
  element collections specifically (off-by-one is most common at the edges);
  algorithmic complexity — O(n²) or worse from nested loops over the same collection,
  `find`/`filter` inside `map`/`forEach`, repeated sorting of the same list, or string
  concatenation in a loop; consider whether a hash/set/map lookup would replace a
  linear scan
- **Error handling**: swallowed exceptions/errors, non-fatal treatment of fatal conditions,
  partial failure leaving inconsistent state, missing rollback, fallbacks that silently mask
  bugs; for scripts: exit codes not checked, `pipefail` absent, `2>/dev/null` on errors
  that should be fatal; retryable vs non-retryable errors not distinguished — retrying a
  non-retryable error forever wastes resources and delays failure, dropping a retryable
  error silently loses work; panic/crash recovery boundary wrong (`recover` in Go,
  `catch_unwind` in Rust) — panic caught too broadly masking bugs, or not caught at the
  right boundary causing process crash
- **Observability & audit**: missing log points where forensics will need them, sensitive
  actions not recorded, audit records that can be erased or overwritten, metrics gaps on
  hot paths, no way to correlate events after an incident; unstructured log messages that
  can't be queried in production incident tools; correlation/trace IDs not propagated
  across service or function calls (can't reconstruct a full request path post-incident);
  health check or readiness endpoint returning 200 even when the service is degraded
  (downstream load balancer keeps sending traffic to a broken instance)
- **Privacy & compliance**: PII in logs, errors, or payloads; data retained longer than
  promised; exports or responses that include more than the caller needs; cross-tenant or
  cross-user data leakage in shared resources; GDPR/CCPA right-to-erasure — does a delete
  actually remove data from all stores (backups, audit logs, caches, analytics pipelines)
  or only the primary DB? data minimization at collection — is the system collecting more
  fields than it needs?
- **Configuration & deploy**: env vars referenced but not declared; secrets in code, logs,
  or error messages; feature flags with no kill switch; assumptions about deploy environment
  baked into logic; config validated at startup (fail fast, clean error) vs at first use
  (fails mid-request, partial state); behavior differences across environments that mask
  bugs (e.g. a dev default that hides a prod misconfiguration)
- **Dependencies & supply chain**: lockfile drift vs. pinned versions, deprecated APIs,
  risky transitive packages, packages with known CVEs; typosquatting — package name one
  character off from a popular one (e.g. `lodahs` instead of `lodash`); `postinstall`
  scripts in npm/yarn packages executing arbitrary code at install time — check unfamiliar
  packages for these; `git+https://` dependencies where the commit can be force-pushed
  after your audit; `--frozen-lockfile` / `--ci` / `npm ci` not used in the build pipeline
  so the lockfile can drift silently between dev and CI
- **Test integrity**: tests that pass without actually exercising the claim, mocks that hide
  real production behavior, missing tests on attack vectors or failure paths changed in this
  branch; snapshot tests that auto-update (`--updateSnapshot`) without human diff review —
  they always pass because they overwrite their own expected output; tests asserting on
  implementation details (private method calls, internal state) rather than observable
  behavior — pass when the bug exists; flaky tests marked `.skip`, `xit`, or `@pytest.mark.skip`
  without a tracking issue or removal deadline
- **Documentation & comments**: contradicts the code, references removed code, claims
  invariants that are no longer true, missing where a future reader would otherwise make a
  wrong assumption
- **Encoding / serialization**: JSON/CSV/XML injection when building output from user input,
  numeric precision loss across serialization (float → string → float), length limits not
  enforced before writing, character encoding assumptions (UTF-8 vs Latin-1 vs system
  locale); Python `yaml.load()` on user-controlled input executes arbitrary code —
  must be `yaml.safe_load()`; XML External Entity (XXE) injection when parsing XML from
  untrusted sources without disabling external entity resolution; prototype pollution in
  JavaScript via `JSON.parse()` on objects with `__proto__` or `constructor` keys (affects
  object-spread and property access on shared prototypes)
- **Resource management**: file descriptor or socket leaks on error paths, DB connections
  not returned to pool, temp files not cleaned up, no size or quota check before writing
  large output, cleanup missing on SIGTERM/SIGKILL; connection pool exhaustion under
  sustained load — all connections checked out, new requests queue indefinitely or time
  out; goroutine or thread leaks from spawned workers that are never joined or cancelled;
  memory leaks from closures capturing large objects that are never released
- **Maintainability**: dead code — variables assigned but never read, functions defined
  but never called (check with the Grep tool across the repo), imports no longer
  referenced after this change; magic numbers — bare numeric literals used in logic
  (thresholds, limits, retry counts, timeouts) that should be named constants; hardcoded
  URLs, hostnames, or ports that belong in config; DRY violations — similar code blocks
  (3+ lines) copy-pasted in the diff where a shared helper would remove the duplication;
  conditional side effects — one branch updates a related record, emits an event, or
  writes a log but a sibling branch silently skips that same step; module boundary
  violations — a caller reaching into another module's internals directly, or database
  queries placed in layers (controller, view, route handler) that don't own data access
- **API contract**: applies when the diff touches routes, endpoints, or response shapes —
  regardless of language or framework (Node/Express, Python/Flask/FastAPI/Django REST,
  Go, Ruby/Rails, etc.); breaking changes to response shape — removed or renamed fields,
  changed field types (string → number, object → array), new required request parameters
  added without a default; changed HTTP methods or status codes on existing endpoints;
  versioning strategy inconsistency (mixing URL-path `/v1`, header, and query-param
  versioning in the same API); error response format inconsistent with other endpoints in
  the codebase; list endpoints with no pagination and no `LIMIT` that grow unboundedly
  with data; rate limiting absent on an endpoint where similar endpoints have it; API
  documentation (OpenAPI/Swagger spec, README) not updated to match changed behavior;
  backwards compatibility for clients that can't force-update (mobile apps, third-party
  integrations, older SDK versions that may still be in use)
- **Cryptographic misuse**: weak hashing algorithms (MD5, SHA1) used for security-sensitive
  operations such as password storage or token generation; predictable randomness
  (`Math.random()`, Python `random`, `rand()`) used to generate tokens, session IDs,
  nonces, or CSRF values — must use a cryptographically secure RNG; non-constant-time
  comparison (`==`, `===`, `string.compare()`) on secrets, HMAC digests, or API tokens
  enables timing attacks that reveal whether a guess is correct; hardcoded encryption
  keys or initialization vectors; missing salt in password hashing (bcrypt/argon2 handle
  this automatically; hand-rolled hashing often forgets it)
- **Anything else**: if it smells wrong and doesn't fit a category, surface it. The lenses
  are a starting point, not a scope boundary.

### Web / frontend lenses — React, Next.js, browser apps

- **Frontend / UX integrity**: dead-end error states, unhandled loading states, optimistic
  updates that don't reconcile on failure, forms that submit invalid or partial state, no
  error boundary, keyboard/focus traps that strand non-mouse users
- **Accessibility**: keyboard-only flows broken, screen reader markup missing or wrong,
  interactive elements without accessible labels, focus management on dialogs and modals
- **API & contract (client side)**: assumptions about response shape that will break on API
  change, no handling for unexpected fields or missing fields, request size not capped on
  client, auth token handling (storage, refresh, expiry)
- **XSS vectors**: `dangerouslySetInnerHTML` with any value derived from user input or
  external data; `href` / `src` / `action` attributes set from user-controlled strings
  without blocking `javascript:` URLs (`javascript:alert(1)` is a valid href); `eval()` or
  `new Function()` called with any dynamic content; third-party scripts loaded from
  user-supplied URLs
- **React hooks bugs**: `useEffect` missing cleanup for timers, subscriptions, and fetch
  calls — fires state updates on unmounted components and leaks memory; stale closure from
  an incomplete dependency array — the effect reads an old value of a variable that has
  since changed; async race condition where multiple concurrent calls compete to set state
  and the last-to-resolve wins regardless of which was last-started (fix: abort controller
  or sequence counter); object or array literal created inline in JSX props or a
  `useEffect` dependency array — new reference every render, causes infinite loop
- **Auth — client-side gaps**: route guard that only hides the UI but the underlying API
  route has no auth check — bypassed by calling the API directly; auth tokens stored in
  `localStorage` or `sessionStorage` are readable by any XSS payload — prefer httpOnly
  cookies for session tokens; token refresh race condition when multiple parallel requests
  all receive 401 simultaneously and each independently attempts a refresh (token rotation
  invalidates the others); JWT decoded on the client and claims trusted without
  server-side verification — the client can't verify the signature
- **Environment variable leakage**: `NEXT_PUBLIC_` or `REACT_APP_` prefixed variables are
  inlined into the browser bundle at build time — any secret assigned to them is shipped to
  every user; source maps deployed to production expose full original source code to anyone
  who opens devtools
- **Next.js data exposure**: `getServerSideProps` / `getStaticProps` returning objects with
  sensitive fields (user records, internal config, tokens) — the full return value is
  serialized into `__NEXT_DATA__` in the page HTML and visible to anyone who views source;
  API routes under `pages/api/` or `app/api/` missing authentication checks; server actions
  without authorization (any authenticated user can invoke them, not just the intended
  role); `next.config.js` rewrites that proxy internal services without adding an auth
  header; no security headers set (`Content-Security-Policy`, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`) — Next.js does not set these by default
- **Form security**: client-side validation with no equivalent server-side check — disabled
  JavaScript or a direct API call bypasses it entirely; sensitive form data submitted via
  GET method appears in browser history, server access logs, and the `Referer` header sent
  to third parties; file input with no size or type check on the client before upload begins
- **Content Security Policy**: CSP header absent, or set with `unsafe-inline` or
  `unsafe-eval` in `script-src` — without a restrictive CSP a successful XSS can load
  arbitrary external scripts and exfiltrate data; `report-uri` or `report-to` absent so
  violations are never observed
- **Subresource Integrity (SRI)**: third-party scripts and stylesheets loaded from CDNs
  without an `integrity="sha384-..."` attribute; a compromised CDN, a BGP hijack, or a
  CDN provider incident silently serves malicious content to all users
- **Clickjacking**: no `X-Frame-Options: DENY` header and no `frame-ancestors 'none'` in
  CSP; the page is embeddable in an attacker's iframe and user clicks on sensitive actions
  (confirm payment, approve OAuth, delete account) are intercepted
- **Cookie security flags**: session cookies or auth cookies set without `Secure` (sent
  over HTTP), `HttpOnly` (readable by JS), or `SameSite=Lax`/`Strict` (CSRF vector);
  applies to cookies set in Next.js API routes, server actions, and `Set-Cookie` response
  headers
- **React Server Component data boundary**: RSC props passed across the `"use client"`
  boundary are serialized into the browser bundle; sensitive server-side data (DB records,
  internal config, access tokens) included in those props crosses the trust boundary and
  is visible to the user in the page source or network tab
- **Accessibility gaps**: color contrast ratio below 4.5:1 on body text or 3:1 on large
  text; CSS animations or transitions that do not respect `prefers-reduced-motion: reduce`;
  layout that breaks or clips content at narrow viewport widths, trapping users
- **Bundle size and rendering performance**: new production dependencies that are
  known-heavy (moment.js, full lodash, jQuery) when a lighter alternative or native API
  exists; barrel imports (`import { x } from 'library'`) instead of deep imports
  (`import x from 'library/specific'`) that block tree-shaking and inflate the bundle;
  `React.memo`, `useMemo`, or `useCallback` absent on components or computed values
  passed as props where reference instability causes unnecessary child re-renders;
  sequential `await fetch()` calls that could be `Promise.all` (fetch waterfall);
  layout thrashing — reading DOM geometry (`.offsetHeight`, `.getBoundingClientRect()`)
  then writing layout properties inside the same loop; below-fold images missing
  `loading="lazy"`

### React Native lenses

- **Insecure data storage**: `AsyncStorage` stores data in plaintext and is readable on
  rooted/jailbroken devices and via `adb backup`; use `react-native-keychain` or
  `expo-secure-store` for tokens, credentials, and PII
- **Hardcoded secrets in the JS bundle**: React Native ships the JS bundle as a readable
  file — any string in the bundle (API keys, internal URLs, signing secrets) is trivially
  extractable with a decompiler or `strings`; secrets belong in environment variables
  resolved at build time, never in source
- **Deep link handling without validation**: `myapp://reset-password?token=X` and similar
  deep links accepted without verifying origin or sanitizing parameters; a malicious web
  page can trigger deep links targeting your app; validate all deep link payloads as
  untrusted input
- **WebView with JS bridge open to remote content**: `javaScriptEnabled` on a WebView
  loading a third-party or user-supplied URL; the `onMessage` handler trusting any origin;
  a compromised page can call into your React Native code via `postMessage`
- **Biometric auth bypassed**: `TouchID`/`FaceID`/fingerprint used as a UX gate but the
  actual authorization check is done client-side — a rooted device or hook can spoof the
  result; the server must be the authority on whether the session is authenticated
- **Metro bundler exposed on dev builds**: Metro serves the JS bundle over HTTP on the
  local network during development; a dev build shipped to testers or left on a shared
  network exposes the full source to anyone on that network
- **Expo-specific**: OTA updates via EAS Update deliver a new JS bundle that bypasses app
  store review — a compromised update server or a missing code-signing check can push
  malicious code to all installed instances silently
- **Network security / certificate pinning**: no SSL certificate pinning allows MITM
  attacks on rooted/jailbroken devices; cleartext HTTP allowed via Android
  `android:usesCleartextTraffic="true"` in the manifest or iOS `NSAllowsArbitraryLoads`
  in Info.plist; no minimum TLS version enforced; pinned certificate hashes not updated
  before certificate rotation (causes production outage)
- **App Transport Security / Network Security Config**: iOS ATS and Android NSC exception
  domains broader than necessary; `NSExceptionAllowsInsecureHTTPLoads` or
  `cleartextTrafficPermitted` with domain wildcards; exceptions added during development
  and never removed before production
- **Runtime permission handling**: sensitive permissions (camera, microphone, location,
  contacts) requested at app launch rather than at the point of first use; no rationale
  string explaining why the permission is needed; app not gracefully handling permission
  denial — crashes or shows a blank screen instead of a degraded-but-functional state
- **Debug artifacts in release builds**: `__DEV__` flag used as a security gate;
  `console.log` calls printing tokens, user data, or internal URLs left in release builds
  (readable by other apps on non-sandboxed Android via `adb logcat`); Reactotron or
  Flipper debug bridges left open in release configurations
- **Third-party SDK data collection**: analytics SDKs, crash reporters (Firebase Analytics,
  Sentry, Amplitude, Crashlytics) collecting device identifiers or PII without user
  consent; data sent to third-party servers not disclosed in the privacy policy; IDFA/GAID
  usage without the required consent flow on iOS 14+ / Android 12+

### Browser extension lenses

- **Over-broad manifest permissions**: `"matches": ["<all_urls>"]` or host permissions for
  all sites when only a subset is needed; `tabs`, `history`, `bookmarks`, `cookies`
  declared without necessity — each is a privacy risk and a breach vector if the extension
  is compromised
- **Content scripts trusting page content**: content scripts reading DOM values (form
  fields, page text, cookies) and forwarding them to the background; a malicious page can
  poison those values to inject data into your extension's context
- **Message passing without origin validation**: `chrome.runtime.onMessage` accepting
  messages from any sender without checking `sender.id` or `sender.origin`; content
  scripts treated as trusted when they may be running in a hostile page context
- **`chrome.storage` holding secrets in plaintext**: `storage.local` and `storage.sync`
  are readable by all extension scripts and accessible to users via DevTools; tokens and
  credentials stored here are exposed to any XSS or content script compromise
- **`externally_connectable` too broad**: allows arbitrary web pages to send messages
  directly to the extension background; should be locked to specific origins
- **`eval()` or remote code execution**: `eval()`, `new Function()`, or
  `importScripts()` with a remote URL — all violate Manifest V3 CSP and create code
  injection vectors; extension code must be self-contained and static
- **`chrome.tabs.executeScript` / `scripting.executeScript` with dynamic strings**: calling
  these with a user-controlled or externally-derived code string is equivalent to `eval()`
  with elevated privileges — only ever pass hardcoded string arguments
- **Background service worker lifecycle**: Manifest V3 service workers are terminated by
  the browser after ~30 seconds of inactivity; module-level variables are lost on
  termination; state that must persist across events must go to `chrome.storage`, not
  memory; code that assumes the service worker is always alive will silently lose state
- **Web accessible resources**: files listed in `web_accessible_resources` in
  `manifest.json` are fetchable by any web page at `chrome-extension://[id]/[file]`;
  internal config files, key material, or data files accidentally listed become accessible
  to all origins
- **Content script DOM access scope**: content scripts share the full DOM with the page
  they run in; a content script that reads `document.forms`, `document.cookie` (when
  `HttpOnly` is absent), or intercepts `input` events has privileged access to every page
  the extension matches; over-broad `matches` combined with DOM reading is a significant
  privacy risk even without an explicit bug
- **Extension update supply chain**: extensions auto-update silently; a compromised Chrome
  Web Store publisher account or a self-hosted update URL under attacker control can push
  a malicious version to all installed instances with no user approval beyond the original
  install; treat the update endpoint and publisher credentials as high-value secrets

### Django lenses

- **ORM safety**: `.raw()`, `.extra()`, and `RawSQL()` with string-formatted user input — are
  all values passed via `params=`? `QuerySet.filter()` used where `.get()` would raise
  `DoesNotExist` unhandled; `.get_or_create()` race condition under concurrent requests;
  `bulk_create()` / `bulk_update()` bypassing `save()` signals and validators — are those
  signals load-bearing? missing `select_for_update()` on rows that must not be double-spent
- **N+1 queries**: `select_related()` / `prefetch_related()` absent on foreign keys accessed
  in loops or templates; serializers iterating over querysets without prefetch; Django admin
  list views with callable fields hitting the DB per row
- **Auth and permissions**: view missing `@login_required` or `LoginRequiredMixin`; class-based
  view `get_queryset()` not filtering by `request.user` — any authenticated user can request
  any object by ID; object-level permission check (`has_object_permission`, `django-guardian`)
  absent where row-level isolation is required; `request.user.is_staff` used as an
  authorization check without also checking `is_active`
- **CSRF**: `@csrf_exempt` on a state-changing view; AJAX requests not sending
  `X-CSRFToken`; `CsrfViewMiddleware` removed from `MIDDLEWARE`; cookie flags —
  `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE` not set
- **Redirect safety**: `next` parameter in login/logout redirects accepted without validating
  the host — open redirect to attacker-controlled URL; `redirect(request.GET.get('next'))`
  without `url_has_allowed_host_and_scheme()` check
- **Template XSS**: `{{ var|safe }}` suppresses autoescaping — is the value actually safe?
  `mark_safe()` called on any string derived from user input or external data; custom template
  tags that return unescaped HTML; `Template(user_input)` — Django template injection gives
  arbitrary attribute access on context objects
- **File upload**: `FileField` / `ImageField` with no content-type or extension validation;
  upload path containing user-controlled segments (path traversal); no file size limit before
  writing; uploaded files served from a path under `MEDIA_URL` without access control
- **Settings hardening**: `DEBUG = True` shipped to production (leaks full tracebacks and SQL
  queries); `ALLOWED_HOSTS = ['*']` or empty in production; `SECRET_KEY` hardcoded in
  `settings.py` or committed to git; `SecurityMiddleware` not first in `MIDDLEWARE` (HTTPS
  redirect and HSTS won't apply); `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`,
  `SECURE_BROWSER_XSS_FILTER` not set; `CORS_ALLOW_ALL_ORIGINS = True` with credentials
- **Django REST Framework** (if `rest_framework` is installed): `permission_classes` not set
  or set to `AllowAny` on a view that mutates data; `DEFAULT_PERMISSION_CLASSES` in settings
  too permissive for the API surface; serializer missing `read_only_fields` on fields the
  caller must not write (e.g., `owner`, `created_at`, `is_staff`); `ModelSerializer` with
  `fields = '__all__'` — exposes internal fields; `throttle_classes` absent on
  unauthenticated endpoints; `validated_data` bypassed — logic reading from `request.data`
  directly after a failed `is_valid()` check
- **Signals and middleware**: `post_save` signal handler calling `.save()` without
  `update_fields` — triggers infinite signal loop; signal handler that raises silently
  (Django swallows signal exceptions by default); custom middleware mutating `request` in
  a way that breaks downstream middleware ordering assumptions
- **Mass assignment**: `ModelForm` without an explicit `fields` list or `exclude` — a
  caller can POST any field name and overwrite sensitive model attributes (`is_staff`,
  `owner_id`, `subscription_tier`); `ModelForm(request.POST, instance=obj)` without
  restricting which fields can change is particularly dangerous for update endpoints
- **Django admin exposure**: admin panel at the default `/admin/` URL with no IP
  allowlist, no MFA, and no custom URL slug; `ModelAdmin.list_display` with callables or
  related model accessors hitting the DB once per row (N+1 on every admin list page);
  `raw_id_fields` or `autocomplete_fields` returning objects owned by other users
- **URL parameter injection**: `request.GET.get('order')` passed directly to
  `.order_by()` — attacker names any column, enabling information disclosure via error
  messages or query timing differences; `request.GET` values interpolated into queryset
  filters or template context without sanitization
- **Session security**: session fixation — `request.session.cycle_key()` not called after
  successful login, allowing a pre-login session ID set by an attacker to be reused
  post-login; Django sessions pickled by default — a compromised session store combined
  with a known `SECRET_KEY` gives RCE via pickle deserialization on session load
- **Celery / async task security**: task `kwargs` containing PII or credentials logged by
  Celery workers and visible in log aggregation tools; task results stored in Redis or DB
  without TTL accumulate indefinitely and may contain sensitive data; no rate limiting on
  task dispatch — a single user action triggers unbounded task fan-out; task arguments
  visible in Flower, Celery Beat logs, or monitoring UIs without access control

### Serverless / edge function lenses

- **Cold-start state assumptions**: module-level globals may persist across warm invocations
  of the same instance (shared state between unrelated requests) or be absent on a cold
  start; never treat global variables as reliably fresh or reliably persistent — both
  assumptions will be wrong
- **Execution time and memory limits**: long-running operations (report generation, large
  file processing, DB migrations) will be killed mid-flight by the platform with no
  cleanup; partial writes, dangling transactions, and inconsistent state result; move
  long work to a queue or background job
- **Stateless filesystem**: writes to `/tmp` on Lambda are instance-local and lost on the
  next cold start; Cloudflare Workers have no filesystem; Vercel Edge has no filesystem;
  any code that writes temp files and reads them back across invocations will silently
  break in production
- **Environment variables missing in edge runtime**: not all variables in `process.env`
  are available in the Edge runtime (Next.js middleware, Cloudflare Workers) — a secret
  may silently be `undefined` with no error thrown; validate required env vars at startup
- **CORS headers on function responses**: missing `Access-Control-Allow-Origin` on
  cross-origin endpoints; wildcard CORS (`*`) on an endpoint that sends `credentials:
  'include'` (browsers block this combination); `OPTIONS` preflight not handled — browsers
  reject the actual request before it fires
- **Fan-out cost bomb**: a handler that triggers N downstream function calls per invocation
  with no cap; one spammy event or a misconfigured trigger produces thousands of billable
  invocations and downstream API calls in seconds
- **No timeout on external calls**: DB queries, HTTP calls, and third-party API calls
  inside a function with no timeout set; the function hangs until the platform kills it;
  retries amplify the problem; always set an explicit timeout shorter than the function's
  execution limit
- **Vercel-specific**: `vercel.json` rewrites that proxy internal services without adding
  an auth header; `VERCEL_ENV` used as a security gate (`if (env === 'production') checkAuth()`)
  — preview deployments bypass the check; never use deployment environment as an auth
  substitute
- **Cloudflare Workers-specific**: secrets declared as `vars` in `wrangler.toml` are
  plaintext in the bundle — use `[secrets]` instead; KV store keys that are predictable
  allow enumeration; Durable Objects have shared state across concurrent requests and
  require explicit locking for consistency
- **AWS Lambda-specific**: Lambda not placed in a VPC when it needs to reach private
  resources (RDS, ElastiCache, internal services); Lambda in a VPC without a NAT gateway
  or VPC endpoint silently loses internet access; no reserved concurrency configured — one
  high-traffic function exhausts the account-level concurrency limit and starves all other
  functions; Lambda function URLs with `AuthType: NONE` are publicly callable with no auth
- **AWS API Gateway**: no request body validation schema (malformed payloads reach the
  handler and cause unhandled errors); no request or response size limits; throttling not
  configured at the route level; auth model choice wrong for the threat model (API key on
  a user-facing endpoint, unauthenticated on an internal endpoint)
- **Dependency validation at startup**: DB connections and secret fetches at module level
  (outside the handler function) run on cold start; if a required secret or connection is
  unavailable the function silently returns 500 with no actionable error; validate that
  all required dependencies are reachable before the handler accepts its first request

### Supabase / PostgREST lenses

- **Security & authorization**: RLS `USING` vs `WITH CHECK` asymmetries (a row readable ≠
  row writable — check both); column-level GRANTs missing; `SECURITY DEFINER` functions
  without explicit `search_path`; JWT claim trust (which claims does your RLS actually verify
  and where could they be spoofed?); signed URL leakage; role/tier escalation paths;
  multi-tenant row isolation — can user A ever see user B's rows?
- **Attack vectors / bypasses**: UPDATE-defeats-INSERT-check (INSERT policy blocks a row but
  UPDATE policy allows transforming an existing row into that state); cascade-vs-immutability
  collisions (FK cascade deletes rows the policy was supposed to protect); RLS-vs-RPC duality
  (a `SECURITY DEFINER` function runs as the defining role, bypassing the caller's RLS
  entirely — is that intentional?); clone/table-inheritance bypasses; side channels (timing,
  error message differences, behavioral differences that reveal row existence); audit-bypass
  via column un-set instead of hard delete
- **Concurrency & races (database)**: TOCTOU — check then act with no lock; transaction
  isolation level too low for the operation; missing `SELECT FOR UPDATE` where needed;
  idempotency on retries; lost updates (last-write-wins when it shouldn't); double-fire on
  triggers; trigger on wrong event (AFTER vs BEFORE, row vs statement)
- **Data integrity**: missing CHECK constraints, missing FK, missing UNIQUE, NOT NULL gaps
  where null would violate a business rule, denormalization drift (cached column disagrees
  with source), orphan rows when parent is deleted, soft-delete invariants not enforced at
  DB level
- **Performance (database)**: N+1 queries in RPC or edge function; missing indexes on FK,
  filter, and sort columns; oversized payloads with no `LIMIT`; function volatility wrong
  (`VOLATILE` when `STABLE` is safe); sequential scans on hot paths; redundant `SELECT`s;
  statement-level trigger where row-level is needed (or vice versa); lock contention
- **Migration safety**: DDL that takes a lock blocking writes on large tables; `NOT VALID`
  needed for constraint backfills; rollback path for each migration; data backfills that can
  fail mid-flight leaving partial state; ordering of dependent migrations; can the migration
  be re-run safely?
- **API & contract (Supabase)**: breaking response shape changes, edge function CORS/auth
  headers, request size limits, RPC signatures that have drifted from generated TypeScript
  types
- **Realtime channel auth**: Supabase Realtime subscriptions require channel-level
  authorization separate from Postgres RLS; RLS policies on the table do not automatically
  protect realtime event streams; a client can subscribe to a table's changes and receive
  rows that a direct query would deny; verify channel filters and auth checks in Realtime
  subscription handlers
- **Storage policies**: Supabase Storage has its own policy system independent of Postgres
  RLS; objects in a public bucket are accessible at a predictable URL regardless of the
  user's auth state; signed URLs generated with no expiry or a very long expiry (default
  can be up to 1 year) provide permanent access after the sharing context expires; Storage
  policies are often left at permissive defaults
- **Auth configuration**: OAuth redirect URIs not locked down in the Supabase dashboard —
  any redirect target accepted (open redirect); email confirmation disabled, allowing
  unverified addresses to access protected data immediately; magic link expiry set too long;
  PKCE flow not enforced for OAuth (auth code interception attack possible without it)
- **pg_net / pg_cron attack surface**: `pg_net` (HTTP requests from inside Postgres)
  available to non-superuser roles enables SSRF from the database tier to internal
  services or cloud metadata endpoints; `pg_cron` jobs executing SQL as a privileged role
  on a schedule — is the job SQL static or influenced by table data an attacker can write?
  both extensions are enabled by default in many Supabase projects

### Firebase / Firestore lenses

- **Security rules too permissive**: `allow read, write: if true` or `if request.auth !=
  null` without document ownership checks — any authenticated user can read or overwrite
  any other user's documents; rules must verify `request.auth.uid == resource.data.userId`
  or equivalent for every sensitive collection
- **Rules pass emulator but fail in production**: the Firebase emulator does not enforce
  all production behaviors and does not catch all rule logic errors; always test rules
  against realistic data shapes and run `firebase emulators:exec` with a test suite, not
  just interactive testing
- **Admin SDK bypasses rules entirely**: Cloud Functions and server code using the Admin
  SDK skip Firestore security rules; if a Cloud Function writes user-controlled data back
  to Firestore without its own validation, rules provide no protection for that write path
- **API key exposed in client bundle**: Firebase config (`apiKey`, `projectId`,
  `storageBucket`) is intentionally shipped to the browser — this is by design, not a
  secret — but the entire security model then depends on rules being correct; a permissive
  rule plus an exposed key equals full database access for anyone
- **Cloud Functions `onRequest` publicly callable**: HTTP-triggered Cloud Functions have
  no built-in authentication; any caller on the internet can invoke them; must check
  `context.auth` on callable functions or verify an ID token manually on HTTP functions
- **`onWrite` / `onUpdate` trigger loops**: a Cloud Function that writes to the same
  document it was triggered by will fire itself again; Firestore does not prevent this;
  always check that the new write actually changes data before writing, or use a separate
  `processing` flag
- **Firebase Storage rules separate from Firestore rules**: setting Firestore rules does
  not affect Storage; Storage rules default to deny-all after the free-tier default
  expires, but explicitly written rules may be too broad; check for public read on buckets
  containing PII or user-uploaded files
- **Real-time listeners not unsubscribed**: `onSnapshot` listeners not cleaned up on
  component unmount accumulate over navigation, consume quota, and can deliver data to
  components after the user logs out; always call the unsubscribe function in cleanup
- **Unbounded queries**: Firestore queries on client-readable collections without `.limit()`;
  a caller can fetch an entire large collection in one request with no server-side
  enforcement of result size; combined with permissive rules this is both a data
  exfiltration vector and a cost bomb
- **Firebase Authentication token lifecycle**: custom claims set via
  `admin.auth().setCustomUserClaims()` do not take effect until the client forces a token
  refresh — code that checks claims immediately after setting them sees stale values;
  `verifyIdToken()` without `{ checkRevoked: true }` accepts tokens belonging to
  disabled or deleted accounts
- **Data validation in security rules**: Firestore rules can and should validate the shape
  and types of incoming writes (`request.resource.data.keys().hasOnly([...])`,
  `request.resource.data.score is int`); missing data validation in rules allows malformed
  or oversized documents to be written that break client rendering or violate business
  invariants downstream
- **Firebase Hosting rewrites**: `firebase.json` rewrites exposing Cloud Functions at
  paths under the Hosting domain without intending to; `cleanUrls: true` and
  `trailingSlash` misconfigurations causing unexpected routing behavior or unintentionally
  exposing function endpoints at predictable URLs

### PostgreSQL / SQL lenses (standalone, non-Supabase)

- **Authorization**: which roles can call this function or access this table? is `SECURITY
  DEFINER` used and is `search_path` locked? are column-level permissions correct?
- **SQL injection**: dynamic SQL built with string concatenation or `format()` — are all
  user-supplied values parameterized? `EXECUTE` with `USING` vs. string interpolation
- **Query correctness**: plan stability under data growth, `EXPLAIN` reviewed for sequential
  scans, `NULL` semantics in `WHERE` / `JOIN` conditions, aggregate edge cases (empty set,
  single row)
- **Transaction boundaries**: is this query inside the right transaction boundary? autocommit
  assumptions?
- **Row-level security**: Postgres supports RLS independently of Supabase; tables
  containing multi-tenant or user-scoped data should have RLS enabled with correct
  policies; `ALTER TABLE t ENABLE ROW LEVEL SECURITY` with no policies attached defaults
  to deny-all for non-superusers — verify that is intentional and not an accident
- **Connection security**: `pg_hba.conf` with `trust` authentication on local or network
  connections (any OS user connects as any Postgres role without a password); SSL not
  required for remote connections (`sslmode=disable` accepted); `listen_addresses = '*'`
  combined with a permissive `pg_hba.conf` exposes the DB to the network
- **Privilege escalation paths**: `GRANT` chains that allow an unprivileged application
  role to reach superuser-level operations; `COPY TO/FROM PROGRAM` available to a role
  that processes user-supplied input (OS command execution); `CREATE EXTENSION` granted to
  a non-superuser who can then load dangerous extensions (e.g. `plpythonu`)
- **Audit logging**: `log_statement` and `log_min_duration_statement` not configured (no
  visibility into slow or suspicious queries in production); connection attempt logging
  disabled; `pgaudit` extension not installed for compliance-grade audit trails
- **Index correctness**: partial index predicate does not match the actual query predicate
  — index exists but is never used; expression index on a mutable or volatile expression;
  missing indexes on FK columns used in joins causing full sequential scans; covering
  index opportunities missed on hot read paths

### GraphQL lenses

- **Introspection enabled in production**: exposes the full schema — every type, field,
  argument, and relationship — to any unauthenticated caller; attackers use it to map the
  entire API surface before probing; disable or restrict introspection in production
- **No query depth limit**: `{ user { friends { friends { friends { ... } } } } }` is
  valid GraphQL; without a max depth, a single query generates exponential resolver calls
  and DB hits; set a depth limit (typically 5–7 for most schemas)
- **No query complexity limit**: depth limits alone are not enough — a wide query (100
  fields, each resolving 100 items) has low depth but high cost; assign a complexity score
  per field and reject queries that exceed a budget
- **Field-level authorization missing**: the entry-point resolver checks auth, but a
  nested field (e.g., `user.paymentMethods`, `order.internalNotes`) has no authorization
  check of its own; an attacker constructs a query that reaches the sensitive field through
  a permitted entry point
- **N+1 from resolvers**: each resolver fires independently; a list of 100 users each
  resolving a `posts` field makes 100 DB calls; use DataLoader or query batching to
  coalesce resolver calls — without it the endpoint is a denial-of-service vector
- **Mutation authorization separate from query**: being able to `query { user(id: X) }`
  does not mean the caller can `mutation { updateUser(id: X, ...) }`; check authorization
  independently on every mutation, not just on read operations
- **Batched query abuse**: if the server accepts an array of operations in one request,
  rate limits counted per-request are trivially bypassed; either disable batching or apply
  rate limits per operation within a batch
- **Error messages leaking internals**: default GraphQL error responses include resolver
  stack traces, SQL query text, internal field names, and file paths; production servers
  must map errors to safe messages and log details server-side only
- **Subscription authorization**: GraphQL subscriptions run over a persistent WebSocket;
  auth checked on the HTTP upgrade request but not validated on each subscription event;
  subscription filters enforced client-side only — a subscriber receiving all events and
  filtering locally sees all events before filtering; server must scope each subscription
  to the authenticated user
- **File upload security**: GraphQL multipart upload (`graphql-multipart-request-spec`)
  with no file size limit, no content-type or extension validation, and no path traversal
  check on the storage destination — same risks as any file upload endpoint but less
  visible because it's handled inside the GraphQL layer
- **Persisted queries not enforced in production**: server accepts arbitrary ad-hoc
  queries rather than only pre-registered persisted query IDs; persisted queries eliminate
  the depth/complexity/introspection attack surface entirely because only pre-approved
  queries are accepted; ad-hoc queries should be disabled in production if the client only
  ever needs a known set of operations
- **Federation / schema stitching boundary**: in a federated setup (Apollo Federation,
  GraphQL Mesh), each subgraph must enforce authorization independently; if only the
  gateway checks auth and a subgraph is directly reachable (misconfigured network, exposed
  internal port), all auth is bypassed entirely

### Webhook lenses

- **Missing signature verification**: most providers (Stripe, GitHub, Twilio, Shopify,
  Discord) include an HMAC signature header; if it is not verified, any caller can POST
  fake events to the endpoint and trigger your business logic
- **Replay attacks**: a captured valid webhook request can be replayed later; the provider
  typically includes a timestamp in the signed payload (Stripe does); reject events where
  the timestamp is older than ~5 minutes
- **Processing before acknowledging**: the event is processed before returning a 200;
  if processing takes too long, the provider times out and retries — the event runs twice;
  respond 200 immediately, then process the event asynchronously
- **No idempotency**: providers retry on timeout or 5xx; the same event can be delivered
  more than once; use the event ID as an idempotency key and check it before processing
- **Event type not validated from verified payload**: checking `req.body.type` before
  verifying the signature means an attacker can POST `{ "type": "payment.succeeded" }` and
  trigger the success handler; always derive the event type from the verified payload
- **Returning the wrong status on unprocessable events**: returning 5xx on a malformed
  event causes the provider to retry indefinitely; returning 4xx tells the provider to
  stop; distinguish between "I failed to process this" (5xx, retry) and "this event is not
  for me" (2xx, discard) and "this event is invalid" (4xx, stop retrying)
- **SSRF via user-registered webhook URLs**: if the application allows users to register
  their own callback URLs, an attacker registers `http://169.254.169.254/latest/meta-data/`
  (AWS IMDS), internal service hostnames, or `file://` URIs; validate registered URLs
  against a blocklist of RFC1918, link-local, and loopback ranges, and restrict to
  `https://` scheme only
- **Webhook secret rotation**: no mechanism to rotate the HMAC signing secret without
  downtime; secret hardcoded in an environment variable rather than a secrets manager;
  no grace period management — old and new secrets must both be accepted during a rotation
  window, then the old one revoked
- **Delivery failure visibility**: no alerting when webhook delivery fails repeatedly;
  missed events go undetected until a user reports a data inconsistency; no dead-letter
  queue, no retry dashboard, no monitoring on the endpoint's error rate

### Stripe / payment integration lenses

- **Amount calculated on the client**: the server receives a price, quantity, or total
  from the client and trusts it; a caller can POST any amount; the server must calculate
  or verify the charge amount from its own data (product catalog, order record), never from
  a client-supplied value
- **Webhook signature not verified**: use `stripe.webhooks.constructEvent()` — not manual
  HMAC comparison or checking `req.body.type` before verification; see Webhook lenses
- **Subscription status checked client-side**: `user.subscription === 'active'` checked
  in client code or from a client-readable field; the authoritative check must be
  server-side against Stripe's API or a server-owned field synced via webhook
- **No idempotency key on charge creation**: duplicate network requests or user double-
  clicks create duplicate charges; pass a unique `idempotencyKey` on every
  `paymentIntents.create` and `charges.create` call
- **Test mode keys in production**: `sk_test_` keys process no real money; if a test key
  reaches a production environment, payments silently fail or appear to succeed without
  charging anyone
- **PCI scope expansion**: logging card numbers or CVVs anywhere; passing raw card data
  through your server when using Stripe Elements (which is designed to keep card data off
  your server and reduce PCI scope); storing card details outside of Stripe's vault
- **Incomplete webhook event handling**: acting on `payment_intent.succeeded` but not
  handling `payment_intent.payment_failed`, disputes, refunds, and subscription
  cancellations — orders get stuck in wrong states silently; map every event type your
  integration depends on
- **`livemode` not checked**: Stripe test events can be sent to production webhook
  endpoints; always verify `event.livemode` matches the expected environment before
  fulfilling orders or granting access
- **Free trial and coupon abuse**: trial eligibility checked by email only — create a new
  address, get another trial; coupon codes applied without validating the coupon is still
  active, not past its `redeem_by` date, not past its `max_redemptions` limit, and not
  restricted to specific products or customers
- **Currency and decimal handling**: Stripe amounts are in the smallest currency unit
  (cents for USD, pence for GBP) but whole units for zero-decimal currencies (JPY, KRW);
  mixing up the multiplier — `amount: 1000` means $10.00 USD but ¥1000 JPY — causes
  order-of-magnitude errors in charge amounts; always document and assert the currency
  unit alongside every amount field
- **Metered billing atomicity**: `subscriptionItems.createUsageRecord()` failures that are
  silently swallowed leave billing state inconsistent; usage records reported for the wrong
  subscription item ID are ignored without an error; no reconciliation between what your
  system recorded as usage and what Stripe actually billed
- **Checkout Session expiry**: Sessions expire after 24 hours; code that attempts to
  retrieve or complete an expired session receives a `resource_missing` error; no graceful
  handling (redirect back to cart, re-create session) leaves the user stuck at a dead URL

### Shell / bash script lenses

- **Shell hygiene**: `set -euo pipefail` absent or incomplete; unquoted variable expansions
  (word splitting and glob expansion on `$var` and `"$@"`); arrays used where they should be
  vs. space-split strings; `[[ ]]` vs `[ ]` correctness; `local` missing in functions
- **Injection & traversal**: unvalidated input used in command strings; `eval` on
  user-controlled data; PATH not locked down in scripts run as root or from cron; `..` in
  file paths accepted from input; heredoc content with user data injected
- **Temp files**: created with `mktemp`, not predictable names in `/tmp`; `trap EXIT`
  cleans up; world-readable permissions on files containing sensitive data
- **Concurrency (scripts)**: no `flock` on shared resource writes; PID files checked and
  written non-atomically (two instances start simultaneously); signal handlers call
  non-async-signal-safe functions
- **Exit code contract**: every called subprocess's exit code checked; `VAR=$(cmd)` failure
  silently makes `VAR` empty — checked after; `||` / `&&` chains that hide failures
- **Cron / scheduled context**: PATH may be minimal; environment variables may differ from
  interactive shell; no output destination for errors (stderr goes nowhere)
- **CLI UX** (if this script is user-facing): `--help` present; `--dry-run` available for
  destructive scripts; progress output for long operations; SIGINT handled cleanly; output
  machine-parseable when piped
- **Secrets in debug output**: `set -x` enabled in a script that handles credentials or
  tokens — logs every command with all expanded variable values, including secrets, to
  stdout/stderr which is captured by CI logs, systemd journal, and monitoring systems;
  credentials echoed in success or error messages
- **Network operations**: `curl` or `wget` without `--fail` or `--fail-with-body` — HTTP
  4xx/5xx responses exit with code 0 and an empty or error body silently processed as
  success; `-k`/`--insecure` disabling TLS certificate verification; fetching and piping
  directly to `bash` (`curl https://... | bash`) without verifying a checksum or
  signature first
- **Symlink attacks**: writing to a file path without checking if it is a symlink first;
  an attacker with local write access creates a symlink from the expected temp path to a
  sensitive system file (`/etc/passwd`, a config file), and the script overwrites it;
  use `set -o noclobber`, `O_NOFOLLOW`-equivalent checks, or `mktemp` for all temp paths

### ETL / data pipeline lenses

- **Idempotency**: can the pipeline be re-run after a failure without double-loading,
  duplicating records, or corrupting state? is there a natural key or dedup strategy?
- **Watermarking / incremental correctness**: can records be skipped or double-loaded when
  the source changes during a run? is the high-water mark written atomically with the data?
- **Checkpoint atomicity**: if the job crashes at 80%, does it resume from the right offset,
  or does it restart from zero and double-load the first 80%? is the checkpoint file written
  atomically (write-then-rename) or in-place?
- **Dead-letter handling**: where do rejected or unparseable records go? are they observable?
  is there a threshold beyond which the job fails rather than silently dropping rows?
- **Schema evolution**: what happens when the source adds, removes, or renames a column?
  does the pipeline fail hard, silently drop the new column, or handle it gracefully?
- **Row-count / hash reconciliation**: is there a check that source row count equals
  destination row count after load? is there a hash or checksum check?
- **Data type coercion**: silent truncation (`BIGINT` → `INT`), float precision loss,
  string-to-date parsing with wrong locale or format, null vs. empty string conflation
- **Large dataset handling**: streaming vs. buffering — does the pipeline load the full
  dataset into memory? chunking strategy? disk exhaustion on temp output?
- **Rollback**: if the load fails mid-flight, what state is the destination in? is there
  a rollback procedure, or do you need to manually clean up?
- **Source credential security**: credentials for source systems (DB connection strings,
  API keys for data providers) hardcoded in pipeline config, DAG definitions, or
  `dbt profiles.yml` committed to git; no rotation mechanism for long-lived pipeline
  credentials; service accounts with read access to production data used by dev/staging
  pipelines
- **PII in pipeline metadata**: raw PII appearing in error messages, dead-letter records,
  Airflow task instance logs, or monitoring dashboards; pipeline operators can read PII
  via the monitoring UI without being authorized to access production data; PII should be
  masked or tokenized in all metadata and observability outputs
- **Cross-environment data leakage**: pipeline configured to read from production but
  write to staging, or vice versa; environment-specific connection config not validated
  at startup; accidental write of production PII to a staging database with different (or
  absent) access controls
- **Out-of-order record handling**: pipeline assumes records arrive in source order;
  late-arriving or out-of-order events cause incorrect aggregations, window computations,
  or state transitions; no out-of-order tolerance window or late-event handling strategy
  defined
- **Secrets in orchestration tools**: Airflow `Connection` objects storing plaintext
  passwords exportable via the Airflow REST API or visible in the UI to any DAG author;
  Prefect blocks or Dagster resources not using the secrets manager integration; pipeline
  run parameters containing credentials logged by the orchestrator

### Discord / Slack / Telegram bot lenses

- **Bot token in source or git history**: the token grants full bot access; anyone with
  it can read messages, post as the bot, and modify server settings; must live in
  environment variables only — never in source, never in logs, never in error messages
- **No webhook origin verification**: Slack and Discord sign webhook payloads with an HMAC
  signature; if the signature is not verified, any caller can POST fake events to your
  endpoint and trigger commands; Telegram uses a secret token in the header — verify it
- **Command injection via user input**: the bot receives a message and passes it
  unsanitized to a shell command, SQL query, template string, or `eval()`; treat all
  content from users, channel names, and usernames as untrusted input
- **Privilege escalation via role ID**: checking `member.roles.has(ADMIN_ROLE_ID)` where
  `ADMIN_ROLE_ID` is hardcoded; role IDs are server-specific and can be reassigned; a
  different role that happens to share an ID (e.g. after server migration) gets elevated
  access unintentionally
- **Rate limit handling absent**: bot does not back off on 429 responses from the platform
  API; gets globally rate limited or temporarily banned; implement exponential backoff and
  respect `Retry-After` headers
- **Storing user IDs as authentication tokens**: Discord and Slack user IDs are public and
  visible to all server members; using a user ID to authorize an API call means any user
  who knows another user's ID can impersonate them in requests to your backend
- **DM vs channel context confusion**: bot responds to a DM with information scoped to a
  specific server (server config, other users' data) that the DM recipient should not
  see; always verify that the requesting context has access to the data being returned
- **Telegram-specific**: webhook endpoint not verifying the `X-Telegram-Bot-Api-Secret-
  Token` header — any caller can send fake updates; polling is safe for development but
  production webhooks must validate origin
- **Slash command interaction token reuse**: Discord interaction tokens are valid for 15
  minutes; if stored and replayed, or if the endpoint does not deduplicate on token, an
  attacker can re-trigger a command after the user acted; track used interaction IDs and
  reject duplicates
- **Bot OAuth scope over-granting**: bot invited with `Administrator` permission or broad
  scopes (`channels:history`, `files:read`, `users:read`) when only narrow permissions
  (e.g. `chat:write`) are needed; least-privilege applies to bot OAuth scopes — audit the
  permission manifest and request only what each feature actually uses
- **User-supplied file and URL handling**: bots that download and process files or URLs
  from users with no file type validation, no size limit, and no SSRF protection; polyglot
  files, zip bombs, and decompression bombs; SSRF via user-supplied URLs the bot fetches
  on behalf of the requester (validate scheme is `https://` and host is not RFC1918)

### Native app lenses (iOS, Android, desktop)

- **OS permission model**: does the app request only the permissions it needs? does it
  handle permission denial gracefully?
- **Credential and key storage**: secrets in source, hardcoded in binary, or stored in
  OS keychain / secure enclave? what happens if device is compromised?
- **IPC & inter-process auth**: if the app communicates via sockets, named pipes, or
  shared memory — who else can connect? is the channel authenticated?
- **Memory safety**: buffer overflows from untrusted input, use-after-free, uninitialized
  memory read; applies to C/C++/Rust unsafe blocks and any FFI boundary
- **Resource leaks**: file handles, sockets, database connections, and locks released on
  all code paths including error paths and cancellation
- **Concurrency**: mutex misuse (double-lock, priority inversion, lock inversion);
  `volatile` absent on shared memory; race on lazy initialization
- **Certificate pinning**: no SSL certificate pinning allows MITM attacks on
  rooted/jailbroken devices or on a compromised network; pinned certificate hashes or
  public keys not updated before certificate rotation causes a production outage for all
  installed versions
- **Screenshot and screen recording protection**: sensitive screens (auth codes, financial
  data, health records) not setting `FLAG_SECURE` on Android — content visible in the
  recent apps switcher and screenshotted by accessibility services; iOS equivalent
  (`allowScreenshots = false` or obscuring the window on `UIApplicationUserDidTakeScreenshotNotification`)
  absent
- **Clipboard data exposure**: sensitive values (passwords, tokens, account numbers)
  written to the system clipboard without clearing after a short timeout; clipboard
  content readable by all apps on Android < 10 and in some iOS accessibility contexts;
  password manager autofill writes to clipboard and leaves it there indefinitely
- **Jailbreak and root detection**: apps handling financial data, DRM-protected content,
  or protected health information not detecting rooted/jailbroken devices; at minimum,
  alert the user and disable high-risk features when root/jailbreak is detected
- **App signing and integrity**: APK or IPA signed with a debug keystore in production
  builds; no integrity attestation (Google Play Integrity API, Apple DeviceCheck) for
  apps that must verify they haven't been repackaged or tampered with (e.g. license
  enforcement, anti-cheat, financial apps)
- **Deep link validation**: Android `intent-filter` with `android:exported="true"` and no
  host or path restriction — any app can send an intent to this component with arbitrary
  data; iOS universal link `apple-app-site-association` file not served over HTTPS or not
  restrictive enough, allowing any path to be claimed

### Electron lenses

- **`nodeIntegration: true` in renderer**: any XSS in the renderer process has full
  Node.js access — filesystem, shell execution, network sockets; this is the single most
  critical Electron misconfiguration; `nodeIntegration` must be `false` for any window
  that loads remote or user-supplied content
- **`contextIsolation: false`**: exposes Node.js globals and `require` in the renderer's
  web context; use `contextBridge.exposeInMainWorld()` to expose only specific, validated
  functions to the renderer — never the raw Node API
- **Remote content in an unsandboxed renderer**: loading a third-party URL in a
  `BrowserWindow` without `sandbox: true` and a `partition`; a compromised page in the
  renderer can call preload APIs and escalate to main process privileges
- **`shell.openExternal()` with user-controlled URL**: opens the URL in the default
  browser or OS application handler; a `javascript:`, `file:`, or custom protocol URL can
  execute code or open local files; validate the protocol is `http:` or `https:` before
  calling
- **`ipcMain` handlers without input validation**: renderer sends an IPC message and the
  main process executes it without checking the sender or validating the payload; a
  compromised renderer (XSS, malicious content) gains main-process capabilities through
  every unguarded handler
- **Auto-updater without code signing**: update fetched over HTTP or from an unverified
  source; an attacker who can intercept the update or control the update server can push
  malicious code to all installed instances; Electron's built-in updater requires
  code-signed releases and HTTPS
- **`webContents.executeJavaScript()` with any dynamic string**: equivalent to `eval()`
  in the renderer with the caller's privileges; only ever pass hardcoded string literals —
  never user input, network data, or variables
- **Protocol handler registration**: `app.setAsDefaultProtocolClient('myapp')` registers
  the app to receive `myapp://` deep links from the browser; incoming URLs are passed by
  the OS as command-line arguments; validate and sanitize every parameter before use, and
  never pass them to `shell.exec()` or `ipcMain` handlers directly
- **Child window `webPreferences` inheritance**: windows opened via `window.open()` from
  a renderer inherit the parent's `webPreferences` (including `nodeIntegration`) unless
  `webContents.setWindowOpenHandler()` explicitly overrides them with safe defaults; a
  third-party page that opens a popup inherits the same Node.js access as the main window
- **`allowRunningInsecureContent`**: allows an HTTPS page to load HTTP subresources; if
  `nodeIntegration` is also enabled, a network MITM substituting a malicious HTTP resource
  is a remote code execution path; should always be `false`
- **Native Node module supply chain**: native `.node` addons loaded in Electron are
  compiled binaries; pre-built binaries downloaded from npm are not compiled from source
  and are not reproducible; a compromised addon publisher can push malicious native code
  that runs at OS level with no sandbox
- **Renderer process crash handling**: `webContents.on('render-process-gone')` not
  handled; the app continues presenting a frozen or blank UI after a renderer crash without
  telling the user or attempting recovery; the main process should detect the crash and
  either reload the window or show an error state

### AI agent lenses

- **Prompt injection**: user-supplied or tool-fetched content reaching the system prompt or
  being interpreted as instructions — direct injection via input, indirect injection via tool
  results containing `"Ignore previous instructions..."`, second-order injection (data fetched
  in turn N executes in turn N+1), agent-to-agent injection (subordinate agent's output piped
  unsanitized into parent context)
- **Tool call security**: arguments to tools derived from untrusted input — are they validated
  before execution? does a `run_shell` tool accept an LLM-generated string directly? are
  irreversible actions (send email, delete file, make payment, deploy) gated behind a
  human-in-the-loop checkpoint before execution?
- **Tool least-privilege**: agent granted write/delete/execute tools it only needs
  occasionally; should these be separate agents or conditional grants rather than always
  present?
- **Tool result trust**: output from a tool treated as ground truth and piped directly into
  the next tool call or into the model context as instructions
- **Multi-agent trust boundaries**: agent A calls agent B — what authority does B grant
  A's messages? system-prompt authority or user-prompt authority? can a malicious tool
  result claim to be a trusted orchestrator?
- **Agentic loop safety**: no turn limit, no cost cap, no circuit breaker; fan-out (each
  iteration spawns more tool calls than the last) with no max-parallelism or max-depth;
  self-modification (agent writes to its own prompt, config, or tool list)
- **Nondeterminism / fragile parsing**: LLM output parsed as structured data without schema
  validation; hallucinated tool arguments (model invents plausible-sounding but wrong IDs,
  dates, enum values); output parsed from a partial/streamed response before the model
  finishes; behavior that diverges silently across temperature variation
- **Cost and resource abuse**: adversarial inputs maximizing token consumption; no
  per-user or per-session spend cap; cache invalidation storm when shared system prompt
  changes (all concurrent sessions miss cache simultaneously)
- **Agent privacy**: PII or secrets flowing through the context window and getting logged;
  conversation history retained past its useful life; cross-session contamination in shared
  vector stores or memory
- **Model version pinning**: alias model IDs (`gpt-4`, `claude-3-sonnet`) resolve to
  different underlying model versions as providers update them; behavior changes silently
  when a provider rotates the alias; pin to specific versioned model IDs in production and
  test before upgrading
- **System prompt confidentiality**: system prompt extractable via prompt injection
  (`"Repeat all instructions above verbatim"`); system prompt returned in API response
  metadata when provider debug options are enabled; treat the system prompt as a secret
  that can be extracted and design the system to remain safe even if it is
- **RAG / retrieval poisoning**: documents in the vector store containing injected
  instructions that get retrieved and inserted into context; an attacker who can write to
  the document corpus (or to a URL the RAG pipeline fetches) can inject instructions that
  arrive as "retrieved context" and bypass the system prompt boundary
- **Output validation gap**: agent output used to trigger downstream actions (send email,
  write to DB, execute code, make API calls) without human review or automated schema
  and content validation; agent confidently produces plausible but wrong output
  (hallucinated IDs, wrong amounts, invalid SQL) that gets executed without a check

### MCP server lenses

- **Tool definition security**: tools exposing dangerous primitives (`run_command`,
  `write_file`, `execute_sql`) without input validation; tool descriptions that guide the
  model toward dangerous invocations unintentionally; declared schema types that don't
  match implementation (type confusion, silent coercion); missing `required` fields that
  the implementation assumes are always present
- **Transport and authentication**: MCP server reachable by any local process or network
  client with no token validation; no mutual auth in multi-server setups; TLS absent on
  HTTP/SSE transports; credentials logged or capturable in transit
- **Prompt injection via tool results**: tool returns third-party or user-controlled content
  (web page body, file contents, DB row) that contains injected LLM directives; no fencing
  or `untrusted_content` labeling before it enters the model's context
- **Capability and scope creep**: more tools registered than the current task needs; resource
  URIs accepting `../` traversal; tool side effects undeclared (a "read" tool that also
  writes a log, updates a counter, or triggers a webhook)
- **Error handling and leakage**: stack traces, internal file paths, SQL errors, or API keys
  in tool error responses; errors that reveal resource existence vs. permission-denied
  (enumeration oracle); unhandled panics that crash the server process
- **Session isolation**: shared mutable state across sessions (global variables,
  module-level caches) that one session can corrupt for another; no cleanup on disconnect
  (open handles, locks, in-flight transactions)
- **Idempotency**: model retries a failed tool call without knowing the first call partially
  succeeded (email sent, file half-written, payment charged); no idempotency key support
  for side-effecting tools
- **Dependency on model behavior**: server assumes well-formed arguments because "the schema
  enforces it" — models deviate; no defensive validation at the server boundary
- **Rate limiting on tool calls**: no per-session or per-user rate limit on tool
  invocations; a runaway agent loop or adversarial prompt makes thousands of tool calls in
  seconds, exhausting external API quotas, triggering billing surprises, or causing
  downstream service disruption
- **Tool schema versioning**: tool parameter names or types change (renamed field, changed
  type, added required parameter) without a versioning or deprecation mechanism; existing
  agent integrations break silently or send wrong arguments with no error surfaced to the
  operator
- **Tool description as attack surface**: tool descriptions are part of the prompt sent to
  the model and influence how it calls the tool; a compromised package update that alters
  a tool description can guide the model toward calling the tool with harmful arguments
  without the user or operator noticing; treat tool descriptions as trusted configuration,
  not user-editable data

### Infrastructure / config lenses

- **Secret sprawl**: secrets in environment variables that get logged, in config files
  committed to git, in build artifacts, in container images
- **Blast radius of misconfiguration**: what is the worst-case impact if this config value
  is wrong in production? is there a validation step before the config is applied?
- **Terraform / IaC**: resource recreation vs. update (destroys live data?), missing
  `prevent_destroy`, state drift between plan and apply, IAM over-permissioning
- **Container / image**: running as root when not needed, secrets baked into image layers,
  base image not pinned, no health check, ports exposed unnecessarily
- **Network security**: security groups or firewall rules with `0.0.0.0/0` inbound on
  sensitive ports (22 SSH, 3306 MySQL, 5432 Postgres, 6379 Redis, 27017 MongoDB); no
  egress filtering — any compromised workload can exfiltrate data or establish a C2
  callback; VPC peering with no traffic restriction between peers (full mesh access)
- **IAM / access control**: IAM policies with `Action: "*"` or `Resource: "*"`;
  service accounts with project-level or account-level permissions when resource-scoped
  permissions would suffice; long-lived access keys with no rotation policy and no
  last-used monitoring; MFA not enforced for console access or privilege-escalation API
  calls
- **Kubernetes security**: pods running as root (`runAsNonRoot` not set); `hostNetwork:
  true`, `hostPID: true`, or `privileged: true` granting host-level access; `hostPath`
  mounts exposing the host filesystem to container workloads; Kubernetes Secrets not
  encrypted at rest (etcd encryption not configured); RBAC with `cluster-admin` bound too
  broadly; no `NetworkPolicy` resources — any pod can reach any other pod on any port
- **Logging and monitoring**: no centralized log aggregation; logs stored only on the host
  they describe (lost on instance termination); CloudTrail / GCP Audit Logs / Azure
  Activity Log disabled or retention set too short; no alerting on privilege escalation
  events, new IAM policy attachments, or access from unexpected regions or IPs
- **CI/CD pipeline security**: secrets in CI environment variables printed in build logs
  when a step fails or when `set -x` is active; pipeline steps running with repo-wide
  write permissions instead of scoped tokens; GitHub Actions workflows triggered by
  `pull_request_target` from forked repos with `secrets` accessible — allows a fork's PR
  to exfiltrate repository secrets
- **Backup and recovery**: no automated backup policy for stateful resources (managed
  databases, object storage without versioning); backups never tested with a restore drill
  (backup exists but may not be restorable); single-region deployment with no cross-region
  replication or failover plan for data that must survive a regional outage

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
If "Start a new audit": use the Write tool to overwrite the existing artifact with a fresh header (follow the "artifact does not exist" path below — ask about subagents, then create). Do not continue until the new artifact exists on disk.
If "Continue from where I stopped": proceed as if Status were IN PROGRESS.

**If Status is `IN PROGRESS` (or "Continue from where I stopped" was chosen):** Note the current pass number and all rows with Status = Open in the findings table. Note the `**Subagents:**` field from the artifact header — this is the adversarial subagent setting for this audit. Do not ask the user about subagents again. Continue from where the last pass left off — re-walk every surface from scratch, but use prior finding numbers for known issues.

**If the artifact does not exist:** Before creating it, ask about subagent configuration:

<mandatory>Call AskUserQuestion with:
- Question: "Run an adversarial subagent in parallel with each pass? It launches in the background at the start of the walk — a second agent with no prior context reads the same diff, looking only for failure modes the structured walk missed. Results are collected at the end of the pass. Especially recommended on large or security-sensitive branches. Adds time to each pass."
- Options:
  - "Yes — run adversarial subagent in parallel"
  - "No — main walk only"
</mandatory>

Record the answer. Then create the artifact with the header below, setting `**Subagents:**` to `enabled` or `disabled` based on the answer. Write it to the computed artifact path using the Write tool. The Write tool creates parent directories automatically. Do not continue until the file exists on disk.

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
**Subagents:** enabled | disabled

## Branch summary
[1–3 sentences: what this branch does, what it changes, why it exists]

## Stack detected
[list stacks from Phase 0]

## Lenses applied
[list selected lenses from Phase 1]

## Surface map
[table from Phase 2]

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
- If N ≥ 2: you must have received a **"Continue to pass N"** response from an **AskUserQuestion tool call** in Phase 6 of the previous pass in this conversation session. Look back in the current conversation — find the AskUserQuestion call and the user's "Continue" response. If you cannot find it, **do not start the walk**. Instead, re-read the artifact, run Phase 6 (fix any open findings, increment the passes completed counter), and call the AskUserQuestion pass checkpoint now.

Exception: if the `## Pass N progress` section is present in the artifact with `— in progress` in the pass log (resumed session after compaction or restart), you may proceed without a "Continue" response — the user already authorized this pass in the previous session.

**Rationalizing is not allowed.** "The user probably wants me to continue" is not authorization. Only an explicit AskUserQuestion "Continue" response is.</mandatory>

<recovery>

**If this is a resumed session (after context compaction or restart):**
0. Determine the artifact path: run `git branch --show-current` to get the current branch name. If it returns empty (detached HEAD state): run `git branch` to list all local branches. Call AskUserQuestion — "The repo is in detached HEAD state — no branch is currently checked out. Which branch were you auditing?" — list each local branch as its own option (use Other to type a branch name manually). Use the confirmed branch name. Slugify the branch name (lowercase, replace non-alphanumeric characters with `-`, collapse consecutive hyphens to one, strip leading/trailing hyphens). If $ARGUMENTS is set (scoped audit), apply the same slugification to the scope path and append `--[path-slug]` to form `[branch-slug]--[path-slug].md`. Otherwise the path is `[branch-slug].md`. Read the artifact at `.vibe-check/vc-audit/[computed-path]` to restore full state.
1. Determine BASE_BRANCH using this priority order — stop at the first that succeeds:
   - **Audit artifact**: read `**Base branch:**` from the artifact header. Use that value.
   - **Roadmap**: use the Read tool to check `.vibe-check/vc-plan/roadmap.md`. If it exists and has a `**Base branch:**` line, use that value.
   - **Derive**: run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null`. If it returns a value, strip the `refs/remotes/origin/` prefix directly — do not use shell utilities. If it returns nothing: run `git remote set-head origin -a 2>/dev/null`, then re-run `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null`. If it now returns a value, strip the prefix. If still nothing: run `git for-each-ref --format='%(refname:short)' refs/heads/` and identify the default branch (priority: `main` > `master` > `develop`). Then call AskUserQuestion — "I derived `[branch]` as the base branch for this audit. Is that correct?" — Options: "Yes — use [branch]" / "No — use a different branch (Other)". Use the confirmed or entered value as BASE_BRANCH.
2. If the most recent pass entry in the pass log shows `— in progress`, that pass did not complete — most likely due to context compaction. Check the artifact for a `## Pass N progress` section immediately following that marker (N = the in-progress pass number). If found: read the `[x]`/`[ ]` markers — `[x]` surfaces were already walked and their findings are already written to the artifact; `[ ]` surfaces were not. Store the `[ ]` surfaces as REMAINING_SURFACES. Note whether `subagent:` shows `dispatched` or `pending`. If `## Pass N progress` is not found (compaction happened before the section was written): restart the pass from the beginning.
3. Derive the current pass number, all Open-status findings, and the clean pass count from the artifact. Do not rely on conversation memory. Scan the ID column of the findings table for the highest F-NNN number. Store this value as NEXT_F_NUM. All new findings in this pass must be numbered starting from NEXT_F_NUM + 1. Re-read the full surface map section from the artifact and store every surface listed. If resuming from a `## Pass N progress` section (step 2 above), only the `[ ]` surfaces (REMAINING_SURFACES) need to be walked this session — `[x]` surfaces are already complete.
4. Read the `**Subagents:**` field from the artifact header. Do not ask the user about subagents again — this setting was recorded when the audit was created.
5. Re-derive FILE_READ_MODE and UNTRACKED_FILES: run `git diff BASE_BRANCH...HEAD --shortstat`. If non-empty: normal diff mode. If empty: run `git status --porcelain`, filter out `.vibe-check/` and `.claude/` paths. If any M/A/R entries remain: working tree changes exist, proceed in normal diff mode. Store `??` entries (filtered by sensitive exclusions) as UNTRACKED_FILES. If both committed shortstat and filtered status are empty AND the plan stub at `.vibe-check/vc-plan/[branch-slug].md` contains a `## Chunk files` section: FILE_READ_MODE = true.

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
- [ ] [Surface name] — [file1.ts file2.ts ...]
- [ ] [Surface name] — [file3.ts]
```

For each surface, list the file paths associated with it from the surface map (space-separated after `—`). If FILE_READ_MODE is true, list the chunk file path instead. Set `subagent:` to `pending` if `**Subagents:** enabled` in the artifact header, otherwise `disabled`.

<mandatory>The `## Pass N progress` section is always at the END of the artifact, never embedded inside the `### Pass N — in progress` pass log entry. The pass log entry contains only the two-line block written above (header + `**Surface walk receipts:**`). Never add checklist lines or any other content to the pass log entry during Phase 4 — the checklist lives in `## Pass N progress`, receipts are added to the pass log via Step 4b.</mandatory>

**If this is a resumed pass** (REMAINING_SURFACES loaded from `## Pass N progress` in the recovery step): do not rewrite it. Use the existing section as-is.

**Dispatch the adversarial subagent** if `**Subagents:** enabled` AND the `subagent:` line in `## Pass N progress` shows `pending`: dispatch now using the Agent tool with `run_in_background: true`. Use the subagent prompt from the Adversarial pass section below, omitting the "do not repeat open findings" instruction — the subagent reads the full branch diff itself; deduplication happens at Phase 6 when results are collected. Immediately update the `subagent:` line in `## Pass N progress` to `dispatched`.

**Walk each surface one at a time.** For each `[ ]` surface in `## Pass N progress` (in order from top to bottom):

**Step 1 — Sensitive file check.** If the surface file(s) match any pattern in the Sensitive File Protection section, skip the diff and record a finding per the Sensitive File Protection rules. Use the Edit tool to mark the surface `[x]` in `## Pass N progress`. Move to the next surface.

**Step 2 — Load only this surface's scope:**

If FILE_READ_MODE is false:
- If this surface is marked `(untracked — Read tool)`: use the Read tool to read each file. Skip the diff — untracked files have no diff.
- Otherwise (tracked file — committed, staged, or unstaged):
```bash
git diff BASE_BRANCH -- [file paths for this surface]
```
Substitute BASE_BRANCH. For an initial commit session, substitute `4b825dc642cb6eb9a060e54bf8d69288fbee4904`. This captures committed changes AND any uncommitted staged/unstaged changes vs the base branch. If `$ARGUMENTS` was provided, verify the surface files fall within the requested scope — if a surface file is outside the requested scope, mark it `[x]` and skip it.

If FILE_READ_MODE is true: use the Read tool to read the chunk file for this surface. If the Read tool returns an error, stop and report: "Could not read `[filename]` — verify the file exists. If moved or renamed, update `## Chunk files` in the plan stub and re-run /vc-audit." If the file returns exactly 2000 lines, re-read with increasing offsets (2000, 4000, …) until a read returns fewer than 2000 lines. Concatenate all parts as the complete file content.

<gate>Do not walk this surface until you have its diff output or file content in context. Load only this surface — not the full branch diff.</gate>

**Step 3 — Walk all selected lenses** against this surface. Follow the walk rules below. Follow dependencies into other files using the Read tool as required by the threat model.

<mandatory>**Step 4 — After completing this surface, perform BOTH of the following writes before moving to the next surface:**

**Step 4a — Update the progress checklist.** Use the Edit tool to replace `- [ ] [Surface name]` with `- [x] [Surface name]` in `## Pass N progress`. Do not move to the next surface until this edit has succeeded. This is the resume record — skipping it makes compaction recovery impossible.

**Step 4b — Write this surface's receipt into the pass log.** Use the Edit tool with:
- `old_string`: `\n\n## Pass N progress` (the two newlines immediately before the `## Pass N progress` section header — substitute the actual pass number for N)
- `new_string`: the receipt entry followed by `\n\n## Pass N progress`:

```
- Surface: [name from surface map]
  Verdict: CLEAN | NEW FINDINGS (F-NNN)
  Evidence: file:line — [specific observation from the Read or diff just performed]

## Pass N progress
```

This inserts the receipt into the pass log just before the progress section. Each subsequent surface uses the same anchor — the `\n\n## Pass N progress` text is always present at the end of the new_string, so the anchor remains valid for the next surface.

Do NOT write `Verdict: CLEAN` with no `Evidence:` citation, and do NOT write `Evidence:` without a real `file:line` reference from a tool call you made in Step 2 of this surface. "CLEAN. No issues." is not a valid receipt. Do NOT defer receipt writing to Phase 5 — write it now while the evidence is in your context.</mandatory>

<walk-rules>

Walk every surface in the surface map against every selected lens. These rules apply to
every pass, every time. **If FILE_READ_MODE is true, substitute "the chunk file contents"
for all references to "the diff" or "the branch diff" in these rules** — the chunk files
are the audit surface, not a diff.

**Permitted tools during the walk:** Read (for following dependencies), Edit/Write (for writing findings to the artifact and updating `## Pass N progress`), AskUserQuestion (for user decisions), and Agent (for the adversarial subagent). The only Bash commands permitted are the `git diff` surface-scoping commands specified above, and `git ls-files` if needed to resolve gitignored exclusions. Do not invoke interpreters (node, python, ruby, php, etc.) or run ad-hoc shell scripts to process data — all analysis happens in Claude's reasoning, not in a shell.

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

**Coverage gate:** Before proceeding to Phase 5, read the artifact and verify two things:
1. Every surface in `## Pass N progress` is marked `[x]`. If any is still `[ ]`, walk it now (Steps 1–4).
2. The `### Pass N — in progress` block in the pass log has a receipt entry (with `Verdict:` and `Evidence: file:line`) for every surface. If any surface has `[x]` in the progress section but no receipt in the pass log, re-read that surface's file(s) and write the receipt now via Step 4b — do not write from memory.

Do not proceed to Phase 5 with any surface missing a receipt. An undocumented surface is not a clean surface.

</phase>

---

<phase id="5" name="report">

## Phase 5 — Report and update the artifact

After each pass, update the artifact in place. The artifact accumulates across passes —
do not create a new file per pass.

**First: remove the `## Pass N progress` section.** Use the Read tool to find the exact content of the section (from the `## Pass N progress` line through the last `- [x]` surface line). Use the Edit tool to replace that entire block with an empty string. Confirm it is gone before continuing — this section is transient walk-tracking state and must not persist in the completed pass record.

<mandatory>**Second: finalize the pass log header.** Use the Edit tool to replace `### Pass N — in progress` with `### Pass N — [today's date]`. The surface walk receipts are already written in the pass log from Phase 4 Step 4b — do NOT rewrite or reconstruct them. Do NOT add any new content between the updated header and the first receipt line. This is a one-line header edit only.</mandatory>

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

If the artifact header shows `**Subagents:** enabled`:

<mandatory>Collect the background subagent result dispatched at the start of Phase 4. The subagent ran in parallel while the main walk executed — its findings should now be available. If it has not yet completed, wait for it now.

The subagent prompt used was the one below (for reference — do not re-dispatch). Process the returned output: for each finding, check whether the same issue is already recorded as a row with Status = Open in the findings table. If a duplicate exists, skip it. Add any non-duplicate findings to the findings table using the same F-NNN numbering sequence.

The subagent prompt (for reference only — already dispatched):

**If FILE_READ_MODE is false** (normal diff-based audit): substitute BASE_BRANCH, artifact path, and scope paths into this prompt. If this is a scoped audit, read the `**Scope:**` field from the artifact header and append the scope path(s) as trailing arguments after the sensitive file exclusions in the git diff command (e.g. `-- ':!...' src/auth/`). If this is a full audit, omit the trailing path arguments entirely. Use `git diff [BASE_BRANCH]` (not `...HEAD`) to capture both committed and uncommitted tracked changes.

"Run this git command and read the full output:

git diff [BASE_BRANCH] -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!kubeconfig' ':!*.kubeconfig' ':!google-services.json' ':!GoogleService-Info.plist' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd' [scope paths if scoped audit]

Then use the Read tool to read the audit artifact at [artifact path].

Your task: find failure modes, bugs, and security issues the structured walk missed. Think like an attacker and a chaos engineer. No compliments — only problems.

Rules:
1. Before reporting any finding, quote the specific lines from the diff that motivate it. If you cannot quote specific lines, do not report it.
2. Do not repeat findings already listed as Open in the artifact — check that section before reporting.
3. Classify each finding as FIXABLE (you can state the fix direction) or INVESTIGATE (needs human judgment to resolve).

Output one finding per line in this format:
[FIXABLE|INVESTIGATE] | [critical|high|medium|low] | file:line — what the problem is; what it allows or causes; fix direction or what to investigate

If you find nothing new, output exactly: NO ADDITIONAL FINDINGS"

**If FILE_READ_MODE is true** (chunk branch — no diff): substitute the chunk file paths (from the plan stub's `## Chunk files` section) and artifact path into this prompt:

"Before reading any file, skip it if its filename or path matches any of these sensitive file patterns:
`.env`, `.env.*`, `.envrc`, `.envrc.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.pkcs8`,
`*.jks`, `*.keystore`, `*.ppk`, `id_rsa`, `id_ecdsa`, `id_ed25519`, `id_dsa`, `*.secret`,
`*.secrets`, `*.vault`, `*.enc`, `.netrc`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pypirc`,
`*credentials.json`, `*service-account*.json`, `*-key.json`, `*.tfstate`, `*.tfstate.backup`,
`*.tfvars`, `*.tfvars.json`, `google-services.json`, `GoogleService-Info.plist`, `kubeconfig`,
`*.kubeconfig`, `docker-compose.override.yml`, `docker-compose.*.yml`, `local_settings.py`,
`settings.py`, `application_default_credentials.json`, `.htpasswd`, `htpasswd`, `database.yml`,
`wrangler.toml`, `fly.toml`, `*secrets*`, `*password*`, `*passwd*`

Use the Read tool to read each of the following files (skipping any that match the patterns above):
[list each chunk file path on its own line]

Then use the Read tool to read the audit artifact at [artifact path].

Your task: find failure modes, bugs, and security issues in these files that the structured walk missed. Think like an attacker and a chaos engineer. No compliments — only problems.

Rules:
1. Before reporting any finding, quote the specific lines from the file that motivate it. If you cannot quote specific lines, do not report it.
2. Do not repeat findings already listed as Open in the artifact — check that section before reporting.
3. Classify each finding as FIXABLE (you can state the fix direction) or INVESTIGATE (needs human judgment to resolve).

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
- If the subagent is **unavailable or errors**: append to the pass log: `Adversarial pass: unavailable.` Continue to Phase 6.

</phase>

---

<phase id="6" name="fix-and-loop">

## Phase 6 — Fix and loop

**Auto-fix pass (before decisions):** Use the Read tool to read the current findings table. Scan for every Open row that qualifies for auto-fix:
- Severity is `high` or `critical` — always qualifies, regardless of confidence
- Severity is `low` or `medium` AND confidence is `7/10` or higher (parse the `(N/10)` value from the Severity cell)

For each qualifying finding, in F-NNN order:
1. Attempt to apply the fix directly to the source file using the Edit tool. The fix direction is stated in the finding description. Reference the finding number in an inline code comment if appropriate (e.g., `// fix [F-003]: added null check`).
2. After the Edit, use the Read tool to verify the fix appears in the source file.
3. **If confirmed:** immediately Edit the finding's Status cell from `Open` to `Resolved (pass N) [auto-fixed]`. Do not ask the user.
4. **If the Edit fails or the correct change cannot be determined from the description:** leave Status as `Open`. The finding will be handled in the decision flow below.

After completing the auto-fix pass, tell the user: "Auto-fixed [N] findings: [F-NNN, F-NNN, ...]" (omit this line entirely if N = 0).

After the pass report:
1. For each **Acting on** item (`F-NNN`) that was not already resolved by the auto-fix pass above: apply the fix directly to the source file using the Edit tool. Reference the finding number in an inline code comment if appropriate (e.g., `// fix [F-003]: added null check`). The finding number will be included in the commit message by vc-ship when the branch ships. After the Edit, use the Read tool to verify the fix appears in the source file. If it does not, re-attempt once. If it still fails, tell the user: "Could not apply the fix for [F-NNN] — please apply this change manually: [exact old and new text]." Once the fix is confirmed applied, immediately Edit the finding's Status cell in the findings table from `Open` to `Resolved (pass N)`. Do not proceed to the next Acting on item until the Status cell is updated. If the finding fix cannot be confirmed, leave Status as Open — it will reappear as open on the next pass.
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
3. Once fixes are applied and decisions recorded, increment `**Passes completed:**` in
   the artifact header, then run the **pass checkpoint**.

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

   Re-read the artifact using the Read tool. Count findings table rows by Status using the same breakdown above. Use these counts — do not use memory or session totals.

   **Convergence check — count rows mechanically, do not reason from the pass log narrative:**

   1. Count every findings table row where the Pass column contains `pass N` (current pass number). Call this CURRENT_PASS_FINDINGS. Include ALL Status values — Resolved, Fixed, Dismissed, Deferred, and Open all count. A finding opened and immediately fixed in pass N still counts.
   2. Count every findings table row where the Pass column contains `pass N-1` (previous pass). Call this PREV_PASS_FINDINGS. Same rule — all Status values count.
   3. Count findings table rows where Status = `Open`. Call this OPEN_COUNT.

   CONVERGENCE_CONDITIONS_MET = true ONLY if: CURRENT_PASS_FINDINGS = 0 AND PREV_PASS_FINDINGS = 0 AND OPEN_COUNT = 0. If N < 2 (fewer than two passes have run), CONVERGENCE_CONDITIONS_MET = false — convergence requires at least two passes.

   **Critical:** PREV_PASS_FINDINGS counts findings OPENED in pass N-1, regardless of their current Status. A finding opened in pass 1 and immediately fixed still counts toward pass 1's finding total. Example: if pass 1 opened 9 findings (all now Resolved), then after pass 2: PREV_PASS_FINDINGS = 9 → CONVERGENCE_CONDITIONS_MET = false, even if pass 2 is completely clean. In that case, pass 3 would be the earliest possible convergence opportunity (if both pass 2 and pass 3 open zero findings).

   Store CONVERGENCE_CONDITIONS_MET. Do not announce this determination — just store it.

   **If this is a scoped audit** (artifact path contains `--`) AND CONVERGENCE_CONDITIONS_MET is true: run `git diff BASE_BRANCH --name-only` to get the full tracked file list, and check `git status --porcelain` for any UNTRACKED_FILES (filtered). Combine both for the full branch file list. Glob `.vibe-check/vc-audit/[branch-slug]--*.md` to find all other scoped audit artifacts for this branch. Compute which files on this branch are not covered by any scoped audit. If unaudited files remain, set CONVERGENCE_CONDITIONS_MET = false and note the uncovered files.

   **Note for small branches:** On branches with fewer than five changed files, if CONVERGENCE_CONDITIONS_MET is true, verify the surface map has one entry per changed file and that each receipt entry cited actual line numbers. If coverage is superficial, set CONVERGENCE_CONDITIONS_MET = false.

   <mandatory>Your ONLY valid next action is to call AskUserQuestion with the pass checkpoint below. Do NOT:
   - Write any text output to the user about the pass results, findings, next steps, or options (e.g. "Pass 1 found 4 issues…", "Ready to run Pass 2…", "Next step:…")
   - Write anything to the artifact
   - Write a status like CONVERGED, DONE, STOPPED, or any terminal phrase to the artifact header or pass log
   - End your response
   - Take any other action
   until AskUserQuestion has been called and the user has responded. This applies regardless of pass outcome, finding count, or how trivial the findings were. There are no exceptions. The AskUserQuestion tool call is the only valid communication channel for the pass checkpoint.

   Call AskUserQuestion with the pass checkpoint. Use this exact format — plain text, no markdown:

   **Question text:**
   ```
   Pass [N] complete

   This pass: [N] fixed · [N] deferred · [N] dismissed · [N] new findings
   Still open: [N] findings
   [If CONVERGENCE_CONDITIONS_MET: add a blank line then "Two consecutive clean passes — no findings opened in either pass."]
   [If scoped audit with uncovered files: add "Uncovered files: [list]"]

   Artifact: .vibe-check/vc-audit/[branch-name].md
   ```

   **Options — always include these three:**
   - **Continue to pass [N+1]** — Run the next pass now
   - **Pause** — Stop here; resume later by running /vc-audit again
   - **Stop** — Done auditing; I will review and decide on open findings myself

   **Additional option — include only if CONVERGENCE_CONDITIONS_MET is true:**
   - **Declare convergence** — Mark this audit complete (two clean passes, nothing open)
   </mandatory>

   **If the user chooses Stop**: use the Read tool to read the entire artifact fresh. Write the artifact back using the Write tool with `**Status:** STOPPED` in the header and the findings table rows grouped under status section headers (see **Grouped findings format** below). After the Write, use the Read tool to verify `**Status:** STOPPED` appears. If it does not, re-attempt once. If it still fails, tell the user: "Could not update the artifact — please change the `**Status:**` line to `**Status:** STOPPED` manually." Then stop. A STOPPED audit will not auto-resume; the user must re-run /vc-audit to start a new session.
   **If the user chooses Pause**: stop immediately without modifying the artifact. Phase 3 detects the IN PROGRESS artifact on the next run and resumes from where this pass left off.
   **If the user chooses Continue**: start Phase 4 from the very beginning — the authorization gate, the pass-start marker, and the `## Pass N progress` section must all be executed before any surface walk begins. Do not jump directly into reading files or running bash commands. The required sequence is:
   1. Pass the Phase 4 authorization gate (the "Continue" response you just received satisfies it)
   2. Write `### Pass N — in progress` to the artifact pass log
   3. Append a fresh `## Pass N progress` section listing every surface as `[ ]`
   4. Then begin the surface walk, one surface at a time, checking off `[x]` after each one

   Do not skip surfaces because they were clean last pass. Do not skip steps 2 or 3 — without them, a compaction or interruption mid-pass leaves no record of what was completed.

   **If the user selects "Declare convergence"**: use the Read tool to read the entire artifact fresh. Count findings table rows by Status to get the final totals (Open, Resolved, Deferred, Dismissed). Write the artifact using the Write tool with:
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
