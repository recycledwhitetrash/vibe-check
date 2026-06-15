# /vc-bootstrap — Machine Setup

<!-- version: 2026-06-10 -->

Setup for the vibe-check suite. Configures git, installs and authenticates GitHub CLI,
installs gitleaks, and generates a security-baseline `.gitignore` for your project. Orients
you to the full skill suite and routes you to the right starting point. Run this in each
new project — machine-level steps (git config, GitHub CLI auth, gitleaks) skip automatically
if already done, but the `.gitignore` baseline and project routing are set up fresh each time.
Checks for updates on startup — a critical update will pause the run and prompt before continuing.

---

## Version check

Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/versions.json`. If the fetch fails or returns an error for any reason, skip this section entirely and proceed to Phase 0.

<output-handlers>

**Fetch succeeded — `vc-bootstrap` version matches `2026-06-10`**: proceed silently.

**Fetch succeeded — newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /vc-bootstrap is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue to Phase 0.
If Update now: follow the **Auto-update** steps below, then stop.

**Fetch succeeded — newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /vc-bootstrap that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed to Phase 0.

**Fetch succeeded — fetched version is older than `2026-06-10`**: proceed silently. (This can happen with CDN caching or a rollback — the local version is already newer.)

</output-handlers>

**Auto-update:**
1. Run `git --version` to check whether git is installed. If git is not installed, skip the auto-update entirely and proceed to Phase 0 — git will be installed there first.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-bootstrap.md`.
4. If both succeed: use the Write tool to write the fetched content to `[project-root]/.claude/commands/vc-bootstrap.md`. Tell the user "Updated to the latest version. Please re-run /vc-bootstrap." Do not continue.
5. If either fails: tell the user auto-update failed and to update manually at https://github.com/recycledwhitetrash/vibe-check. Do not continue.

---

<phase id="0" name="detect">

## Phase 0 — Detect

Run all checks up front before asking the user anything.

```bash
git --version
gh --version
gitleaks version
git config --global user.name
git config --global user.email
gh auth status
git rev-parse --show-toplevel 2>&1
```

<gate>Do not proceed until you have all seven outputs.</gate>

If `git rev-parse --show-toplevel` succeeded: use that path as PROJECT_ROOT for all file operations in this skill.
If it failed (git not installed or not in a git repo): use `.` as PROJECT_ROOT — files will be written relative to the current working directory.

Check whether `PROJECT_ROOT/.vibe-check/vc-bootstrap.md` exists using the Read tool.

Build a status table from the results and present it to the user:

| Item | Status |
|------|--------|
| git | ✓ installed / ✗ not found |
| git user.name | ✓ "Greg" / ✗ not set |
| git user.email | ✓ "greg@..." / ✗ not set |
| GitHub CLI | ✓ installed / ✗ not found |
| gh auth | ✓ authenticated as @username / ✗ not authenticated |
| gitleaks | ✓ installed / ✗ not found |

Note: `gh auth status` failing because `gh` is not installed is not a separate problem —
mark both gh and gh auth as not found in that case.

Note: if `git --version` failed, do not attempt to interpret the output of `git config --global user.name` or `git config --global user.email` — both will have errored for the same reason. Mark them as `— (git not installed)`, not as separate failures.

**Re-run detection:** If the bootstrap artifact exists with `**Status:** complete`, tell the
user this project was previously bootstrapped and show the prior configuration summary from
the artifact. Then continue through all phases — machine-level steps (git config, GitHub CLI
auth, gitleaks) skip if already done; project-level steps (`.gitignore`, orientation) re-run.

**Tool installation:**

If git, gh, or gitleaks show ✗ in the status table, detect the current shell environment:

```bash
uname -s
winget --version
```

Determine environment using this priority order:
1. `uname -s` returns `Darwin` → macOS
2. `uname -s` returns `Linux` → Linux/WSL shell (sudo required — treat as Linux regardless of winget availability; on WSL2, winget may be accessible via Windows interop but installs to the Windows environment, not WSL)
3. `uname -s` returned neither `Darwin` nor `Linux` AND `winget --version` succeeds → Windows-native shell (PowerShell, cmd, or Git Bash)

**macOS OR Windows-native shell:**

<mandatory>Call AskUserQuestion with:
- Question: "The following tools are missing and vibe-check will not work without them: [list each missing tool]. Install them now?"
- Options:
  - "Yes — install them now"
  - "I'll install them myself"
