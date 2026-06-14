# /vc-ship — Ship Flow

<!-- version: 2026-06-10 -->

Guides you through a safe push-and-PR flow for a feature branch. Before pushing, runs a
gitleaks secret scan (hard stop on any detected secrets), a lint check, and test coverage
validation against an 80% goal — installing tooling and writing missing tests automatically
if needed.

Checks that your audit is complete, scans the diff for files that shouldn't be committed,
and generates a functional testing checklist. Checks commit history for non-bisectable
patterns (WIP, fixup, squash) and offers to soft-reset and reorganize into clean atomic
commits before creating the PR. Creates the PR with a body reviewers can actually use and
updates the project roadmap automatically.

Run this when your branch is ready to ship.

---

## Version check

Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/versions.json`. If the fetch fails or returns an error for any reason, skip this section entirely and proceed to Phase 0.

<output-handlers>

**Fetch succeeded — `vc-ship` version matches `2026-06-10`**: proceed silently.

**Fetch succeeded — newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /vc-ship is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue to Phase 0.
If Update now: follow the **Auto-update** steps below, then stop.

**Fetch succeeded — newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /vc-ship that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed to Phase 0.

</output-handlers>

**Auto-update:**
1. Run `git rev-parse --show-toplevel` to find the project root.
2. Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-ship.md`.
3. If both succeed: use the Write tool to write the fetched content to `[project-root]/.claude/commands/vc-ship.md`. Tell the user "Updated to the latest version. Please re-run /vc-ship." Do not continue.
4. If either fails: tell the user auto-update failed and to update manually at https://github.com/recycledwhitetrash/vibe-check. Do not continue.

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

Detect the current shell:

```bash
echo $SHELL
```

If the output is a path ending in `bash` or `zsh` (or similar Unix shell): use `&&` to chain
commands throughout this skill. If the output is empty or does not match, you are likely in
PowerShell — run each command as a separate sequential step instead of using `&&` chaining.

```bash
git branch --show-current
git for-each-ref --format='%(refname:short)' refs/heads/
git status --porcelain
gh --version
git symbolic-ref refs/remotes/origin/HEAD
```

<gate>Do not proceed until you have all four outputs.</gate>

<output-handlers>

**`gh --version` failed** (GitHub CLI not installed): Tell the user that GitHub CLI is
required to create PRs — they can install it by searching for "GitHub CLI". Stop here.

**`git branch --show-current` is empty** (detached HEAD): run `git branch` to list all
local branches.
<mandatory>Call AskUserQuestion with:
- Question: "The repo is in detached HEAD state — no branch is currently checked out. Which branch do you want to ship from?"
- Options: list each local branch as its own option (use Other to type a branch name manually).
</mandatory>
Run `git checkout [selected branch name]` to switch to that branch.
Re-read `git branch --show-current` to confirm the branch name, then continue normally.

**`git status --porcelain` is non-empty** (uncommitted changes exist):
<mandatory>Call AskUserQuestion with:
- Question: "There are uncommitted changes on this branch. They will not be included in the PR. Do you want to commit or stash them first?"
- Options:
  - "Pause — I will commit or stash my changes first"
  - "Continue — the uncommitted changes are intentionally excluded"
</mandatory>
If the user pauses: stop here.
If the user continues: note the file paths from the already-collected `git status --porcelain`
output as `[excluded-files]` (these will be written to the state file after slug derivation
below).

**Current branch is a default branch** (main, master, or develop):
<mandatory>Call AskUserQuestion with:
- Question: "You are on [branch], which appears to be the base branch. vc-ship is designed for feature branches. Are you sure you want to create a PR from this branch?"
- Options:
  - "Yes — continue"
  - "No — take me to the right branch"
</mandatory>
If No: tell the user "Run /vc-plan from [branch] — it will read your roadmap and offer
available features to start, or let you create a new branch." Stop.

**No default branch found in refs list**:
<mandatory>Call AskUserQuestion with:
- Question: "What is the name of the base branch this branch will be merged into?"
- Options:
  - "main"
  - "master"
  - "develop"
</mandatory>
Use the answer as BASE_BRANCH.

**Otherwise**: derive BASE_BRANCH using this priority chain:

1. From the `git symbolic-ref refs/remotes/origin/HEAD` output: if it returned a value, strip the `refs/remotes/origin/` prefix directly — do not use shell utilities. Use the result as BASE_BRANCH.
2. If symbolic-ref returned empty or errored: identify all branches whose name is exactly `main`, `master`, or `develop` — partial matches do not count.

If step 2 produces exactly one match: note it as BASE_BRANCH.

If step 2 produces more than one match:
<mandatory>Call AskUserQuestion with:
- Question: "Multiple base branches found: [list]. Which is the correct merge target for this PR?"
- Options: one option per matched branch name.
</mandatory>
Use the answer as BASE_BRANCH.

</output-handlers>

Slugify the current branch name: lowercase the full name, replace every character that is
not a-z, 0-9, or `-` with `-`, collapse runs of consecutive `-` into one, strip any leading
or trailing `-`. This is the branch slug used to find artifacts.

