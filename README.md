```
         (                          )                  )  
         )\ )   (           (    ( /(         (     ( /(  
 (   (  (()/( ( )\  (       )\   )\()) (      )\    )\()) 
 )\  )\  /(_)))((_) )\    (((_) ((_)\  )\   (((_) |((_)\  
((_)((_)(_)) ((_)_ ((_)   )\___  _((_)((_)  )\___ |_ ((_) 
\ \ / / |_ _| | _ )| __| ((/ __|| || || __|((/ __|| |/ /  
 \ V /   | |  | _ \| _|   | (__ | __ || _|  | (__   ' <   
  \_/   |___| |___/|___|   \___||_||_||___|  \___| _|\_\  
```                                                      

# vibe-check

A suite of Claude Code slash commands that helps you work like a developer — plan before you code, review before you ship, and keep a record of what you built and why.

---

## What is this?

vibe-check is a set of guided workflows you run inside Claude Code. Each command (`/vc-plan`, `/vc-audit`, etc.) walks you through a structured process — asking you questions, reading your code, running git commands — so you can do things the right way without already knowing all the right things.

It is designed for developers who are new to professional software workflows: people building with AI assistance, learning to code, or shipping personal projects and side businesses who want their code to be more stable and maintainable.

### What vibe-check does

- Helps you think through what you are building before you write code
- Creates branches, plans, and roadmap entries automatically
- Reviews your code for bugs, security issues, and missing test coverage
- Scans for accidentally committed secrets before they reach GitHub
- Generates pull requests with useful descriptions for reviewers
- Tracks what shipped and helps you reflect on what you are learning

### What vibe-check does not do

**It is not a substitute for a human code review.** An experienced developer reading your code will catch things these commands miss. If you are building something that handles real money, personal health data, or other sensitive information, you need a qualified human reviewer before going to production.

**It is not a security audit.** `/vc-audit` will find common security issues — injection vectors, hardcoded credentials, missing auth checks — but it does not replace a dedicated security assessment by a security professional. It raises the floor; it does not guarantee the ceiling.

**It does not write your code for you.** These commands help you plan, review, and ship code — but you or Claude still need to do the implementation work.

---

## Installation

### Automated (recommended)

Open your project in Claude Code and say:

> "Fetch and follow the install instructions at https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/install.md"

Claude will download all 6 skill files, update your `CLAUDE.md` with coding standards and a usage guide, and write memory files so it understands the suite in future conversations. When it's done, run `/vc-bootstrap` to finish setup.

### Manual

Copy the `.claude/commands/` directory from this repo into the root of your project. Then run `/vc-bootstrap`.

---

## Commands

### `/vc-bootstrap` — Machine setup

**When to use it:** Run this once when you start using vibe-check on a new machine or a new project. Re-run it if you get a new machine or need to check your setup.

**What it does:**

Checks that git, GitHub CLI, and gitleaks are installed — and installs them for you on macOS and Windows automatically, or attempts the install on Linux/WSL and pauses for you to confirm if sudo requires interaction. Configures your git name and email if they are not set. Authenticates GitHub CLI with step-by-step browser instructions. Adds a security-baseline `.gitignore` to your project that blocks common secret and credential files (`.env`, private keys, Terraform state, Firebase config, etc.) from ever being committed. Writes a summary of everything it set up to `.vibe-check/vc-bootstrap.md`. Ends by telling you exactly what to run next based on whether you have an existing project or are starting fresh.

**Why it's useful:**

Most new developers hit frustrating setup problems — git is not configured, GitHub CLI is not connected, secrets end up in version control. Bootstrap eliminates all of those in one run and makes sure the tooling that the other commands depend on is actually in place before you need it.

---

### `/vc-plan` — Feature planning

**When to use it:** Run it before you write any code for a new feature. Start from your main branch. You can also use it when you are not sure what to build next and want help thinking it through.

**What it does:**

Reads your project context (CLAUDE.md, TODOS.md, existing roadmap) and orients to where you are. Asks whether you want to plan a new feature, pick from your roadmap, or work through an existing plan.

For a new feature, it guides a structured planning conversation: scope calibration, status quo check, narrowest useful version, premise challenge, distribution channel (for client-facing products), approaches, definition of done, risks, failure modes, and security considerations. Then runs an adversarial subagent review of the plan to challenge it. Produces an implementation guide with a copyable "Start here" instruction for Claude to use when you begin coding.

For large initiatives, it decomposes scope into a feature roadmap and creates plan stubs for each feature.

Either way, it creates a branch for you, writes the plan to `.vibe-check/vc-plan/[branch].md`, and registers it in a living roadmap at `.vibe-check/vc-plan/roadmap.md` that tracks every feature across its full lifecycle.

**Why it's useful:**

Jumping straight into code without a plan is the most common reason projects get stuck or produce something that does not work the way you expected. `/vc-plan` forces you to articulate what you are actually building, who it is for, and what done looks like — before you spend hours going the wrong direction. The adversarial review means your plan gets challenged before you commit to it, not after.

---

### `/vc-audit` — Code review

**When to use it:** Run it after finishing the implementation of a feature, before you push. Run it from the feature branch you want to review. You can scope it to a subdirectory (`/vc-audit src/auth/`) for focused sessions.

**What it does:**