</mandatory>

If "I'll install them myself": show the install commands for each missing tool and stop here.

If "Yes — install them now": run the appropriate command for each missing tool:

- git missing on macOS: `brew install git`
- git missing on Windows: `winget install --id Git.Git`
- gh missing on macOS: `brew install gh`
- gh missing on Windows: `winget install --id GitHub.cli`
- gitleaks missing on macOS: `brew install gitleaks`
- gitleaks missing on Windows: `winget install --id gitleaks.gitleaks`

After all installs complete, re-run the version checks for the tools that were just installed:
```bash
git --version
gh --version
gitleaks version
```

If any tool still fails after install: tell the user "Installation of [tool] failed — [error output]. You may need to install it manually." Show the manual install command and stop here. For macOS git specifically: if `brew install git` failed, the correct alternative is `xcode-select --install` (installs Xcode Command Line Tools, which includes git — no Homebrew required).

**Linux/WSL shell:**

<mandatory>Call AskUserQuestion with:
- Question: "The following tools are missing and vibe-check will not work without them: [list each missing tool]. Install them now?"
- Options:
  - "Yes — install them now"
  - "I'll install them myself"
</mandatory>

If "I'll install them myself": show the install commands for each missing tool, then tell the user: "Once you've installed them, re-run `/vc-bootstrap` to complete setup." Stop here.
- git: `sudo apt install -y git`
- gh: `curl -sS https://webi.sh/gh | sh`
- gitleaks: `curl -sSfL https://raw.githubusercontent.com/gitleaks/gitleaks/main/scripts/install.sh | sh -s -- -b /usr/local/bin`

If "Yes — install them now": run the appropriate command for each missing tool via the Bash tool:
- git missing: `sudo apt install -y git`
- gh missing: `curl -sS https://webi.sh/gh | sh`
- gitleaks missing: `curl -sSfL https://raw.githubusercontent.com/gitleaks/gitleaks/main/scripts/install.sh | sh -s -- -b /usr/local/bin`

After all installs complete, re-run the version checks for the tools that were just installed:
```bash
git --version
gh --version
gitleaks version
```

If any tool still fails after install: tell the user "Installation of [tool] failed — [error output]. You may need to install it manually. Once fixed, re-run `/vc-bootstrap` to complete setup." Stop here.

</phase>

---

<phase id="1" name="git-config">

## Phase 1 — Git config

Git ships with VS Code and is almost always already present. This phase ensures name,
email, and default branch are configured.

**If `git --version` still failed** (installation in Phase 0 did not complete): tell the user git must be installed before continuing and stop here.

**If git IS installed:**

Check each config value and only prompt for what is missing.

**If `user.name` is not set:**
<mandatory>Call AskUserQuestion with:
- Question: "What name should appear on your git commits? This is public on GitHub. Type it in the 'Other' field below — for example: Jane Smith"
- Options:
  - "Enter my name above ↑"
  - "Skip — I'll set this up later"
</mandatory>
If a name was entered in Other: run `git config --global user.name "[name]"`
If Skip: note user.name as "not set".

**If `user.email` is not set:**
<mandatory>Call AskUserQuestion with:
- Question: "What email address should appear on your git commits? Use the same email as your GitHub account. Type it in the 'Other' field below — for example: jane@example.com"
- Options:
  - "Enter my email above ↑"
  - "Skip — I'll set this up later"
</mandatory>
If an email was entered in Other: run `git config --global user.email "[email]"`
If Skip: note user.email as "not set".

**If both name and email are already set:** note "git ✓ already configured" and proceed.

Check the current value first:
```bash
git config --global init.defaultBranch
```
If the output is non-empty, skip this step — the user's existing preference is preserved.
If the output is empty (not set), run:
```bash
git config --global init.defaultBranch main
```
Tell the user: "Set your default branch name to 'main' — this is the name git gives the first branch in any new project you create."

</phase>

---

<phase id="2" name="github-cli">

## Phase 2 — GitHub CLI

**If `gh --version` still failed** (installation in Phase 0 did not complete): tell the user GitHub CLI must be installed before continuing and stop here.

**If gh IS installed but `gh auth status` failed** (not authenticated):

Tell the user:

GitHub CLI is installed but not connected to your GitHub account yet. Here's how to do
that — it only takes a minute:

**Step 1 — Open the terminal in VS Code**