**Resume check:** Use the Read tool to check whether `.vibe-check/vc-ship/[branch-slug].md`
exists with `**Status:** in progress`. If it does: read `**Excluded files:**` and restore
as `[excluded-files]`. Note that this is a resumed run — continue from the last completed
phase rather than re-running Phase 0 setup.

If `[excluded-files]` is non-empty (set in the uncommitted changes handler above):
use the Write tool to create `.vibe-check/vc-ship/[branch-slug].md`:
```
# vc-ship: [branch-slug]
**Status:** in progress
**Excluded files:** [comma-separated list of paths]
```

```bash
git log BASE_BRANCH...HEAD --oneline
git diff BASE_BRANCH...HEAD --shortstat
```

<gate>Do not proceed until you have both outputs.</gate>

If `git log` returns no commits: tell the user there is nothing to ship on this branch and stop.

</phase>

---

<phase id="1" name="check-artifacts">

## Phase 1 — Check artifacts

Use the Read tool to check for a vc-audit artifact and a vc-plan artifact for this branch.

- vc-audit: `.vibe-check/vc-audit/[branch-slug].md`
- vc-plan: `.vibe-check/vc-plan/[branch-slug].md`

<gate>Do not proceed until you have attempted both reads.</gate>

<output-handlers>

**vc-audit artifact found**: Read the artifact. Extract:
- `**Status:**` value (IN PROGRESS or CONVERGED)
- `**Passes completed:**` count
- Number of open findings (count of F-NNN items in the Open section)
Note these for the review readiness table in Phase 3.

If `**Status:** IN PROGRESS`:
<mandatory>Call AskUserQuestion with:
- Question: "An in-progress audit was found for this branch — [N] passes completed, [N] open findings, convergence not declared. Shipping with an incomplete audit means unresolved findings may reach the reviewer. Continue shipping, or pause to finish the audit first?"
- Options:
  - "Pause — I will finish /vc-audit first"
  - "Continue — ship with the audit incomplete"
</mandatory>
If the user pauses: stop here.
If the user continues: note audit status as "⚠ IN PROGRESS" for the review readiness table.

**vc-audit artifact NOT found**: use the Glob tool to check for
`.vibe-check/vc-audit/[branch-slug]--*.md` (scoped audit artifacts). If a match is found:
read the first match, extract `**Status:**` and `**Passes completed:**`, and note it as
`✓ SCOPED AUDIT — covers [path-slug] only` in the review readiness table. Treat it as a
found artifact and proceed without the AskUserQuestion below.

If no scoped artifact is found either:
<mandatory>Call AskUserQuestion with:
- Question: "No vc-audit artifact was found for this branch. Running /vc-audit before shipping catches bugs and security issues before they reach a reviewer. You can pause and run /vc-audit first, or continue without an audit."
- Options:
  - "Pause — I will run /vc-audit first"
  - "Continue — ship without an audit"
</mandatory>
If the user pauses: stop here.
If the user continues: note audit status as "not run" for the review readiness table.

**vc-plan artifact found**: note it exists.

**vc-plan artifact NOT found**: note it does not exist. No warning needed.

</output-handlers>

</phase>

---

<phase id="2" name="quality-gates">

## Phase 2 — Quality gates

Run checks A, B, and C in order before building the PR. Gitleaks finding real secrets is a
hard stop. Lint and test failures are soft gates — the user can continue, but failures are
noted in the review readiness table.

### A — Gitleaks (secret scan)

```bash
gitleaks version
```

<output-handlers>

**`gitleaks version` failed** (not installed):

Run `uname -s` and `winget --version` to detect OS (same priority order as /vc-bootstrap: Darwin → macOS, Linux → Linux/WSL, neither + winget succeeds → Windows-native).

<mandatory>Call AskUserQuestion with:
- Question: "Gitleaks is not installed. It scans your code for secrets like API keys and passwords before they reach GitHub. Install it now or skip the scan?"
- Options:
  - "Install now"
  - "Skip — continue without scanning"
</mandatory>

