## Version check

Use the Bash tool to run: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/versions.json`

If curl fails or exits non-zero for any reason, skip this section entirely and proceed to Phase 0.

Read the JSON from stdout and check the `{{SKILL_NAME}}` entry.

<output-handlers>

**`{{SKILL_NAME}}` version matches `{{VERSION}}`**: proceed silently.

**Newer version available, `critical` is false**:
<mandatory>Call AskUserQuestion with:
- Question: "A newer version of /{{SKILL_NAME}} is available. Proceed with your current version or update now."
- Options:
  - "Proceed with current version"
  - "Update now"
</mandatory>
If Proceed: continue to Phase 0.
If Update now: follow the **Auto-update** steps below, then stop.

**Newer version available, `critical` is true**:
<mandatory>Call AskUserQuestion with:
- Question: "A critical update is available for /{{SKILL_NAME}} that fixes an important issue. Running the current version may produce incorrect results."
- Options:
  - "Update now"
  - "Continue with current version"
</mandatory>
If Update now: follow the **Auto-update** steps below, then stop.
If Continue: proceed to Phase 0.

**Fetched version is older than `{{VERSION}}`**: proceed silently. (This can happen with CDN caching or a rollback — the local version is already newer.)

</output-handlers>

**Auto-update:**
1. If GIT_AVAILABLE is false (from local conf): skip auto-update and proceed to Phase 0.
2. Run `git rev-parse --show-toplevel` to find the project root.
3. Use the Bash tool to download and overwrite the skill file in one step:
   - bash/zsh: `curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/{{SKILL_NAME}}.md -o "[project-root]/.claude/commands/{{SKILL_NAME}}.md"`
   - PowerShell: `curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/commands/{{SKILL_NAME}}.md -o "[project-root]/.claude/commands/{{SKILL_NAME}}.md"`
{{COMPANION_DOWNLOADS}}4. If curl exits 0: tell the user "Updated to the latest version — reloading and resuming." Then use the Read tool to read `[project-root]/.claude/commands/{{SKILL_NAME}}.md`. Proceed to Phase 0 of the updated skill, following the instructions just read. Do not re-run the version check — the update is already complete. Do NOT stop, do NOT ask the user to re-run the skill — continue executing from Phase 0 immediately.
5. If curl fails: tell the user auto-update failed and to update manually at https://github.com/recycledwhitetrash/vibe-check. Do not continue.