- Windows or Linux: press **Ctrl+`** (the backtick key — top-left of your keyboard, just
  above the Tab key)
- Mac: press **Cmd+`** or go to **View → Terminal** in the top menu bar

**Step 2 — Run the login command**

Type this and press Enter:

    gh auth login

**Step 3 — Answer the prompts**

A menu will appear. Use your **arrow keys** to highlight each choice and press **Enter**:
- **Where do you use GitHub?** → Pick **GitHub.com**
- **What is your preferred protocol?** → Pick **HTTPS**
- **How would you like to authenticate?** → Pick **Login with a web browser**

**Step 4 — Authorize in your browser**

You will see a short code like `XXXX-XXXX`. Copy it. Your browser will open automatically.
Paste the code and click **Authorize GitHub CLI**. If your browser doesn't open, go to
https://github.com/login/device and enter the code there.

**Step 5 — Come back here**

Once the terminal shows "Logged in as [your username]", come back and continue.

<mandatory>Call AskUserQuestion with:
- Question: "Have you completed the GitHub CLI login in your browser?"
- Options:
  - "Yes — I'm logged in"
  - "I got an error or the browser didn't open"
</mandatory>

If error: Tell the user they can also authenticate with a personal access token:
1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Give it a name, set an expiration, and check the **repo** and **read:org** scopes
4. Copy the generated token
5. In the VS Code terminal, run `gh auth login --with-token` and paste the token when prompted

Tell them to re-run `/vc-bootstrap` after completing this. Stop here.

If done: run `gh auth status` to confirm. If it still shows unauthenticated, show the error
output and suggest they try the token method above. Stop here.

**If gh IS installed and already authenticated:** note "GitHub CLI ✓ already authenticated"
and proceed.

</phase>

---

<phase id="3" name="gitleaks">

## Phase 3 — Gitleaks

Gitleaks scans your code for accidentally committed secrets before they reach GitHub. The
`/vc-ship` skill runs it automatically before every push.

**If `gitleaks version` still failed** (installation in Phase 0 did not complete): tell the user gitleaks must be installed before continuing and stop here.

**If gitleaks IS installed:** note "gitleaks ✓ ready" and proceed.

</phase>

---

<phase id="4" name="scaffold">

## Phase 4 — Project scaffold

### .gitignore

Check whether `.gitignore` exists in the current directory using the Read tool.

**If no `.gitignore` exists:** use the Write tool to create `.gitignore` with the
security-baseline template below.

**If `.gitignore` already exists:** Use the Read tool to read it and check whether the
line `# Security — never commit secrets or credentials` is already present.

If the marker is already present: the security block was added in a previous run — skip
without asking.

If the marker is not present:
<mandatory>Call AskUserQuestion with:
- Question: "A .gitignore already exists in this project. Add the security baseline patterns to it, or leave it as-is?"
- Options:
  - "Add security patterns"
  - "Leave it as-is"
</mandatory>
If Add security patterns: use the Edit tool to append the security section to the end of
the existing file.
If Leave it as-is: skip.

**Security-baseline `.gitignore` template:**

```
# ============================================================
# Security — never commit secrets or credentials
# ============================================================

# Environment variables and local config
.env
.env.*
.envrc
.envrc.*
local_settings.py
settings.py
database.yml
application_default_credentials.json

# Private keys and certificates
*.pem
*.key
*.p12
*.pfx
*.p8
*.pkcs8
*.jks
*.keystore
*.ppk
id_rsa
id_ecdsa
id_ed25519
id_dsa

# Secret stores and credential files
*.secret
*.secrets
*.vault
*.enc
*secrets*
*password*
*passwd*
.netrc
*credentials.json
*service-account*.json
*-key.json

# Package manager auth (can contain registry tokens)
.npmrc
.yarnrc
.yarnrc.yml
.pypirc

# Infrastructure secrets
*.tfstate
*.tfstate.backup
*.tfvars
*.tfvars.json
kubeconfig
*.kubeconfig
google-services.json
GoogleService-Info.plist
docker-compose.override.yml
docker-compose.*.yml
wrangler.toml
fly.toml
.htpasswd
htpasswd

# ============================================================
# Operating system files
# ============================================================

.DS_Store
Thumbs.db
desktop.ini

# ============================================================
# Editor files
# ============================================================

.idea/
# .vscode/    ← uncomment this line to exclude VS Code settings from git

# ============================================================
# How to add your own patterns
# ============================================================
#
# Ignore a specific file:
#   my-notes.txt
#
# Ignore all files with a given extension:
#   *.log
#
# Ignore a whole folder and everything inside it:
#   my-folder/
#
# Ignore a file only in the project root (not in subfolders):
#   /config.local.json
#
# Ignore everything in a folder but keep the folder itself:
#   temp/*
#   !temp/.gitkeep
```