If Install now:
  - **macOS**: run `brew install gitleaks`. If the install exits non-zero, tell the user it failed and show the error. Stop here — do not proceed without gitleaks on a failed install.
  - **Windows-native**: run `winget install --id gitleaks.gitleaks`. If the install exits non-zero, tell the user it failed and show the error. Stop here.
  - **Linux/WSL**: attempt `sudo apt install -y gitleaks`. If it succeeds (exit 0): re-run `gitleaks version` to confirm and continue to the `.gitleaks.toml` check below. If it fails or requires interactive input: tell the user "Run this in your terminal: `sudo apt install gitleaks`" (fallback if apt fails: download a binary from https://github.com/gitleaks/gitleaks/releases). Then:
    <mandatory>Call AskUserQuestion with:
    - Question: "Run `sudo apt install gitleaks` in your terminal, then come back here."
    - Options:
      - "Done — gitleaks is installed"
      - "Skip — continue without scanning"
    </mandatory>
    If Done: re-run `gitleaks version` to confirm. If it succeeds: continue to the `.gitleaks.toml` check below. If it still fails: tell the user and stop.
    If Skip: note gitleaks as "not run" and proceed to Section B.
  - After a successful macOS or Windows install: re-run `gitleaks version` to confirm. If it now succeeds: continue to the `.gitleaks.toml` check below. If it still fails: tell the user and stop — secret scanning cannot be skipped after an install attempt.

If Skip: note gitleaks as "not run" and proceed to Section B.

**`gitleaks version` succeeded**: check whether `.gitleaks.toml` exists using the Read tool.

If `.gitleaks.toml` does NOT exist:
<mandatory>Call AskUserQuestion with:
- Question: "No .gitleaks.toml config found. Gitleaks will use its default rules — fine for most projects. Projects with test fixtures or example configs containing fake secrets may want a custom config to prevent false positives."
- Options:
  - "Use defaults — scan now"
  - "Create a .gitleaks.toml first"
</mandatory>
If Create a .gitleaks.toml:
  <mandatory>Call AskUserQuestion with:
  - Question: "Does your project have test fixtures, example .env files, or documentation with fake/example secrets that could trigger false positives?"
  - Options:
    - "Yes — I have fixtures or examples with fake secrets"
    - "No — write a minimal config"
  </mandatory>
  If Yes: ask the user to list the directories or file patterns to exclude (use the Other
  field). Before writing, check each path the user provided against these broad-pattern
  warnings: `**/*`, `*`, `src/`, `lib/`, `app/`, or any single top-level directory that
  would cover production source code. If any match, warn the user: "The pattern '[pattern]'
  would exclude a large portion of your codebase from secret scanning — is this intentional?"
  and require a confirm before proceeding (add a "Yes — this is intentional" / "Let me fix it"
  AskUserQuestion).

  Write `.gitleaks.toml`:
  ```toml
  title = "gitleaks config"

  [extend]
  useDefault = true

  [[rules]]
  [rules.allowlist]
  paths = [
    '''<user-provided paths>'''
  ]
  ```

  After writing, use the Read tool to read the file back and show its full contents to the
  user:
  <mandatory>Call AskUserQuestion with:
  - Question: "Here is the .gitleaks.toml that will be committed. Does the allowlist look correct? Any path listed here will be excluded from secret scanning."
  - Options:
    - "Looks correct — commit it"
    - "Fix it — describe the change in Other"
  </mandatory>
  If Fix: apply the described changes using the Edit tool, then show the file again and ask
  once more before committing.

  If No: write a minimal config:
  ```toml
  title = "gitleaks config"

  [extend]
  useDefault = true
  ```
  Commit: `git add .gitleaks.toml && git commit -m "chore: add gitleaks config"`
  PowerShell: run as two separate commands.

Scan for secrets in two passes — both must be clean before proceeding:

**Pass 1 — committed diff (what goes into the PR):**
```bash
git diff BASE_BRANCH...HEAD | gitleaks detect --pipe
```

**Pass 2 — uncommitted changes (staged and unstaged):**
```bash
git diff HEAD | gitleaks detect --pipe
```

</output-handlers>

<gate>

**Either pass exits non-zero** (secrets detected): Hard stop. Show every finding gitleaks
reported. Tell the user which pass caught it (committed diff or uncommitted changes). Tell
the user: "These must be removed before shipping. If a secret was introduced in a previous
commit, use `git filter-repo` to purge it from git history. Do not push until all secrets
are resolved." Do not continue.

**Both passes exit 0** (no secrets found): note "gitleaks ✓ clean" and proceed to Section B.

</gate>

### B — Lint

**Node/JS/TS package manager detection** (do this once, reuse in Section C):
Check for lockfiles in the project root to determine PKG_MANAGER:

| Lockfile | PKG_MANAGER |
|----------|-------------|
| `pnpm-lock.yaml` | `pnpm` |
| `bun.lockb` or `bun.lock` | `bun` |
| `yarn.lock` | `yarn` |
| `package-lock.json` or none found | `npm` |

If more than one lockfile is detected:
<mandatory>Call AskUserQuestion with:
- Question: "Multiple package manager lockfiles were found: [list]. Which package manager does this project use?"
- Options:
  - "npm"
  - "yarn"
  - "pnpm"
  - "bun"
</mandatory>
Use the answer as PKG_MANAGER.

Detect whether a lint command is available:

| Stack | Signal | Command |
|-------|--------|---------|
| Node / JS / TS | `lint` key in `package.json scripts` | `[PKG_MANAGER] run lint` |
| Python | `ruff` in `pyproject.toml` or installed | `ruff check .` |
| Python (fallback) | `flake8` installed | `flake8 .` |
| Go | `golangci-lint` installed | `golangci-lint run` |

**If lint tooling is found**: run the detected command per the table above.

**If no lint tooling is found**: detect the project stack and set it up before running.

**Node / JS / TS** (`package.json` exists but no `lint` script):
Tell the user: "No lint config found — installing ESLint."
Check for `tsconfig.json` to detect TypeScript.
Run: `[PKG_MANAGER] add -D eslint @eslint/js` (TypeScript: also add `typescript-eslint`)
Write `eslint.config.js`:

Plain JS:
```js
import js from "@eslint/js";
export default [js.configs.recommended];
```
TypeScript:
```js
import js from "@eslint/js";
import tseslint from "typescript-eslint";
export default tseslint.config(js.configs.recommended, ...tseslint.configs.recommended);
```

Use the Edit tool to add `"lint": "eslint ."` to the `scripts` section of `package.json`.
Run: `[PKG_MANAGER] run lint`

**Python** (`pyproject.toml`, `setup.py`, or `.py` files in the root):
Tell the user: "No lint config found — installing ruff."
Run: `pip install ruff`
If `pyproject.toml` exists: use the Edit tool to append:
```toml
[tool.ruff]
# ruff defaults apply — add per-project overrides here
```
If not: use the Write tool to create a minimal `pyproject.toml` with the section above.
Run: `ruff check .`

**Go** (`go.mod` present):
Tell the user: "golangci-lint is not installed."
Detect OS and give the appropriate install command:
- macOS: `brew install golangci-lint`
- Linux / WSL: `curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin`
- Windows: `winget install golangci-lint`
Tell the user to re-run `/vc-ship` after installation. Stop here.

**Unknown stack**:
<mandatory>Call AskUserQuestion with:
- Question: "No lint tooling was detected. What language is this project written in?"
- Options:
  - "JavaScript or TypeScript"
  - "Python"
  - "Go"
</mandatory>
Handle as above for the selected stack. If Other: note "lint — not configured" and proceed
to Section C.

<output-handlers>

**Lint passes**: note "lint ✓" and proceed to Section C.

**Lint fails**:
<mandatory>Call AskUserQuestion with:
- Question: "Lint check failed. Fix lint errors before shipping, or continue with failures noted in the PR."
- Options:
  - "Pause — I will fix the lint errors"
  - "Continue — note lint failures in the PR"
</mandatory>
If Pause: stop here.
If Continue: note "lint ⚠ failures" and proceed to Section C.

</output-handlers>

### C — Test coverage

Detect whether test tooling is available:

| Stack | Signal | Coverage command |
|-------|--------|-----------------|
| Node / JS / TS | `test` key in `package.json scripts` | determined by framework detection below |
| Python | `pytest` installed or in `pyproject.toml` | `pytest --cov=. --cov-report=term-missing` |
| Go | always available | `go test ./... -cover` |

**If a Node/JS/TS `test` script is found**: before running, detect the test framework by
reading `package.json`. Check in this order:
1. `devDependencies` contains `vitest` → framework is **Vitest**
2. `devDependencies` contains `jest` or `ts-jest` → framework is **Jest**
3. The `test` script value contains `vitest` → framework is **Vitest**
4. The `test` script value contains `jest` → framework is **Jest**
5. PKG_MANAGER is `bun` → framework is **bun test**
6. None of the above → framework is **unknown**

Coverage command by framework:

| Framework | npm | pnpm | yarn | bun |
|-----------|-----|------|------|-----|
| Jest | `npm test -- --coverage` | `pnpm test -- --coverage` | `yarn test --coverage` | — |
| Vitest | `npx vitest run --coverage` | `pnpm dlx vitest run --coverage` | `yarn dlx vitest run --coverage` | — |
| bun test | — | — | — | `bun test --coverage` |
| Unknown | see handler below |

**Unknown framework** (a `test` script exists but the framework is unrecognized):
<mandatory>Call AskUserQuestion with:
- Question: "A test script exists but the framework could not be detected. Which test framework does this project use? (For Mocha, Jasmine, or other frameworks, use Other and specify.)"
- Options:
  - "Jest"
  - "Vitest"
  - "bun test"
  - "None — set one up for me"
</mandatory>
If Jest, Vitest, or bun test: run the corresponding coverage command from the table above.
If None: follow the Node/JS/TS setup flow below (detect `vite.config.*` → Vitest, else
Jest unless PKG_MANAGER is `bun`) to install and configure a framework, then run coverage.
If Other: ask the user what coverage command to run. If they cannot provide one, note
"tests — not configured" and proceed to Phase 3.

**If test tooling is found**: run the coverage command per the detection above.

**If no test tooling is found**: detect the project stack and set it up before running.

**Node / JS / TS** (`package.json` exists but no `test` script):
Tell the user: "No test config found — setting up [Jest/Vitest/bun test]."
Check for `vite.config.*` → use Vitest. Otherwise use Jest, unless PKG_MANAGER is `bun`.

*Jest (npm / pnpm / yarn)*:
Run: `[PKG_MANAGER] add -D jest @jest/globals`
If TypeScript: also `[PKG_MANAGER] add -D ts-jest @types/jest`
Write `jest.config.js`:

Plain JS: `export default { testEnvironment: "node", collectCoverage: true, coverageReporters: ["text"] };`

TypeScript: `export default { preset: "ts-jest", testEnvironment: "node", collectCoverage: true, coverageReporters: ["text"] };`

Use the Edit tool to add `"test": "jest --coverage"` to `package.json scripts`.

*Vitest (npm / pnpm / yarn)*:
Run: `[PKG_MANAGER] add -D vitest @vitest/coverage-v8`
Use the Edit tool to add `"test": "vitest run --coverage"` to `package.json scripts`.

*bun*:
No install needed. Use the Edit tool to add `"test": "bun test --coverage"` to
`package.json scripts` if not already present.

**Python** (`pyproject.toml`, `setup.py`, or `.py` files in the root):
Tell the user: "No test config found — installing pytest and pytest-cov."
Run: `pip install pytest pytest-cov`
If `pyproject.toml` exists: use the Edit tool to append:
```toml
[tool.pytest.ini_options]
addopts = "--cov=. --cov-report=term-missing"
```
If not: use the Write tool to create a minimal `pyproject.toml` with the section above.

**Go** (`go.mod` present):
`go test` is built-in — no setup needed. Run `go test ./... -cover` directly.

**Unknown stack**:
<mandatory>Call AskUserQuestion with:
- Question: "No test tooling was detected. What language is this project written in?"
- Options:
  - "JavaScript or TypeScript"
  - "Python"
  - "Go"
</mandatory>
Handle as above for the selected stack. If Other: note "tests — not configured" and proceed
to Phase 3.

After setup, run the test command. If the test runner exits with "no tests found" (no test
files exist yet — common right after setup), treat this as 0% coverage and skip directly
to the coverage evaluation section.

<output-handlers>

**Tests fail outright**:
<mandatory>Call AskUserQuestion with:
- Question: "Tests are failing. Fix failing tests before shipping, or continue with failures noted in the PR."
- Options:
  - "Pause — I will fix the failing tests"
  - "Continue — note test failures in the PR"
</mandatory>
If Pause: stop here.
If Continue: note "tests ⚠ failing" and proceed to Phase 3. Skip coverage evaluation.

**Tests pass**: parse the output for an overall line coverage percentage.

</output-handlers>

#### Coverage evaluation

**Coverage ≥ 80%**: note "tests ✓ [N]% coverage" and proceed to Phase 3.

**Coverage < 80%** (or coverage data is unavailable):

Get the list of files changed on this branch:
```bash
git diff BASE_BRANCH...HEAD --name-only
```

For each source file (skip test files, config files, and lock files), build a LOC audit
table. Source lines = non-blank, non-comment lines. Test file = check for a corresponding
file matching `*.test.*`, `*.spec.*`, or any `__tests__/`, `tests/`, or `spec/` directory.
Coverage = from the coverage output if available, otherwise "—".

| File | Source lines | Test file | Coverage |
|------|-------------|-----------|----------|
| src/auth/session.ts | 120 | ✓ | 42% |
| src/auth/middleware.ts | 88 | — | 0% |

Present the audit table to the user, then work through files with no test file or below-80%
coverage in batches of up to 3 files at a time:
1. Read each source file. If existing test files are present in the project, read one as a
   style reference.
2. Write a test file covering: public function/method signatures, happy paths, error paths,
   and at least one edge case per function. Match the testing framework already in use.
3. If the `Test file` column shows `✓` (an existing test file): use the Read tool to read
   the existing file, identify which functions or paths are not yet covered, and use the
   Edit tool to append new test cases for them — do not overwrite the file.
   If the `Test file` column shows `—` (no test file exists): use the Write tool to create
   the test file.
4. Run the test command scoped to just the new test file to verify it passes before committing.
5. If the tests fail: read the error output, identify which specific test cases are failing,
   fix them automatically, and run again. Repeat up to 3 fix attempts per failing test case.
6. If a specific test case still fails after 3 attempts: remove only that test case from the
   file using the Edit tool. Add the affected source function or scenario to a running list
   `[failed-coverage-items]`. Tell the user what was removed and why.
7. After pruning all unfixable test cases: if any test cases remain in the file, run once more
   to confirm they pass, then commit: `git add [test-file] && git commit -m "test: add coverage for [file]"`.
   PowerShell: run as two separate commands.
   If no test cases remain (all were pruned), do not create or commit the file.

After all batches: re-run the coverage command and show the updated percentage.

Track the number of test-writing rounds completed (each pass through the batch loop = 1 round).

If still below 80% and fewer than 3 rounds completed:
<mandatory>Call AskUserQuestion with:
- Question: "Coverage is now [N]% — still below 80%. Confirm shipping at this coverage?"
- Options:
  - "Confirm [N]% — ship as-is"
  - "Continue adding tests"
</mandatory>

**If Confirm ship as-is**: note "tests ⚠ [N]% (below 80%)" and proceed to Phase 3.

**If Continue adding tests**: re-derive the list of below-80% files from the updated coverage
output. Run another batch pass (Steps 1–7 above) for only those files. Increment the round
counter. After the pass, re-run coverage and repeat this check.

If still below 80% after 3 rounds: skip the question and proceed directly — note
"tests ⚠ [N]% (below 80%)" and proceed to Phase 3.

</phase>

---

<phase id="3" name="read-diff">

## Phase 3 — Read the diff

```bash
git diff BASE_BRANCH...HEAD -- ':!.env' ':!.env.*' ':!.envrc' ':!.envrc.*' ':!*.pem' ':!*.key' ':!*.p12' ':!*.pfx' ':!*.p8' ':!*.pkcs8' ':!*.jks' ':!*.keystore' ':!*.ppk' ':!id_rsa' ':!id_ecdsa' ':!id_ed25519' ':!id_dsa' ':!*.secret' ':!*.secrets' ':!*.vault' ':!*.enc' ':!*secrets*' ':!*password*' ':!*passwd*' ':!.netrc' ':!.npmrc' ':!.yarnrc' ':!.yarnrc.yml' ':!.pypirc' ':!*credentials.json' ':!*service-account*.json' ':!*-key.json' ':!*.tfstate' ':!*.tfstate.backup' ':!*.tfvars' ':!*.tfvars.json' ':!google-services.json' ':!GoogleService-Info.plist' ':!kubeconfig' ':!*.kubeconfig' ':!docker-compose.override.yml' ':!docker-compose.*.yml' ':!local_settings.py' ':!settings.py' ':!database.yml' ':!application_default_credentials.json' ':!wrangler.toml' ':!fly.toml' ':!.htpasswd' ':!htpasswd'
```

<gate>Do not proceed until you have the diff output.</gate>

### Suspicious file check

From the diff output, extract the list of changed file paths. Check each path against
these patterns — match by path segment, not exact name:

| Pattern | Reason |
|---------|--------|
| `node_modules/` anywhere in path | dependency directory — should not be committed |
| `dist/`, `build/`, `out/`, `target/` at root or in path | build output |
| `__pycache__/`, `*.pyc`, `*.pyo` | Python bytecode cache |
| `coverage/`, `.nyc_output/` | test coverage report output |
| `venv/`, `.venv/`, `env/` at root | Python virtual environment |
| `*.log` | log files |
| `.DS_Store`, `Thumbs.db`, `desktop.ini` | OS metadata |
| `*.tmp`, `*.temp`, `*.swp` | temporary files |
| `.cache/`, `.parcel-cache/` | tool cache directories |

If no changed files match: proceed silently.

If any changed files match: tell the user which files matched and why, then:
<mandatory>Call AskUserQuestion with:
- Question: "These files in your diff look like they may not belong in git: [list with reason for each]. Add them to .gitignore?"
- Options:
  - "Yes — add these patterns to .gitignore"
  - "No — these files should be committed"
</mandatory>

If Yes: use the Edit tool to append the appropriate patterns to `.gitignore`. If `.gitignore`
does not exist, use the Write tool to create it with just those patterns. Then run:
`git add .gitignore && git commit -m "chore: update .gitignore"`
PowerShell: run as two separate commands.

</phase>

---

<phase id="3.5" name="bisectability">

## Phase 3.5 — Bisectability check

Run:
```bash
git log BASE_BRANCH...HEAD --oneline
```

Scan the commit messages for patterns that indicate non-bisectable commits. Flag any message that:
- Contains `wip`, `fixup`, `squash`, `temp`, `debug`, `checkpoint` (case-insensitive)
- Starts with `fixup!` or `squash!` (git rebase shorthand)
- Is very short (1–3 characters, e.g. "." or "x")

Bisectable branches have clean, atomic commits — each one leaves the codebase in a working
state with a meaningful message. This makes `git bisect` reliable for tracking down regressions.

If no flagged commits: proceed silently to Phase 4.

If flagged commits are found:
<mandatory>Call AskUserQuestion with:
- Question: "Found [N] commit(s) that may break git bisect: [list of flagged messages]. Would you like to reorganize into clean, atomic commits? This will soft-reset the branch back to [BASE_BRANCH] — all your changes stay in the working tree, nothing is lost — then recommit them in logical groups."
- Options:
  - "Yes — help me reorganize into clean commits" (Recommended)
  - "Continue as-is"
</mandatory>

If yes:

1. Run `git reset --soft $(git merge-base HEAD BASE_BRANCH)` to put all branch commits back
   into the working tree, resetting exactly to the divergence point (not BASE_BRANCH tip).

2. Run `git status --short` to get the full list of changed files.

3. If `[excluded-files]` is non-empty: remove those paths from the file list before
   proposing any groupings. Tell the user: "These files were in your working tree before
   the regroup and are excluded from all commit groups — they remain untouched:
   [list of excluded files]."

4. Propose logical groupings from the remaining files based on file types and paths. Each
   group must leave the codebase in a working state on its own. Good groupings:
   - Production code changes by feature area (one commit per distinct concern)
   - Test files committed with the production code they test, or separately as `test:`
   - Config/tooling changes as `chore:`
   - Documentation and artifact changes as `docs:`

<mandatory>Call AskUserQuestion with:
- Question: "Here's how I'd group the changes for clean, bisectable commits: [list each group: proposed commit message + files]. Does this look right?"
- Options:
  - "Looks good — proceed"
  - "Change group [N] — describe in Other"
  - "Add all changes to one commit"
  - "Cancel regroup — continue as-is"
</mandatory>

If "Cancel regroup — continue as-is": proceed to Phase 4 without regrouping.

5. For each confirmed group in order:
   `git add [files in group] && git commit -m "[message]"`
   PowerShell: run as two separate commands.
   Use conventional commit prefixes: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`.

<gate>Do not proceed to Phase 4 until all groups are committed and `git status --short`
shows no files other than those in `[excluded-files]` (excluded working-tree files are
expected to remain).</gate>

</phase>

---

<phase id="4" name="draft-pr">

## Phase 4 — Draft the PR

*This phase drafts the PR content for user review. No GitHub actions happen here —
the push and PR creation are both in Phase 5.*

### PR title

Derive a title from the commit log and branch name. Keep it under 70 characters. Write it
as an action phrase: "Add dark/light mode toggle", "Fix session timeout on inactive tab".

### Work description

Write a 2–4 sentence plain-language summary of what this branch does. Write for a reviewer
who has not seen the branch — describe what changed and why, not how.

### Review readiness table

Build from the artifact check results in Phase 1. Use these status formats exactly:

| Skill | Status |
|-------|--------|
| /vc-plan | ✓ found |
| /vc-audit | ✓ CONVERGED — N passes · N open |
| Gitleaks | ✓ clean |
| Lint | ✓ |
| Tests | ✓ 87% coverage |

Status values:
- vc-plan found → `✓ found`
- vc-plan not found → `not run`
- vc-audit CONVERGED → `✓ CONVERGED — N passes · N open`
- vc-audit IN PROGRESS → `⚠ IN PROGRESS — N passes · N open`
- vc-audit not found → `not run`
- gitleaks clean → `✓ clean`
- gitleaks skipped or not installed → `not run`
- lint passes → `✓`
- lint failures (user continued) → `⚠ failures`
- lint not configured → `not configured`
- tests pass + ≥ 80% → `✓ N%`
- tests failing (user continued) → `⚠ failing`
- tests not configured → `not configured`
- tests below 80% confirmed → `⚠ N% (below 80%)`
- tests below 80% with pruned cases → `⚠ N% — auto-generated tests could not cover: [failed-coverage-items list]`

### Testing checklist

From the diff in Phase 3, generate a list of functional verification items — things the
developer should manually test to confirm the feature or fix works as intended.

Guidelines:
- Each item describes what to do and what to expect: "Toggle the dark/light mode switch —
  verify the UI theme changes immediately without a page reload"
- Cover the happy path for every changed feature or behavior
- Include at least one edge case per changed feature where relevant: empty input, missing
  data, boundary values, unauthenticated state
- Include at least one failure/error path for anything that can fail: "Submit the form with
  the email field empty — verify an error message appears and the form is not submitted"
- Do not write security checks or code assertions — this is a manual functional checklist
- Aim for 3–8 items; more than 10 items suggests the branch is too large for a single PR

### Present the draft

Present the full draft PR in your response — title, description, review readiness table,
and testing checklist — so the user can read it before deciding.

<mandatory>Call AskUserQuestion with:
- Question: "Does the PR title, description, and testing checklist look right?"
- Options:
  - "Looks good — create the PR"
  - "Edit the title — describe the change in Other"
  - "Edit the description or checklist — describe the change in Other"
</mandatory>

If the user requests edits: apply them and present the updated draft. Ask again. Do not
proceed to Phase 5 until the user approves the draft.

</phase>

---

<phase id="5" name="push-and-create">

## Phase 5 — Push and create the PR

### Commit vibe-check artifacts

Run `git status --porcelain .vibe-check/` to check for uncommitted changes in the artifact directory. If any exist, commit them now:

```bash
git add .vibe-check/
git commit -m "docs: add vibe-check artifacts"
```

This ensures the audit artifact, plan stub, and any other skill outputs travel with the PR and are visible to reviewers.

<gate>Do not push until the .vibe-check/ directory is clean (no uncommitted changes).</gate>

### Push

Before pushing, check whether `origin` is configured:

```bash
git remote -v
```

If `origin` is not listed:
<mandatory>Call AskUserQuestion with:
- Question: "No remote named 'origin' is configured. How would you like to add one?"
- Options:
  - "Create a new GitHub repository for me"
  - "I have a repository — let me enter the URL"
  - "Skip — I will add a remote manually"
</mandatory>

If "Create a new GitHub repository for me":
<mandatory>Call AskUserQuestion with:
- Question: "What visibility should the new GitHub repository have?"
- Options:
  - "Private"
  - "Public"
</mandatory>
Run `gh repo create --source=. --[private|public] --push`. If it fails, report the error and stop.
If it succeeds: check whether BASE_BRANCH exists on the remote:
```bash
git branch -r | grep origin/BASE_BRANCH
```
If BASE_BRANCH is not on the remote: run `git push origin BASE_BRANCH` before proceeding.
The remote is now configured and the branch has been pushed — skip the `git push` command
below and proceed to "Check for an existing PR".

If "I have a repository — let me enter the URL":
<mandatory>Call AskUserQuestion with:
- Question: "Enter your GitHub repository URL — for example: https://github.com/yourname/yourrepo.git"
- Options:
  - "Cancel — I will add a remote manually"
</mandatory>
If the user provides a URL in Other: run `git remote add origin [URL]`, then proceed to the push.
If Cancel: tell the user to run `git remote add origin [URL]` and then re-run `/vc-ship`. Stop here.

If "Skip — I will add a remote manually": tell the user to run `git remote add origin [URL]`
and then re-run `/vc-ship`. Stop here.

```bash
git push -u origin HEAD
```

<gate>Do not proceed until the push completes. If the push fails (remote rejected,
authentication error, or any other error), report the exact error message and stop —
do not attempt to create a PR.</gate>

### Check for an existing PR

```bash
gh pr view --json number,title,url
```

<gate>Do not proceed until you have the output.</gate>

<output-handlers>

**Command succeeded and returned JSON** (PR already exists):
Tell the user a PR already exists and show the number, title, and URL.
<mandatory>Call AskUserQuestion with:
- Question: "A PR already exists for this branch. What would you like to do?"
- Options:
  - "Update the PR description with the approved body"
  - "Leave the existing PR as-is"
</mandatory>
If update:
<mandatory>Use the Bash tool to run `gh pr edit --title "approved title" --body` with the approved
PR title and body passed via a HEREDOC.</mandatory>
Note the PR URL. Proceed to Update plan artifact.
If leave as-is: note the existing PR URL. Proceed to Update plan artifact.

**Command failed or returned no PR**: continue to create a new PR below.

</output-handlers>

### Create the PR

<mandatory>Use the Bash tool to run `gh pr create` with the approved title and PR body.
Pass the body via a HEREDOC to preserve formatting. Use this pattern:

```bash
gh pr create --title "approved title" --base [BASE_BRANCH] --body "$(cat <<'EOF'
approved PR body
EOF
)"
```

Substitute the actual approved title and body. Do not use placeholder text.
</mandatory>

<gate>Do not proceed until the PR is created. If creation fails, report the exact error
message and stop.</gate>

Report the PR URL to the user.

Tell the user: "Merge this PR before starting your next feature. Starting a new branch before this is merged will likely cause merge conflicts in the roadmap."

### Update plan artifact

Check whether `.vibe-check/vc-plan/[branch-slug].md` exists using the Read tool.

**Plan artifact found**: use the Edit tool to add `**Shipped:** [PR URL]` on a new line
directly after the `**Status:**` line in the artifact header. If `[failed-coverage-items]`
is non-empty, also add `**Coverage gaps:** auto-generated tests could not cover: [failed-coverage-items list]`
on the following line.

**Plan artifact not found**: note this — the roadmap update below must record the branch as
shipped without a plan.

### Update roadmap

Check whether `.vibe-check/vc-plan/roadmap.md` exists using the Read tool.

**Roadmap exists — row found** (Progress table has a row where Branch matches
`[current-branch-slug]`): use the Edit tool to update that row — set `Built` to `✓`. If
no plan artifact was found, also set Plan status to `no plan`.

**Roadmap exists — no exact match**: before treating this as unplanned, attempt a fuzzy
match. Strip any trailing `-N` suffix from `[current-branch-slug]` (where N is a whole
number) to get the base slug. Search the roadmap for a row whose Branch column matches
the base slug.

- **Fuzzy match found**: ask the user:
  <mandatory>Call AskUserQuestion with:
  - Question: "No exact roadmap row was found for `[current-branch-slug]`. Did you mean the row for `[base-slug]`? (This branch may have been renamed by collision detection.)"
  - Options:
    - "Yes — update that row"
    - "No — this branch was not planned"
  </mandatory>
  If yes: update the matched row — set `Built` to `✓` and update the Branch column to
  `[current-branch-slug]`.
  If no: fall through to the unplanned handler below.

- **No fuzzy match either** (this branch was never planned): use the Edit tool to append a
  new row to both the Features table and the Progress table recording that this branch
  shipped without a plan:
  To derive `[next #]`: count the existing rows in the Features table (not counting the
  header row) and add 1.
  - Features row: `| [next #] | [branch-slug] | unplanned | — | \`[branch-slug]\` | — |`
  - Progress row: `| [branch-slug] | no plan | [branch-slug] | ✓ |`

  After each Edit, use the Read tool to verify the new row appears in the roadmap. If a row
  is missing: re-attempt the Edit once. If it still fails, report the error and show the user
  the exact row text to add manually:
  - Features row: `| [next #] | [branch-slug] | unplanned | — | \`[branch-slug]\` | — |`
  - Progress row: `| [branch-slug] | no plan | [branch-slug] | ✓ |`

