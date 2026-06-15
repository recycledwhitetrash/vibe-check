# /vc-plan

<!-- version: 2026-06-14 -->

The project coordinator for your entire codebase. Run it before writing code to plan a
feature, typically from your main branch to pick up the next thing to build, or when you're not sure
what to build next and want help figuring it out.

For a single feature, it guides a structured conversation — scope calibration, status quo
check, narrowest useful MVP, premise challenge, approaches, definition of done, risks, failure
modes, security, and long-term trajectory — then runs an adversarial review and produces an implementation guide
with a copyable "Start here" instruction for Claude.

For a large initiative or full project, it decomposes the scope into a feature roadmap,
creates a plan stub for each feature, and coordinates the work across branches and sessions.

Either way, every plan is registered in a living roadmap at `.vibe-check/vc-plan/roadmap.md`
that tracks planning and build status across the whole project. The roadmap stores the project
scope classification (internal vs. client-facing) and grows over time — new features are added
as they are planned, branches are marked built when they ship.

Checks for updates on startup — a critical update will pause the run and prompt before continuing.

---

## Version check

Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/versions.json`. If the fetch fails or returns an error for any reason, skip this section entirely and proceed.

<output-handlers>

**Fetch succeeded — `vc-plan` version matches `2026-06-14`**: proceed silently.

**Fetch succeeded — newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /vc-plan is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue.
If Update now: follow the **Auto-update** steps below, then stop.

**Fetch succeeded — newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /vc-plan that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed.

</output-handlers>

**Auto-update:**
1. Run `git --version` to check whether git is installed. If git is not installed, skip the auto-update entirely and proceed to Phase 0 — git will be installed there first.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the WebFetch tool to fetch `https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/vc-plan.md`.
4. If both succeed: use the Write tool to write the fetched content to `[project-root]/.claude/commands/vc-plan.md`. Tell the user "Updated to the latest version. Please re-run /vc-plan." Do not continue.
5. If either fails: tell the user auto-update failed and to update manually at https://github.com/recycledwhitetrash/vibe-check. Do not continue.

---

<protected>
This skill is a conversation, not a black box. Every major conclusion must be
confirmed by the user through an explicit question before it is written to the
artifact. Do not make decisions on behalf of the user and proceed silently.
Present your analysis, then ask.

When you have enough information to proceed, proceed. Do not ask for clarification
on details that can be resolved as work unfolds. 70% certainty is enough to move
forward — the artifact can always be updated.
</protected>

---

<phase id="0" name="orientation">

## Phase 0 — Orientation

Detect the current shell:

```bash
echo $SHELL
```

If the output is a path ending in `bash` or `zsh` (or similar Unix shell): use `&&` to chain
commands throughout this skill. If the output is empty or does not match, you are likely in
PowerShell — run each command as a separate sequential step instead of using `&&` chaining.

### Read project context

Silently attempt to read the following files using the Read tool. Do not report success or
failure to the user — just use what you find to inform later phases:

- `CLAUDE.md` (project root)
- `TODOS.md` (project root)

If either read fails or the file does not exist, continue silently.

Run:

```bash
git branch --show-current
```

```bash
git for-each-ref --format='%(refname:short)' refs/heads/
```

<gate>Do not proceed until you have both command outputs.</gate>

**If `git branch --show-current` returned empty AND `git for-each-ref` returned non-empty output** (branches exist but none is checked out — detached HEAD state): Tell the user: "You are in detached HEAD state — this usually means you checked out a specific commit rather than a branch. Run `git checkout [BASE_BRANCH]` to return to your main branch before planning." Stop here.

**If both commands returned empty output** (no branches exist — brand-new repository with no commits): run `git commit --allow-empty -m "init"` to create the initial commit. Tell the user: "Created an initial commit so branch operations will work — continuing with planning." Then re-run both commands above to get the current branch and branch list, and continue normally.

From the output, identify the current branch name.

Derive BASE_BRANCH using the following priority chain. Stop at the first step that returns a value:

1. Run `git symbolic-ref refs/remotes/origin/HEAD`. If it returns output (e.g. `refs/remotes/origin/main`): strip the `refs/remotes/origin/` prefix directly — do not pipe through shell utilities. Use the result as BASE_BRANCH.
2. Look for a branch in the `git for-each-ref` output whose name is exactly `main`, `master`, or `develop` — partial matches do not count. Use the first match as BASE_BRANCH.
3. If neither step resolves BASE_BRANCH: use the handler below.

Store the resolved value as BASE_BRANCH — this is the branch all features branch from throughout this skill.

<output-handlers>

**If BASE_BRANCH could not be resolved** (steps 1 and 2 above both returned nothing):
<mandatory>Call AskUserQuestion with:
- Question: "vc-plan needs to know which branch your features branch off from. What is the name of your main branch? Recommendation: main — it is the most common default."
- Options:
  - "main" — most common default branch name
  - "master" — older git convention, still common
  - "develop" — used in gitflow-style repos
</mandatory>

**If the current branch IS the default branch:**

Check for a roadmap at `.vibe-check/vc-plan/roadmap.md` using the Read tool, and for any
plan files using the Glob tool to list `.vibe-check/vc-plan/*.md` (exclude `roadmap.md`).

### Project scope

After reading the roadmap (or confirming it does not exist), determine PROJECT_SCOPE:

1. If the roadmap was read successfully: look for a `**Project scope:**` line in the header.
   If found, store its value as PROJECT_SCOPE. Skip the question below and proceed to routing.

2. If no roadmap exists, or if the roadmap exists but has no `**Project scope:**` line:

<mandatory>Call AskUserQuestion with:
- Question: "What type of project is this? Your answer sets the right planning depth and compliance requirements."
- Options:
  - "Internal tooling for me personally"
  - "Internal tooling for multiple users at my company"
  - "Internal tooling that generates client-facing artifacts"
  - "Client-facing product"
</mandatory>

Store the answer as PROJECT_SCOPE.

If the roadmap does not yet exist: use the Write tool to create `.vibe-check/vc-plan/roadmap.md` with a minimal header so PROJECT_SCOPE survives compaction:

```
# Project roadmap

**Created:** [today's date]
**Status:** in progress
**Project scope:** [PROJECT_SCOPE]
**Base branch:** [BASE_BRANCH]
```

Phase 2 will complete the roadmap with features and tables.

If PROJECT_SCOPE is "Internal tooling that generates client-facing artifacts" or
"Client-facing product": tell the user:

> "This project is client-facing and requires additional oversight and permission before
> going live. Please ensure you have the appropriate approvals before deploying.
> *(Alert routing TBD — check with your team lead before launching.)*"

If the roadmap exists but had no `**Project scope:**` line: use the Edit tool to insert
`**Project scope:** [PROJECT_SCOPE]` on a new line after the `**Status:**` line in the
roadmap header.

If the roadmap exists: look for a `**Base branch:**` line in the header.
- If found: use that value as BASE_BRANCH (overrides the derived value — it was set intentionally for this project).
- If not found: use the Edit tool to insert `**Base branch:** [BASE_BRANCH]` on a new line after the `**Status:**` line in the roadmap header.

<output-handlers>

**Roadmap exists and has unbuilt features** (Progress table rows where `Built` is not `✓`):
<mandatory>Call AskUserQuestion with:
- Question: "You are on [branch name]. What would you like to do?"
- Options: one option per unbuilt feature using its Branch slug as the label with its current
  Plan status in parentheses — e.g. "user-auth (stub)" or "workspace-ui (final)". Add two
  final options: "Start a new plan — this is not part of the roadmap" and "Help me figure
  out what to build next — I want to brainstorm"
</mandatory>
If the user picks a roadmap feature: run `git branch --list "[selected-slug]"`.

If the branch already exists:
<mandatory>Call AskUserQuestion with:
- Question: "Found an existing branch `[selected-slug]` for feature '[feature name]'. Is this the right branch to continue work on?"
- Options:
  - "Yes — switch to it"
  - "No — this is a different branch"
</mandatory>
If yes: run `git status --short`. If any uncommitted changes exist:
<mandatory>Call AskUserQuestion with:
- Question: "You have uncommitted changes on `[current-branch]`. Stash them before switching to `[selected-slug]`?"
- Options:
  - "Yes — stash them" (run `git stash` before switching)
  - "No — switch anyway" (user accepts the risk of conflicts)
</mandatory>
If stash: run `git stash`. After checkout succeeds, tell the user: "Your changes on `[current-branch]` have been stashed. When you return to that branch, run `git stash pop` to restore them."
Run `git checkout [selected-slug]`.
If no: ask the user to type a new branch name in Other. Slugify it.

Run `git branch --list "[new-slug]*"` to check for collisions. Only treat as a collision if a branch name is exactly `[new-slug]` or matches `[new-slug]-N` where N is a whole number. If a collision exists, take the highest N and use N+1 to produce `[final-slug]`. Otherwise `[final-slug]` = `[new-slug]`.

Run `git checkout -b [final-slug]`. Confirm they are now on the branch.

Use the Edit tool to update the roadmap row (Branch column: `[selected-slug]` → `[final-slug]`).

Use the Read tool to check whether `.vibe-check/vc-plan/[selected-slug].md` exists.
- If it exists: rename it to `.vibe-check/vc-plan/[final-slug].md` — use `mv` in bash/zsh or `Move-Item` in PowerShell.
- If it does not exist: skip the rename and tell the user: "No stub file was found for `[selected-slug]` — a new stub will be created when you reach the artifact step."

If the branch does not exist: run `git checkout -b [selected-slug]`. Confirm they are now on
the branch.

Before continuing to Phase 1, use the Read tool to check `.vibe-check/vc-plan/[selected-slug].md`.
If the file contains a `## Chunk files` section, this is an onboard chunk — the plan stub was
pre-written by `/vc-onboard`. Do not run the planning flow. Tell the user:

> Branch `[selected-slug]` is ready. The plan stub was pre-written by `/vc-onboard` and contains
> the file list for this chunk. Run `/vc-audit` to start the audit.

Stop here — do not continue to Phase 1 or beyond.

Otherwise: Phase 1 will read the plan and resume from the correct point.
If the user picks "Start a new plan": proceed to Phase 1.
If the user picks "Help me figure out what to build next": jump to **Brainstorm path** below.

**Roadmap exists but all features are built**: tell the user all roadmap features are
complete, then:
<mandatory>Call AskUserQuestion with:
- Question: "All roadmap features are complete. What would you like to do?"
- Options:
  - "Start a new plan — add a new feature"
  - "Help me figure out what to build next — I want to brainstorm"
</mandatory>
If start new plan: proceed to Phase 1.
If brainstorm: jump to **Brainstorm path** below.

**No roadmap, plan files exist**: these are plans from prior sessions without a roadmap.
<mandatory>Call AskUserQuestion with:
- Question: "You are on [branch name]. Which branch are you starting? Pick an existing plan or start a new one."
- Options: one option per file found using the filename stem (without `.md`) as the label.
  Add two final options: "Start a new plan" and "Help me figure out what to build next — I want to brainstorm"
</mandatory>
If the user picks an existing plan: run `git branch --list "[selected-slug]"`. If the branch
already exists, run `git checkout [selected-slug]` to switch to it. If it does not exist, run
`git checkout -b [selected-slug]` to create it. Confirm they are now on the branch. Phase 1
will handle the existing plan.
If the user picks "Start a new plan": proceed to Phase 1.
If the user picks "Help me figure out what to build next": jump to **Brainstorm path** below.

**No roadmap, no plan files exist:**
<mandatory>Call AskUserQuestion with:
- Question: "No plans exist yet for this project. How would you like to start?"
- Options:
  - "Start a new plan — I know what I want to build"
  - "Help me figure out what to build — I want to brainstorm"
</mandatory>
If start new plan: proceed to Phase 1.
If brainstorm: jump to **Brainstorm path** below.

</output-handlers>

**If the current branch is NOT the default branch:**

Run:

```bash
git log --oneline -10
```

If the output shows commits on this branch: note the count. Include it in the question below
so the user is aware of existing work before deciding whether to continue on this branch or
start fresh.

<mandatory>Call AskUserQuestion with:
- Question: "You are currently on `[current-branch]`[, which has [N] recent commit(s)]. Is this the branch you want to plan for, or do you want to start a new feature?"
- Options:
  - "Yes — plan for [current-branch]"
  - "Start a new feature instead"
</mandatory>
If yes:
Read the roadmap at `.vibe-check/vc-plan/roadmap.md` using the Read tool.
- If it exists and has a `**Project scope:**` line: store its value as PROJECT_SCOPE.
- If it exists and has a `**Base branch:**` line: use that value as BASE_BRANCH.
- If it exists but has no `**Base branch:**` line: use the Edit tool to insert `**Base branch:** [BASE_BRANCH]` on a new line after the `**Status:**` line in the roadmap header.
- If it does not exist or has no `**Project scope:**` line: PROJECT_SCOPE will be resolved in Phase 2.
Continue to Phase 1.

If new feature:
Run `git status --short`. If any uncommitted changes exist:
<mandatory>Call AskUserQuestion with:
- Question: "You have uncommitted changes on `[current-branch]`. Stash them before switching to [BASE_BRANCH]?"
- Options:
  - "Yes — stash them" (run `git stash` before switching)
  - "No — switch anyway" (user accepts the risk of conflicts)
</mandatory>
If stash: run `git stash`, then proceed with checkout. After the checkout succeeds, tell the user: "Your changes on `[current-branch]` have been temporarily saved (stashed) — they are not lost, just parked. Run `git stash pop` on that branch when you want them back."
- bash/zsh: `git checkout [BASE_BRANCH] && git pull origin [BASE_BRANCH]`
- PowerShell: run as two separate commands: `git checkout [BASE_BRANCH]` then `git pull origin [BASE_BRANCH]`
If the pull fails: continue with a warning — "Could not pull latest from origin — proceeding with local state."
Proceed to Phase 1.

</output-handlers>

### Brainstorm path

*Only runs when the user picks the brainstorm option from a routing question above.*

Ask the following directly in your response text (not via AskUserQuestion):

"Are you thinking of a new feature for your existing project, or a new project entirely?"

Wait for the user's response. Then ask one open-ended question at a time to help them
surface what to build. Aim for 2–4 questions — enough to land on a concrete idea, not
a full interrogation. Good starting questions depending on context:

- "What's something you find yourself doing repeatedly that feels like it should be faster or automated?"
- "What's the last thing you built that made you think 'this could be even better if...'?"
- "What's taking up the most time in your current workflow that you haven't fixed yet?"
- "If you could add one thing to this project, what would make it most useful to you?"

Once the user lands on a concrete idea: confirm it back in one sentence —
"So you want to build [X] — [brief description]. Does that capture it?"

Wait for confirmation, then continue to Phase 1 with that as the starting problem statement.

</phase>

---

<phase id="1" name="problem-capture">

## Phase 1 — Problem capture

**If the current branch is the default branch** (identified in Phase 0): no artifact exists yet —
the branch will be created during Phase 2. Skip the artifact check below and proceed directly
to the problem question at the end of this phase.

**Otherwise**, check whether a plan artifact already exists for this branch:

1. Run `git branch --show-current` to get the current branch name.
2. Slugify the branch name: lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens. This is the branch slug.
3. Artifact path: `.vibe-check/vc-plan/[branch-slug].md`
4. Use the Read tool to check whether the artifact exists at that path.

<gate>Do not proceed until you have checked for an existing artifact.</gate>

<output-handlers>

**If the artifact exists:**
Read it using the Read tool. Present a brief summary of the existing plan to the user.

<mandatory>Call AskUserQuestion with:
- Question: "A plan for this branch already exists. Updating preserves your previous thinking and picks up where you left off. Starting fresh loses the existing plan entirely. What would you like to do?"
- Options:
  - "Review and update the existing plan — keep what still applies, revise what changed" (Recommended if the original intent is mostly intact)
  - "Start fresh — the plan has changed enough that the old one is not useful"
</mandatory>

If updating: read the existing artifact. Present a one-line summary of each section's state — "complete," "in progress," or "stub placeholder." Then ask the user directly in your response text (not via AskUserQuestion): "Which section would you like to pick up from? The sections are: Premises, Problem / Goal, Direction, Approaches, Not in scope, Definition of done, Risks, Failure modes & security, Long-term trajectory." Wait for their answer, then jump to that phase. If starting fresh: continue below.

**If the artifact does not exist:** Continue below.

</output-handlers>

Ask the user to describe what they're planning to build or fix. This is the opening of the
conversation — keep it open-ended and low pressure. If the user arrived via the Brainstorm
path, their idea is already captured — confirm it briefly and proceed to Phase 2.

<mandatory>Ask the following directly in your response text (not via AskUserQuestion — this is a free-form opening):

"What problem are you solving, or what are you trying to build? Describe it in your own words — no need for technical detail yet."

Then wait for the user's response before continuing to Phase 2.
</mandatory>

</phase>

---

<phase id="2" name="discovery-and-premise-challenge">

## Phase 2 — Discovery and premise challenge

### Planning assistance

<mandatory>Call AskUserQuestion with:
- Question: "Would you like to work through some planning questions first, or go straight to scoping and building the plan stub?"
- Options:
  - "Help me think it through — walk me through the planning questions" (Recommended for new or uncertain features)
  - "Skip — I know what I want, let's go straight to scoping"
</mandatory>

If skip: jump to **Scope assessment** below — skip discovery and premise sections, but scope must still be assessed before branch creation.

---

### Discovery questions

*Only run if the user chose "Help me think it through."*

#### Scope calibration

Ask the following directly in your response text (not via AskUserQuestion):

"Roughly how often would you use this once it's built? And how long do you think it
will take to build?"

Wait for the user's response. If the ratio looks significantly off — for example, several
hours of build time to save only a few minutes per week — surface the math gently:

"That's about [X] of build time for [Y] saved per week — you'd break even after roughly
[N] uses. Is there a smaller first version that captures most of the value and gets you
something to use faster?"

Do not block progress. Surface the observation and let the user decide.

#### Pain point and problem framing

Ask the following directly in your response text (not via AskUserQuestion):

"Is this your biggest time drain right now, or is there something else you're spending
more time on? And — is there an existing tool, setting, or quick script that might
already handle this, even partially?"

Wait for the user's response. If they identify a higher-value problem: offer to switch
focus to that instead. If they confirm this is the right target: continue.

#### Status quo

Ask the following directly in your response text (not via AskUserQuestion):

"What are you doing right now to handle this? Walk me through the current process, even
if it's rough."

Wait for the user's response.

- If the current process is fragile, manual, or error-prone: tell the user this is a
  strong candidate for automation — a good tool should make this significantly faster
  and less error-prone.
- If the current process is functional: note that the solution needs to be meaningfully
  easier or faster than the current path to be worth the build time.

#### Narrowest useful version

Ask the following directly in your response text (not via AskUserQuestion):

"What's the smallest version of this that would still be genuinely useful on its own —
something you could put into use right away and learn from before building more?"

Wait for the user's response. Use this answer to scope the plan: the stub should reflect
this smaller version, not the full eventual vision.

---

### Premise challenge

Based on the user's description (and discovery answers, if they ran), identify 2–4 key
assumptions or framings behind this plan. Present them as numbered premises all at once
in your response text:

```
PREMISES:
1. [stated or implied assumption about the problem or goal] — do you agree?
2. [assumed constraint or technical approach] — do you agree?
3. [inferred scope or definition of success] — do you agree?
```

Wait for the user's response to all premises.

If the user disagrees with any premise: update your understanding accordingly, note the
revision, and reflect the corrected framing back in one sentence. You may loop once if a
disagreement changes the problem framing significantly.

These agreed (or revised) premises will be written into the plan stub. If a plan artifact already exists (the update path): use the Edit tool to replace the content of the `## Premises` section with the agreed premises.

### 12-month direction

Once the premises are confirmed, ask the user to look further out. Ask the following directly
in your response text (not via AskUserQuestion):

"Looking further out: if this goes well and you keep building on it, what does this look like
in 12 months? Describe it briefly — even a rough picture is useful."

Wait for the user's response. If they say they don't know, skip it, or give a non-answer,
follow up once: "Even a rough picture helps — what would you hope to be true about this in a
year?" If still no meaningful answer, treat the 12-month direction as "Not defined — scope
limited to this branch." and use that when writing the artifact.

### Scope assessment

Before writing the artifact, assess whether this is a single feature or a full project.

A **multi-feature initiative** has 3 or more distinct user-facing capabilities that each represent meaningful standalone work — for example: adding multi-tenancy to an existing app (workspace isolation, tenant auth, workspace UI, billing per tenant are all separate), or building a new product from scratch. A **single feature** is one cohesive change, even if large or technically complex.

Signals this is a multi-feature initiative:
- The user described 3 or more distinct user-facing capabilities — this alone is sufficient to trigger decomposition
- A large cross-cutting change on an existing codebase that touches multiple systems (e.g., adding multi-tenancy, overhauling auth, introducing a new billing model)
- "Build [app / product / platform / tool] from scratch" framing
- The 12-month direction looks like what they are building right now, not a future extension
- No existing codebase — everything needs to be created

If this is a multi-feature initiative:

<mandatory>Call AskUserQuestion with:
- Question: "This looks like a multi-feature initiative — too large for a single branch or audit pass. I can break it into a feature roadmap with a plan stub for each feature. Each stub pre-loads the problem, dependencies, and relevant existing code so that running /vc-plan on the feature branch picks up at the approaches phase with context already loaded. Or you can continue as a single plan and narrow the scope in the approaches phase."
- Options:
  - "Break it down — create a feature roadmap" (Recommended)
  - "Continue as a single plan — I will scope it in Phase 3"
</mandatory>

If break it down: skip the artifact stub and all remaining phases. Jump to the **Project decomposition** section at the end of this skill.
If continue as single plan: proceed to write the artifact stub below.

### Create your feature branch

<output-handlers>

**If the current branch is the default branch** (either started here, or the user chose "Start a
new feature" on a non-default branch and was switched back to main in Phase 0): create the
feature branch now.

Generate 2–3 short descriptive branch slugs from the confirmed problem statement. They should
be lowercase, hyphen-separated, 2–4 words — for example: `add-user-auth`, `fix-session-timeout`,
`migrate-to-postgres`.

<mandatory>Call AskUserQuestion with:
- Question: "What would you like to name this branch? Pick one of these suggestions or type your own in Other."
- Options: [the 2–3 generated slugs]
</mandatory>

Take the chosen slug (or the value from Other if the user typed their own). Slugify it:
lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive
hyphens, strip leading/trailing hyphens. This is `[branch-slug]`.

If the slug was derived from a user-typed "Other" value: show the derived slug and ask for confirmation before creating the branch: "Your branch will be named `[final-slug]` — does that look right?" If yes: proceed. If they want a different name: ask them to type it, re-slugify, and show the result again before proceeding.

Run `git branch --list "[branch-slug]*"` to check for collisions. Only treat as a collision if
a branch name is exactly `[branch-slug]` or matches `[branch-slug]-N` where N is a whole number.
If a collision exists, take the highest matching N and append N+1 to produce the final slug.

Run `git status --short`. If uncommitted changes exist:
<mandatory>Call AskUserQuestion with:
- Question: "You have uncommitted changes on [BASE_BRANCH] — these will carry over to the new branch `[final-slug]`. Carrying them over means those edits will be part of this feature branch (useful if the changes belong to this feature). Stashing them keeps [BASE_BRANCH] clean and leaves the changes parked until you need them. What would you like to do?"
- Options:
  - "Carry them over — these changes belong to this feature branch"
  - "Stash them — keep [BASE_BRANCH] clean, I'll decide later"
</mandatory>
If stash: run `git stash`. After the branch is created, tell the user: "Your changes on [BASE_BRANCH] have been temporarily saved (stashed) — they are not lost, just parked. Run `git stash pop` if you want to restore them on this new branch."

Run `git checkout -b [final-slug]`.
<gate>Do not proceed until the branch is created. Confirm to the user: "You are now on branch `[final-slug]`."</gate>

Update `[branch-slug]` to `[final-slug]` — all subsequent steps use this for artifact paths.

**If the current branch is NOT the default branch**: the branch was confirmed in Phase 0 (either
selected from the roadmap, or the user confirmed it as the correct branch). Run
`git branch --show-current`, then slugify: lowercase, replace any character that is not
alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens.
This is `[branch-slug]` for all subsequent steps.

</output-handlers>

### Write artifact stub

If PROJECT_SCOPE has not been set by this point:

<mandatory>Call AskUserQuestion with:
- Question: "What type of project is this? Your answer sets the right planning depth and compliance requirements."
- Options:
  - "Internal tooling for me personally"
  - "Internal tooling for multiple users at my company"
  - "Internal tooling that generates client-facing artifacts"
  - "Client-facing product"
</mandatory>

Store the answer as PROJECT_SCOPE.

If PROJECT_SCOPE is "Internal tooling that generates client-facing artifacts" or
"Client-facing product": tell the user:

> "This project is client-facing and requires additional oversight and permission before
> going live. Please ensure you have the appropriate approvals before deploying.
> *(Alert routing TBD — check with your team lead before launching.)*"

<mandatory>Use the Write tool to create the artifact at `.vibe-check/vc-plan/[branch-slug].md` with the following content:

```
# Plan: [branch-slug]

**Branch:** [full branch name]
**Date:** [today's date]
**Status:** draft

---

## Premises

[If discovery was run: numbered list of agreed premises from the premise challenge.
 If the user skipped discovery: "Skipped — user proceeded directly to scoping."]

---

## Problem / Goal

[confirmed problem statement in 2–4 sentences — scoped to the narrowest useful version
 if discovery was run]

---

## Direction

| | |
|---|---|
| **This branch** | [one sentence: what this plan delivers] |
| **12 months** | [user's answer to the 12-month question, or "Not defined — scope limited to this branch."] |

---

## Approaches

*In progress*

---

## Not in scope

*In progress*

---

## Definition of done

*In progress*

---

## Risks

*In progress*

---

## Failure modes & security

*In progress*

---

## Long-term trajectory

*In progress*
```
</mandatory>

The Write tool creates parent directories automatically.

### Update roadmap

Every plan — whether standalone or part of a larger initiative — is registered in the
project roadmap so it is always the source of truth for all planning.

Derive a short feature name from the confirmed problem statement (3–5 words, title-cased).

Check whether `.vibe-check/vc-plan/roadmap.md` exists using the Read tool.

**If the roadmap exists and has a `## Features` table**: use the Read tool to read the current Features table and identify the highest row number. Use that number + 1 as `[next #]`. Then use the Edit tool to append one row to the Features table and one row to the Progress table:
- Features row: `| [next #] | [feature name] | standalone | — | \`[branch-slug]\` | \`.vibe-check/vc-plan/[branch-slug].md\` |`
- Progress row: `| [feature name] | draft | [branch-slug] | — |`

After each Edit, use the Read tool to verify the new row appears in the file. If a row is
missing, re-attempt the Edit once. If it still fails, tell the user and provide the exact row
text to add manually.

**If the roadmap exists but has no `## Features` table** (header written during Phase 0): use the Edit tool to append the following after the existing header:

```
---

## Features

| # | Feature | Build phase | Depends on | Branch | Plan stub |
|---|---------|------------|-----------|--------|-----------|
| 1 | [feature name] | standalone | — | `[branch-slug]` | `.vibe-check/vc-plan/[branch-slug].md` |

---

## Progress

| Feature | Plan status | Branch | Built |
|---------|------------|--------|-------|
| [feature name] | draft | [branch-slug] | — |

---

## How to work on a feature

Run `/vc-plan` from your main branch — it reads this roadmap, offers available features as
options, and creates branches automatically. After planning, implement using the Start here
instruction, then run `/vc-audit` and `/vc-ship`. The roadmap updates automatically when
plans finalize and branches ship.
```

After the Edit, use the Read tool to verify the `## Features` table appears. If it does not, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

**If no roadmap exists**: use the Write tool to create `.vibe-check/vc-plan/roadmap.md`:

```
# Project roadmap

**Created:** [today's date]
**Status:** in progress
**Project scope:** [PROJECT_SCOPE]
**Base branch:** [BASE_BRANCH]

---

## Features

| # | Feature | Build phase | Depends on | Branch | Plan stub |
|---|---------|------------|-----------|--------|-----------|
| 1 | [feature name] | standalone | — | `[branch-slug]` | `.vibe-check/vc-plan/[branch-slug].md` |

---

## Progress

| Feature | Plan status | Branch | Built |
|---------|------------|--------|-------|
| [feature name] | draft | [branch-slug] | — |

---

## How to work on a feature

Run `/vc-plan` from your main branch — it reads this roadmap, offers available features as
options, and creates branches automatically. After planning, implement using the Start here
instruction, then run `/vc-audit` and `/vc-ship`. The roadmap updates automatically when
plans finalize and branches ship.
```

</phase>

---

<phase id="3" name="approaches">

## Phase 3 — Approaches and scope boundary

### Codebase check

Before generating approaches, check whether any of this already exists. Use the Grep
and Glob tools to search the codebase for existing code related to the problem — look
for file names, function names, class names, or patterns that suggest related
functionality.

If the codebase is empty or this is a brand new project: skip this check and note
"New project — no existing code to check."

If relevant existing code is found: summarize what exists. When presenting this to the
user, emphasize the DRY principle — building on or extending existing code keeps the
codebase consistent and avoids duplication:

<mandatory>Ask the following directly in your response text (not via AskUserQuestion):

"Here's what I found that might be relevant: [summary]. Building on this existing code
keeps things consistent and avoids duplication — does any of this change how you want
to approach the problem, or should I generate approaches assuming we're building from
scratch?"

Wait for the user's response before generating approaches.
</mandatory>

If no relevant code is found: proceed directly to approaches without interrupting.

### Distribution channel

*Only run if PROJECT_SCOPE is not "Internal tooling for me personally."*

Ask the following directly in your response text (not via AskUserQuestion):

"How will the people who need this get access to it? For example: a shared script or
CLI they run manually, a package or library they install, an internal web app, an API
service, or something else?"

Wait for the user's response. Then use the Edit tool to add a Distribution section to
the plan stub, inserted after the Direction section:

```
## Distribution

**How users get this:** [user's answer]
```

After the Edit, use the Read tool to verify the `## Distribution` section appears in the file. If it is missing, re-attempt the Edit once. If it still fails, tell the user and provide the exact text to add manually after the Direction section.

### Generate approaches

Generate 2–3 distinct implementation approaches for the confirmed problem. Approaches
should be genuinely different — not variations of the same idea. Always include:
- One **minimal** approach: fewest files, smallest change, gets the job done
- One **ideal architecture** approach: best long-term structure, even if more work

For each approach:
- **Name** — a short label (3–6 words)
- **Description** — 2–3 sentences on how it works
- **Tradeoff** — what it costs vs. what it gains (be specific)
- **Reversibility** — is this a one-way door (hard to change course later) or a two-way door (easy to revise)? When approaches are otherwise equal, prefer the two-way door.

If the scope is small and the right approach is obvious from the problem description and
codebase check, you may skip the full approaches exercise — proceed directly to the
subtraction pass with a one-sentence note explaining why.

Present all approaches clearly in your response before asking the user to choose. Include your recommendation and why.

<mandatory>Call AskUserQuestion with:
- Question: "This is the most consequential decision in the plan — changing direction after coding starts means throwing away work. Which approach do you want to take? Recommendation: [state which approach you would recommend and one-line reason]."
- Options: one option per approach, with the description field summarizing the key tradeoff as a single sentence
  (User can select Other to describe their own approach or a hybrid)
</mandatory>

If the user selects Other or describes a hybrid: ask one follow-up question in plain text to confirm you understand the approach before continuing.

### Subtraction pass

Once the approach is confirmed, apply subtraction thinking: what parts of this approach could be removed without losing the core value? Are there components that are nice-to-have but not essential for the first version? Present your assessment in 2–3 sentences, then ask:

<mandatory>Call AskUserQuestion with:
- Question: "Before locking in scope: is there anything in this approach that could be cut or deferred to a follow-up branch without losing what matters most? Recommendation: cut anything that can ship separately — smaller branches are easier to review and less risky."
- Options:
  - "Keep the full approach as described — nothing to cut" — scope is right as-is
  - "Cut or defer something" — describe what to remove or defer in Other
  - "I want to think about this — let me describe a slimmer version" — type your slimmed scope in Other
</mandatory>

Incorporate any scope reductions before continuing.

### Scope check

Based on the confirmed approach and any scope reductions, estimate:
- How many files is this work expected to touch?
- How many new components, services, or classes does it introduce?

If the answer is more than 8 files or more than 2 new major components, the scope may
be too large for a single branch. Large branches are harder to review, riskier to
merge, and more likely to create conflicts.

Note: this estimate is based on the plan description before any code is written — actual
scope may be smaller or larger once implementation begins. If it turns out the branch is
bigger or smaller than expected, the user can revisit this decision at any time.

If the scope looks too large:
<mandatory>Call AskUserQuestion with:
- Question: "Based on the plan description, this looks like it may be too large for a single branch — estimated [N] files touched and [N] new components introduced. This is a rough estimate and may change once coding starts, but large PRs get worse reviews and carry more merge risk. Would you consider splitting this into smaller branches? Recommendation: split if you can identify a natural boundary — the first branch unblocks the second."
- Options:
  - "Keep it as one branch — the scope is intentional" — proceed as planned
  - "Split it — help me define the boundary" — discuss how to divide the work into two branches
  - "Let me think about what to cut" — return to the subtraction pass
</mandatory>

If the user wants to split: help them identify a natural first-branch boundary (what must ship first to unblock the rest?). Recommend running `/vc-plan` again on the smaller scope. Do not continue with the current plan until scope is confirmed.

If the scope looks right-sized: continue without interrupting.

### Define the boundary

Ask the user to state what's explicitly NOT in scope for this branch. This prevents scope creep and gives reviewers a clear picture of intentional boundaries.

<mandatory>Ask the following directly in your response text (not via AskUserQuestion):

"What is explicitly NOT part of this branch? List anything that is related but intentionally out of scope — things someone might expect to be included but won't be."

Wait for the user's response.
</mandatory>

### Update artifact

If approaches were skipped (scope was small and the right approach was obvious): use the Edit tool to replace the `*In progress*` placeholder in the Approaches section with a brief note:

```
**Approach:** [one sentence on the chosen direction — why it was obvious from the problem description]
**Selected:** [selected approach name]
```

After the Edit, use the Read tool to verify the Approaches section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

Otherwise:

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Approaches section with:

```
### [Option A name]
[description]
**Tradeoff:** [what it costs vs. gains]
**Reversibility:** [one-way / two-way door — one sentence]

### [Option B name]
[description]
**Tradeoff:** [what it costs vs. gains]
**Reversibility:** [one-way / two-way door — one sentence]

### [Option C name] *(if applicable)*
[description]
**Tradeoff:** [what it costs vs. gains]
**Reversibility:** [one-way / two-way door — one sentence]

**Selected:** [selected approach name] — [one sentence on why]
```
</mandatory>

After the Edit, use the Read tool to verify the Approaches section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Not in scope section with the user's answer as a bulleted list. If the user listed reasons, include them. If the list is empty, write: "None stated."</mandatory>

After the Edit, use the Read tool to verify the Not in scope section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

</phase>

---

<phase id="4" name="definition-of-done">

## Phase 4 — Definition of done

Based on the selected approach, propose a definition of done as a checklist of specific, testable criteria. Each item must describe an observable outcome — not a task.

- Bad: "implement authentication"
- Good: "a user can log in with email and password and receive a session token"

Include at least one criterion for edge cases: what does done look like when inputs are empty, missing, or malformed? What does the user see when an operation fails? A feature that only handles the happy path is not done.

Write 3–6 criteria and present them to the user.

<mandatory>Call AskUserQuestion with:
- Question: "Vague done criteria lead to scope creep and shipping incomplete work. Observable, testable criteria mean you will know exactly when you are done. Does this definition of done cover everything? Recommendation: if the criteria match your mental model of what shipped looks like, go with the first option."
- Options:
  - "Looks complete — use this as-is" — the criteria accurately describe what done looks like for this branch
  - "A few adjustments needed" — mostly right but something needs to change; describe in Other
  - "Something important is missing" — a key outcome is not captured; describe what is missing in Other
</mandatory>

If the user wants adjustments: ask them to describe the changes in plain text, then incorporate them.

Once the criteria are confirmed, update the artifact's Definition of done section:

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Definition of done section with the confirmed checklist:

```
- [ ] [criterion]
- [ ] [criterion]
...
```
</mandatory>

After the Edit, use the Read tool to verify the Definition of done section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

### Test planning

Ask the user what tests they plan to write. This is lightweight — not a full test plan,
just enough to confirm testability is being considered before a line of code is written.

<mandatory>Ask the following directly in your response text (not via AskUserQuestion):

"What tests are you planning to write for this? At minimum: one test for the happy
path and one for a failure case. Are there any edge cases from the done criteria
that need their own tests?"

Wait for the user's response.
</mandatory>

Add the test criteria to the artifact as additional items in the Definition of done
checklist:

<mandatory>Use the Edit tool to append the user's test criteria to the existing
Definition of done checklist. Format each as:

```
- [ ] Test: [what the test covers]
```

If the user states that tests are not applicable (config-only change, docs, infra, or similar):
add a single pre-checked item instead: `- [x] Test: N/A — [user's stated reason]`

If the user says they are not writing tests or does not have an answer, add a
single item: `- [ ] Test: happy path and at least one failure case covered`
</mandatory>

After the Edit, use the Read tool to verify the test criteria were appended to the Definition of done checklist. If the section is unchanged, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

</phase>

---

<phase id="5" name="risks">

## Phase 5 — Risks

Based on the selected approach and definition of done, identify the top risks. Use inversion thinking: rather than only asking "what could go wrong?", also ask "what would need to be true for this to fail completely?" The answers to the second question often surface risks the first misses.

Consider:

- **Technical risks** — unknowns, dependencies, or areas where the approach might not work
- **Scope risks** — things that could expand the work unexpectedly
- **Integration risks** — how this interacts with existing code, APIs, or systems

Present the risks as a table and explain briefly why each one matters.

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [risk] | Low / Med / High | Low / Med / High | [what to do if it happens] |

<mandatory>Call AskUserQuestion with:
- Question: "Unacknowledged risks become surprises mid-development. Knowing them now means you can plan around them or decide they are acceptable. Are there risks missing from this list, or any you would remove or adjust? Recommendation: if the list feels complete, go with the first option."
- Options:
  - "This covers it — move on" — the risk table is accurate and complete
  - "Add one or more risks" — something is missing; describe the additional risks in Other
  - "Remove or adjust something" — a risk is wrong, overstated, or needs a better mitigation; describe in Other
</mandatory>

If the user adds or adjusts: incorporate the changes.

If the user selects "This covers it" but the risk table has zero data rows: do not proceed.
Generate 2–3 risk suggestions specific to this plan's approach and problem statement.
Present them in plain text and ask: "Every non-trivial feature has at least one risk —
here are a few that apply to this plan. Would you like to add any of these?" Let the user
pick which to include (or type their own in Other), then add the selected risks to the table
before continuing.

Once risks are confirmed, update the artifact's Risks section:

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Risks section with the confirmed table.</mandatory>

After the Edit, use the Read tool to verify the Risks section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

</phase>

---

<phase id="6" name="failure-modes-and-security">

## Phase 6 — Failure modes and security

### Failure modes

For each main operation this plan introduces, work through how it can fail. At planning stage you don't need full exception class names — but you do need to confirm nothing fails silently.

For each operation, identify:
- **Failure path** — what happens when the operation fails?
- **Visibility** — does it fail loudly (user sees an error) or silently (nothing happens, no feedback)?
- **Partial success** — can it partially succeed and leave data in an inconsistent state?
- **User impact** — what does the user see or experience when it fails?

Present this as a table:

| Operation | Failure path | Silent? | User sees |
|-----------|-------------|---------|-----------|
| [operation] | [how it fails] | Yes / No | [message or outcome] |

Silent failures — where something goes wrong and the user has no idea — are always a problem. Flag any as gaps that need to be addressed.

### Security considerations

Check these four things for this plan:

1. **New attack surface** — does this add inputs, endpoints, file paths, or background jobs that could be abused?
2. **Data access** — does this touch user data or credentials? Is access scoped to the right user?
3. **Authorization** — who can do what this creates? Could one user accidentally access another's data?
4. **New dependencies** — are any new libraries or external services being added? Any known security concerns with them?

Present your findings briefly. If nothing applies ("this is a read-only internal tool with no new inputs"), say so clearly.

<mandatory>Call AskUserQuestion with:
- Question: "Are there failure modes or security concerns we have not addressed? Recommendation: if the tables above look complete and no silent failures are flagged, go with the first option."
- Options:
  - "Looks complete — move on" — failure modes and security considerations are covered
  - "There is a failure mode we missed" — describe it in Other
  - "There is a security concern we missed" — describe it in Other
</mandatory>

If the user adds items: incorporate them.

If the user selects "Looks complete" but the failure modes table has zero data rows: do not
proceed. Generate 2–3 failure mode suggestions specific to the operations this plan introduces.
Present them in plain text and ask: "Every feature that does something can fail — here are a
few failure modes that apply here. Would you like to add any of these?" Let the user pick which
to include (or type their own in Other), then add the selected rows to the table before
continuing.

Once confirmed, update the artifact's Failure modes & security section:

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Failure modes & security section with the confirmed content. Use the table format above for failure modes, followed by a short Security considerations paragraph or bullet list.</mandatory>

After the Edit, use the Read tool to verify the Failure modes & security section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

</phase>

---

<phase id="7" name="long-term-trajectory">

## Phase 7 — Long-term trajectory

Based on the selected approach, assess the long-term implications of this work.

**Reversibility** — rate 1–5:
- 5: Easily changed or reversed — no lasting consequences if this turns out to be wrong
- 3: Moderate effort to change — some rework required but not catastrophic
- 1: One-way door — extremely hard to reverse; commits the project to this direction

**Technical debt** — what shortcuts, compromises, or assumptions does this approach introduce that will need to be revisited later? Be specific — "this is fine for now but assumes X" is more useful than "some tech debt."

**Path dependency** — does this make future work easier or harder? Does it open up future capabilities, or does it close off options?

**What comes next** — if this ships and works well, what would a natural Phase 2 look like? What becomes possible that wasn't before?

Present your assessment in plain language, then ask:

<mandatory>Call AskUserQuestion with:
- Question: "Does this trajectory assessment match how you are thinking about this work? Recommendation: if the reversibility score and debt assessment feel accurate, go with the first option."
- Options:
  - "Yes, this looks right — finalize the plan" — assessment is accurate
  - "The reversibility is different than you described" — explain in Other
  - "There is debt or a constraint you missed" — describe in Other
</mandatory>

If the user adjusts: incorporate the changes.

Once confirmed, update the artifact's Long-term trajectory section and finalize the artifact:

<mandatory>Use the Edit tool to replace the `*In progress*` placeholder in the Long-term trajectory section with:

```
**Reversibility:** [N/5] — [one sentence on why]

**Technical debt introduced:** [description, or "None identified"]

**Path dependency:** [does this make future changes easier or harder, and how]

**What comes next:** [description of a natural Phase 2, or "None identified"]
```
</mandatory>

After the Edit, use the Read tool to verify the Long-term trajectory section no longer contains `*In progress*`. If it does, re-attempt once. If it still fails, tell the user and provide the exact text to add manually.

<mandatory>Use the Read tool to check the current value of `**Status:**` in the artifact.

If it is `draft`: use the Edit tool to change `**Status:** draft` to `**Status:** final`. After the Edit, use the Read tool to verify `**Status:** final` appears in the artifact. If it does not, re-attempt once. If it still fails, tell the user and provide the exact line to replace manually.

If it starts with `stub`: use the Edit tool to replace the entire `**Status:** stub...` line (whatever it says after `stub`) with `**Status:** final`. After the Edit, use the Read tool to verify `**Status:** final` appears in the artifact. If it does not, re-attempt once. If it still fails, tell the user and provide the exact line to replace manually.

If it is already `final`: check whether a `**Last updated:**` line exists in the artifact header. If it does: use the Edit tool to update it to `**Last updated:** [today's date]`. If it does not: use the Edit tool to insert `**Last updated:** [today's date]` on a new line immediately after the `**Status:** final` line.</mandatory>

</phase>

---

<phase id="8" name="adversarial-review">

## Phase 8 — Adversarial review

The plan is written. Before declaring it complete, dispatch a subagent to read it with fresh context and find problems the conversation may have missed.

<mandatory>Use the Agent tool to dispatch a reviewer subagent. The subagent has no context from this conversation — it reads only the artifact. Prompt it with:

"Read the plan document at [artifact path]. Review it on these 5 dimensions. For each dimension, output PASS or list specific issues with a suggested fix.

1. Completeness — are all parts of the plan filled in? Are there gaps in the problem statement, missing approaches, vague done criteria, or no risks listed?
2. Consistency — do the parts agree with each other? Does the selected approach match the done criteria? Do the risks reflect the chosen approach?
3. Clarity — could a developer start coding from this plan without asking questions? Flag anything ambiguous.
4. Scope — does the plan stay focused on the stated problem, or does it drift into unrelated work?
5. Feasibility — is the selected approach realistic given what the plan describes? Are there hidden complexities not acknowledged?

Output a quality score (1–10) and a numbered list of issues. If there are no issues on a dimension, write PASS."
</mandatory>

<gate>Do not proceed until the subagent has returned its review.</gate>

If the subagent is unavailable or fails: use the Edit tool to append the following to the artifact,
then continue to Phase 9.

```
## Review

**Adversarial review:** unavailable — subagent did not run
```

Read the subagent's output. If the quality score is 8 or above and there are no issues: tell the
user the plan passed review. Use the Edit tool to append the following to the artifact, then
continue to Phase 9.

```
## Review

**Adversarial review:** PASSED — quality score [N]/10
```

If there are issues:

Present the findings to the user in plain language — not the raw subagent output. Group by
dimension. For each issue, state what the problem is and what the suggested fix is.

<mandatory>Call AskUserQuestion with:
- Question: "The plan review found [N] issue(s). Addressing them now takes a few minutes and produces a stronger plan. Skipping them is fine if you disagree with the findings. What would you like to do? Recommendation: fix the issues if any feel like genuine gaps."
- Options:
  - "Fix all issues — update the plan" — incorporate the reviewer's suggested fixes
  - "Review each issue — I will decide which to apply" — go through findings one at a time
  - "Skip — the plan is good as-is" — proceed without changes
</mandatory>

If fixing all issues: update the artifact using the Edit tool to address each finding. Then append
the following to the artifact and continue to Phase 9.

```
## Review

**Adversarial review:** [N] issue(s) found — all addressed
```

If reviewing each issue: for each finding, ask the user in plain text whether to apply, modify,
or skip it. Apply accepted changes using the Edit tool. After all issues are reviewed, append the
following to the artifact and continue to Phase 9.

```
## Review

**Adversarial review:** [N] issue(s) found — [M] addressed, [N-M] skipped
```

If skipping: append the following to the artifact and continue to Phase 9.

```
## Review

**Adversarial review:** [N] issue(s) found — user chose to proceed without changes
```

Do not run a second review pass. One adversarial pass is enough.

</phase>

---

<phase id="9" name="implementation-guide">

## Phase 9 — Implementation guide

Generate a concrete implementation guide from the finalized plan. This gives the developer
(or Claude Code) enough to start building without re-reading the full plan.

From the selected approach, definition of done, codebase check results, and failure modes,
derive the following four sections:

**Files** — Every file that needs to be created or modified. For each: the path relative to
the project root, and one sentence describing what the plan requires it to do. If this is a
new project with no existing structure yet, list the files the selected approach requires.

**Interfaces** — The key contracts that must exist for the approach to work: function
signatures for new or modified functions, component prop types, API endpoint shapes (method,
path, request/response), data model changes (new fields, tables, or types). Use whatever
format matches the project's language. Keep this to contracts only — not implementation. If
nothing non-obvious applies, write: "None — implementation follows naturally from the approach."

**Implementation order** — An ordered list of 3–6 steps describing what to build first. Note
dependencies explicitly: "step 3 requires step 2 to exist." Derive the order from the
interfaces — things with no dependencies come first.

**Start here** — A single instruction the developer can paste directly into a Claude Code
conversation to begin implementation. Write it as:

> Read the plan at `[artifact path]`. Implement the [selected approach name]: [2–3 specific
> directives drawn from the approach description, definition of done, and not-in-scope list].
> Do not implement anything listed under Not in scope.

The directives must be concrete enough that Claude Code can act without asking clarifying
questions. Draw entirely from what the plan already decided — do not introduce new scope.

### Confirm and write to artifact

Present the full implementation guide to the user in your response text before writing anything.

<mandatory>Call AskUserQuestion with:
- Question: "Here is the implementation guide — does this look right?"
- Options:
  - "Looks right — write it to the artifact" (Recommended)
  - "Adjust something — describe in Other"
</mandatory>

If adjusting: incorporate the user's changes, then ask again. Once confirmed:

<mandatory>Use the Edit tool to append the following to the artifact after the Long-term
trajectory section:

```
---

## Implementation guide

### Files
[files list]

### Interfaces
[interfaces, or "None — implementation follows naturally from the approach."]

### Implementation order
[ordered steps with dependency notes]

### Start here
[start here instruction]
```
</mandatory>

### Output the Start here instruction

Output the Start here instruction directly in your response as a code block so the developer
can copy it without opening the artifact:

```
Read the plan at `.vibe-check/vc-plan/[branch-slug].md`. Implement the [approach]: [directives].
```

</phase>

---

<phase id="10" name="complete">

## Phase 10 — Complete

### Update roadmap

Check whether `.vibe-check/vc-plan/roadmap.md` exists using the Read tool. If it does:

1. In the Features table, find the row where Branch matches `[current-slug]`. Note the feature name from that row.
2. In the Progress table, find the row for that feature name.
3. Use the Edit tool to update that row: set Plan status to `final` and set Branch to `[current-slug]` (replacing `—` if it was a stub).
4. Use the Read tool to verify the update appears. If not, re-attempt the Edit once. If it still fails, tell the user and provide the exact updated row text to apply manually.

If the roadmap does not exist, or no matching feature is found: skip this step silently.

### Commit the plan artifact

<mandatory>Call AskUserQuestion with:
- Question: "Your plan is saved at `.vibe-check/vc-plan/[branch-slug].md`. Would you like me to commit it now so it travels with your branch into the PR?"
- Options:
  - "Yes — commit it now" (Recommended)
  - "No — I'll commit it with my code"
</mandatory>

If yes:
- bash/zsh: `git add .vibe-check/ && git commit -m "docs: add plan for [branch-slug]"`
- PowerShell: run as two separate commands: `git add .vibe-check/` then `git commit -m "docs: add plan for [branch-slug]"`
If no: continue.

### Tell the user

The plan is complete. Tell the user the path the artifact was written to
(`.vibe-check/vc-plan/[branch-slug].md`). Do not summarize the entire plan back to the user —
they just built it with you.

</phase>

---

## Project decomposition

This section runs only when the user chose "Break it down" in the scope assessment. It
produces a roadmap artifact and a plan stub for each feature. Normal phases do not run.

**Branch check:** Before creating any files, verify that the current branch is BASE_BRANCH. If not, switch now:

```bash
git checkout [BASE_BRANCH]
```

If the checkout fails (uncommitted changes): offer to stash first using the same AskUserQuestion pattern used in Phase 0.

### Step 0 — Context capture

Before mapping features, establish whether there is an existing codebase and capture relevant context that will be written into every stub.

**Determine codebase state:**

If the project description clearly indicates a brand new project with no existing code: note `greenfield — no existing code` and skip the scan below.

If the project has an existing codebase (the user is adding or changing something in a running app): use the Grep and Glob tools to scan for code most likely to be touched by this initiative. Look for:
- Entry points, routers, or top-level modules
- Data models, schemas, or entity definitions
- Auth or session handling files
- Any files whose names match key terms from the user's problem description

Summarize what you find in 3–5 sentences: what exists, how it is organized, and which parts are most relevant to the initiative. If nothing relevant is found, note that explicitly.

Store this summary as **[existing-code-context]** — it will be written into every stub.

### Step 1 — Feature mapping

From the confirmed problem and 12-month direction, identify all discrete user-facing
features the project requires. A feature is something a user can do or see — not a
technical component or infrastructure concern.

Group features into three build phases:

- **Foundation** — must exist before anything else can be built (auth, core data model,
  navigation shell, database schema). If any other feature depends on it, it goes here.
- **Core** — the primary value of the product; the main things users do once the foundation
  exists. This is what makes the product worth using.
- **Enhancing** — adds value but is not required for a first working version (notifications,
  billing, exports, admin tools, analytics). Can be deferred.

For each feature, propose a branch name as a short kebab-case slug — for example
`user-auth`, `workspace-ui`, `tenant-billing`. The stub artifact is named using this slug
so that when the user creates the branch and runs `/vc-plan`, Phase 1 detects the stub
automatically. Do not add any prefix like `feature/` — the slug should be the full branch name.

Present the feature map to the user.

<mandatory>Call AskUserQuestion with:
- Question: "Does this feature breakdown cover everything you want to build? Anything missing, or that should be split or merged?"
- Options:
  - "Looks complete — use this breakdown"
  - "Add or change something" — describe in Other
</mandatory>

Incorporate any changes before continuing.

### Step 2 — Build order

Identify dependencies between features (feature B cannot be built until feature A exists).
Propose a build order that:
- Places all Foundation features first
- Orders Core features by dependency chain (fewest dependencies first)
- Places Enhancing features last
- Notes which features have no dependencies and could be built in parallel

Present the build order as a numbered list with dependency notes. Ask the user to confirm:

<mandatory>Call AskUserQuestion with:
- Question: "Does this build order work for your project? You can adjust the sequence."
- Options:
  - "Yes — use this order"
  - "Adjust the order" — describe the change in Other
</mandatory>

### Step 3 — Create or update roadmap artifact

Check whether `.vibe-check/vc-plan/roadmap.md` exists using the Read tool.

**If no roadmap exists**: use the Write tool to create it:

```
# Project roadmap: [project name]

**Created:** [date]
**Status:** in progress
**Project scope:** [PROJECT_SCOPE]
**Base branch:** [BASE_BRANCH]

---

## Features

| # | Feature | Build phase | Depends on | Branch | Plan stub |
|---|---------|------------|-----------|--------|-----------|
| 1 | [name] | Foundation | — | `[slug]` | `.vibe-check/vc-plan/[slug].md` |
...

---

## Build order

[numbered list with dependency notes]

---

## Progress

| Feature | Plan status | Branch | Built |
|---------|------------|--------|-------|
| [name] | stub | — | — |
...

---

## How to work on a feature

Run `/vc-plan` from your main branch — it reads this roadmap, offers available features as
options, and creates branches automatically. After planning, implement using the Start here
instruction, then run `/vc-audit` and `/vc-ship`. The roadmap updates automatically when
plans finalize and branches ship.
```

**If a roadmap already exists**: do not overwrite it. Use the Edit tool to:
1. Append new rows for each decomposed feature to the Features table (continue the row numbering)
2. Append new rows for each decomposed feature to the Progress table
3. Append a Build order section after the existing content if one does not already exist; if one exists, append a sub-section for this initiative's build order
4. Leave the "How to work on a feature" section unchanged

### Step 4 — Create plan stubs

For each feature, create a stub plan artifact. The stub pre-loads the problem statement and
direction so that running `/vc-plan` on the feature branch picks up at Phase 3 (approaches)
rather than starting from scratch.

Name each stub using the branch slug directly: if the branch is `user-auth`, the stub is
`.vibe-check/vc-plan/user-auth.md`. This matches the one-shot path exactly — Phase 1 always
looks for `.vibe-check/vc-plan/[branch-slug].md` regardless of how the artifact was created.

<mandatory>Use the Write tool to create each stub. Do not proceed until all stubs are
written to disk.

Each stub follows this template:

```
# Plan: [slug]

**Branch:** [slug] — create this branch when you are ready to build this feature
**Date:** [today's date]
**Status:** stub — run /vc-plan on the feature branch to complete

---

## Initiative context

**Initiative:** [project/initiative name]
**Codebase:** [greenfield — no existing code | existing codebase]
**Existing code relevant to this feature:** [from [existing-code-context], filtered to what is most relevant to this specific feature — or "None — new project"]
**Other features in this initiative:** [comma-separated list of sibling feature names and their branch slugs, e.g. "user-auth (Foundation), workspace-ui (Core)"]

---

## Premises

*Run /vc-plan to define premises.*

---

## How to build this feature

1. Run `/vc-plan` from your main branch — it reads the roadmap, offers this feature as an option, and creates the `[slug]` branch automatically
2. Run `/vc-plan` — pick this feature, choose "review and update the existing plan," and continue from the Approaches section — Problem/Goal and Direction are already filled in
3. Implement using the Start here instruction the plan generates
4. Run `/vc-audit` on the branch before submitting
5. Run `/vc-ship` to push and create the pull request (PR) — it updates the roadmap automatically

---

## Problem / Goal

[2–3 sentences describing this specific feature — what it does, why it exists, and what
user need it addresses. Derived from the project decomposition.]

---

## Direction

| | |
|---|---|
| **This branch** | [one sentence: what this feature delivers] |
| **Depends on** | [feature name(s) this depends on, or "none"] |

---

## Approaches

*Run /vc-plan on this feature's branch to define and select an approach.*

---

## Not in scope

*Run /vc-plan to define the scope boundary.*

---

## Definition of done

*Run /vc-plan to define done criteria.*

---

## Risks

*Run /vc-plan to identify risks.*

---

## Failure modes & security

*Run /vc-plan to define failure modes.*

---

## Long-term trajectory

*Run /vc-plan to assess trajectory.*

---

## Implementation guide

*Run /vc-plan to generate the implementation guide.*
```
</mandatory>

### Step 5 — Output

Tell the user:
1. The roadmap artifact path (`.vibe-check/vc-plan/roadmap.md`) and how many features were identified
2. A numbered list of ALL features in build order. For each feature include:
   - Feature name and tier (Foundation / Core / Enhancing)
   - Dependencies (or "none")
   - Branch creation command as an inline code snippet: `git checkout -b [slug]`
   - Stub path: `.vibe-check/vc-plan/[slug].md`
3. The workflow instructions below, presented as a clear section the user can refer back to:

---

**How to work on each feature:**

For each feature, in build order:

1. Create the branch: `git checkout -b [slug]`
2. Run `/vc-plan` — it detects the stub and continues from the approaches phase with the problem, existing-code context, and dependencies already loaded
3. Implement using the Start here instruction the plan generates
4. Run `/vc-audit` on the branch before submitting
5. Run `/vc-ship` to push and create the pull request (PR)
6. vc-ship updates the roadmap automatically when you ship each branch — no manual step needed

---

<mandatory>Call AskUserQuestion with:
- Question: "Your roadmap and plan stubs are saved at `.vibe-check/vc-plan/`. Would you like me to commit them now so they travel with the repo from the start?"
- Options:
  - "Yes — commit them now" (Recommended)
  - "No — I'll commit them myself"
</mandatory>

If yes:
- bash/zsh: `git add .vibe-check/ && git commit -m "docs: add project roadmap and plan stubs"`
- PowerShell: run as two separate commands: `git add .vibe-check/` then `git commit -m "docs: add project roadmap and plan stubs"`
If no: continue.

Then ask whether the user wants to start planning the first feature now:

<mandatory>Call AskUserQuestion with:
- Question: "The roadmap is ready. Do you want to start planning the first feature ([first-slug]) now?"
- Options:
  - "Yes — start planning now" (Recommended)
  - "Not yet — I will come back when I am ready"
</mandatory>

If yes: run `git branch --list "[first-slug]*"` to check for existing branches. Filter results:
only treat as a collision if a branch name is exactly `[first-slug]` or matches `[first-slug]-N`
where N is a whole number. If a collision exists, take the highest N and use N+1.

Run `git status --short`. If uncommitted changes exist:
<mandatory>Call AskUserQuestion with:
- Question: "You have uncommitted changes on [BASE_BRANCH] — these will carry over to the new branch `[final-slug]`. Carrying them over means those edits will be part of this feature branch. Stashing them keeps [BASE_BRANCH] clean. What would you like to do?"
- Options:
  - "Carry them over — these changes belong to this feature branch"
  - "Stash them — keep [BASE_BRANCH] clean, I'll decide later"
</mandatory>
If stash: run `git stash`. After the branch is created, tell the user: "Your changes on [BASE_BRANCH] have been temporarily saved (stashed) — they are not lost, just parked. Run `git stash pop` if you want to restore them on this new branch."

Run `git checkout -b [final-slug]`. Confirm the branch was created.
This is now `[branch-slug]` for all remaining phases. Then jump directly to Phase 3 — the stub already has Problem/Goal and Direction loaded, so begin at the codebase check. Do not re-run Phases 0, 1, or 2.

If no: tell the user that when they are ready to work on a feature, running `/vc-plan` from
[main branch name] will read the roadmap and offer the available features to start — no git
commands needed. Do not continue to any other phase.