### Suite orientation

Tell the user in plain language what each skill does and when to use it:

- **/vc-plan** — Start here for every new feature. Creates a branch, writes a plan, and
  tracks what you're building on a roadmap.
- **/vc-audit** — Reviews your code before you ship. Finds bugs, security issues, and
  things you might have missed. Run it after finishing a feature.
- **/vc-ship** — Pushes your branch and creates a pull request on GitHub, with a secret
  scan and test coverage check built in. Run it after audit passes.
- **/vc-retro** — Looks back at recent work and helps you see what's going well and what to
  improve. Run it weekly or at the end of a milestone.
- **/vc-onboard** — Use this if you already have a project with existing code. It maps the
  codebase into feature areas, scaffolds git if needed, optionally sets up a GitHub remote,
  and writes plan stubs for each area to your main branch, so you can pick features one at a time with `/vc-plan`.

Re-run `/vc-bootstrap` on any new machine you code from — git config, GitHub CLI auth, and gitleaks are machine-level and need to be set up once per machine. The `.gitignore` and project routing steps run every time.

### Write artifact

Get the authenticated GitHub username:
```bash
gh api user --jq '.login'
```
If this returns empty or exits non-zero, try the fallback:
```bash
gh auth status
```
Extract the username from a line like `Logged in to github.com account [username]`. If that also fails or returns no username, use `[GitHub username — run \`gh api user --jq '.login'\` to confirm]` as the value in the artifact.

Use the Write tool to create `.vibe-check/vc-bootstrap.md`:

```markdown
# vc-bootstrap
**Date:** [today's date]
**Status:** complete

## Configured

| Item | Value |
|------|-------|
| git user.name | [name or "not set — run /vc-bootstrap to configure"] |
| git user.email | [email or "not set — run /vc-bootstrap to configure"] |
| git defaultBranch | [value from `git config --global init.defaultBranch` as read in Phase 1] |
| GitHub CLI | ✓ authenticated as @[username] |
| gitleaks | ✓ [version] |
```

Note: extract the gitleaks version string from the `gitleaks version` output collected in Phase 0 (e.g. `v8.18.4`). Use that value for [version] above.

</phase>

---

<phase id="5" name="handoff">

## Phase 5 — Handoff

Present a summary of everything set up or confirmed in this run.

Check whether this is a fresh project or an existing one:
```bash
git log --oneline -1
```

**`fatal: not a git repository` error** (no git repo initialized):
<mandatory>Call AskUserQuestion with:
- Question: "This folder isn't a git repository yet. Initialize one now?"
- Options:
  - "Yes — run git init"
  - "No — I'll set it up myself"
</mandatory>
If Yes: run `git init`. Then run:
```bash
git add .gitignore .vibe-check/vc-bootstrap.md
git commit -m "chore: bootstrap vibe-check setup"
```
Then tell the user:
> You're all set. Run **/vc-plan** to start your first feature — it will create a branch,
> help you think through what you're building, and track it on a roadmap. When you're
> ready to upload your code to GitHub, run **/vc-ship** — it will create the GitHub
> repository and send your commits there for you.
If No: tell the user to run `git init` in their terminal when ready, then run `/vc-plan`.

**No output, empty output, or a `fatal: ... does not have any commits yet` error** (fresh project — treat all three as equivalent): Run:
```bash
git add .gitignore .vibe-check/vc-bootstrap.md
git commit -m "chore: bootstrap vibe-check setup"
```
Then tell the user:

> You're all set. Run **/vc-plan** to start your first feature — it will create a branch,
> help you think through what you're building, and track it on a roadmap. When you're
> ready to upload your code to GitHub, run **/vc-ship** — it will create the GitHub
> repository and send your commits there for you.

**Has commits** (existing project): Tell the user:

> You're all set. Run **/vc-onboard** to bring the vibe-check suite up to speed with your
> existing codebase — it will map your code into feature areas and write plan stubs for
> each area to main — then run `/vc-plan` to start working through them.

</phase>