**No roadmap exists**: use the Write tool to create `.vibe-check/vc-plan/roadmap.md`:

```
# Project roadmap

**Created:** [today's date]
**Status:** in progress

---

## Features

| # | Feature | Build phase | Depends on | Branch | Plan stub |
|---|---------|------------|-----------|--------|-----------|
| 1 | [branch-slug] | unplanned | — | `[branch-slug]` | — |

---

## Progress

| Feature | Plan status | Branch | Built |
|---------|------------|--------|-------|
| [branch-slug] | no plan | [branch-slug] | ✓ |

---

## How to work on a feature

Run `/vc-plan` from your main branch — it reads this roadmap, offers available features as
options, and creates branches automatically. After planning, implement using the Start here
instruction, then run `/vc-audit` and `/vc-ship`. The roadmap updates automatically when
plans finalize and branches ship.
```

### Commit and push artifact updates

If `.vibe-check/vc-ship/[branch-slug].md` exists: use the Edit tool to update
`**Status:** in progress` to `**Status:** complete`.

After all artifact updates are complete, commit and push them so they are visible in the PR:

```bash
git add .vibe-check/ && git commit -m "chore: update vibe-check artifacts for [branch-slug]" && git push
```
PowerShell: run as three separate commands.

If the push fails: read the error output and attempt to fix the underlying issue (e.g. diverged remote, missing upstream), then retry. If the push still fails after one fix attempt, tell the user the error and instruct them to push manually: `git push`.

</phase>