Reads the diff between your branch and main, selects the relevant review lenses for what it finds (security, data integrity, error handling, authentication, API contracts, performance, test coverage, and more), and walks every changed file against every applicable lens.

Each finding is recorded in the audit artifact immediately when discovered, with a severity rating, confidence score, the specific lines of code that motivate it, and what it allows or causes. At the end of each pass, the skill goes through every open finding:

- For findings it is confident about, it **applies the fix directly to your source files** using the Edit tool, right in the session.
- For findings where human judgment is needed, it calls a decision prompt — one per finding — asking you to choose: Fix now, Defer, or Dismiss. Dismiss requires a stated reason.

After fixes are applied, it re-reads the full diff and walks every surface again from scratch. It keeps looping until two consecutive passes find zero open findings — that is convergence. The audit artifact accumulates the full history across all passes: what was found, what was fixed, what was deferred, and what was dismissed, with every resolved finding cross-referenced back to its original number.

If adversarial subagents are enabled: after each pass, a second agent with no prior context reviews the same diff independently — its only job is finding what the structured walk missed.

When used after `/vc-onboard` on existing code with no diff, it automatically switches to FILE_READ_MODE and reviews the designated chunk files directly. Supports LARGE_DIFF detection to avoid context exhaustion, and resumes automatically after a long session compacts.

**Why it's useful:**

Code that "works" and code that is ready to ship are different things. `/vc-audit` finds the issues that are easy to miss when you are the person who wrote the code — missing auth checks, unvalidated inputs, error paths that are never handled, tests that do not cover the important cases — and then fixes many of them in the same session. The artifact gives you a paper trail of everything that was reviewed and every decision that was made, which matters when something goes wrong in production.

---

### `/vc-ship` — Push and PR

**When to use it:** Run it when your branch is ready to ship — audit is done, you are satisfied with the implementation, and you want to push to GitHub and open a pull request.

**What it does:**

Runs gitleaks on both your committed diff and any uncommitted changes — if any secrets are detected, it stops immediately before anything reaches GitHub. If gitleaks is not installed, it installs it automatically on macOS and Windows, or attempts the install on Linux/WSL and pauses for you to confirm if sudo requires interaction. You can also choose to skip the scan and proceed without it. Checks for lint configuration and runs your linter; sets up a linter if none is found. Validates test coverage against an 80% goal; if coverage is below that, it writes missing tests automatically and iterates up to three rounds.

Scans the diff for files that look like they should not be committed — build output, dependency directories, OS metadata, log files, temp files — and offers to add them to `.gitignore`. Checks your commit history for non-bisectable patterns (WIP commits, fixups, squash commits) and offers to soft-reset and reorganize them into clean atomic commits.

Checks that a remote is configured; if not, offers to create the GitHub repo via `gh repo create`. Creates the pull request with a description that reviewers can actually use, including a functional testing checklist. Updates the plan artifact and roadmap to mark the branch as shipped.

**Why it's useful:**

Every step of the ship flow is something that trips up developers at some point — accidentally pushing a `.env` file, opening a PR before tests pass, writing a useless PR description, forgetting to update the roadmap. `/vc-ship` does all of that in the right order so you do not have to remember it. The secret scan alone is worth it: credentials in git history are very hard to fully remove once they are pushed.

---

### `/vc-retro` — Retrospective

**When to use it:** Run it at the end of a work session, sprint, or week. Run it from any branch.

**What it does:**

Reads your git history for the period since your last retro (up to 31 days), scoped to your commits as the author. Quantifies what shipped: commit count, active days, which files were touched most often, test coverage signal, and planning discipline (how often you had a plan before you coded). If a previous retro exists within 31 days, loads it to show period-over-period deltas — how commit count, hotspot files, and test coverage changed.

Asks four structured reflection questions, prompts once if you give a non-answer, and writes the full retrospective to `.vibe-check/vc-retro/[date]-[slug].md` so your history travels with the repo.

**Why it's useful:**

Without regular reflection, it is easy to stay in a pattern that is not working without noticing. The quantified history removes the "I feel like I was productive" ambiguity — you can see exactly how many commits shipped, which files kept changing (a signal of instability), and whether you were planning before you coded or just diving in. Period-over-period comparison shows whether things are actually getting better.

---

### `/vc-onboard` — Existing project onboarding

**When to use it:** Run it once on a project that already has code but was started before vibe-check was installed. It maps the existing codebase into feature areas and sets up the planning structure so you can start running the other commands.

**What it does:**

Scans your codebase (excluding dependency and build directories), detects your tech stack, and asks a few questions to understand what the project does. Proposes a breakdown of the codebase into logical feature chunks — self-contained areas like `auth`, `payments`, `api`, `ui` — with a maximum of 15 files per chunk. You confirm or adjust the breakdown before anything is created.

Sets up git if not already initialized, optionally creates a GitHub remote via `gh repo create`, and commits the existing codebase as a baseline. Writes a plan stub for each chunk directly to your main branch and registers each one in the project roadmap. Resumes automatically if the session is interrupted.

After it finishes, you run `/vc-plan` to pick a chunk, create a branch, and start working on it one area at a time.

**Why it's useful:**

Existing codebases are messy to get under control — it is hard to know where to start, and diving into one area while other areas are unknown is risky. `/vc-onboard` gives you the map first. The chunk structure means you can review and stabilize one piece at a time, working systematically through the whole codebase rather than hoping you find the important issues before they become production problems.
