### Security baseline check

Use the Read tool to read `.gitignore` (if it exists). Check whether the lines `# vibe-check security baseline start` and `# vibe-check security baseline end` are both present.

**Both markers present**: read the content between the markers and compare it line-by-line to the current baseline block below. If the content matches exactly: skip. If it differs:
- Use the Edit tool to replace everything from `# vibe-check security baseline start` through `# vibe-check security baseline end` (inclusive) with the updated baseline block below.
- Tell the user: "Updated the vibe-check security baseline in `.gitignore`."

**Markers absent** (or `.gitignore` does not exist):
<mandatory>Call AskUserQuestion with:
- Question: "No vibe-check security baseline was found in `.gitignore`. Add the security patterns now?"
- Options:
  - "Add security patterns"
  - "Leave it as-is"
</mandatory>
If Add security patterns:
- If `.gitignore` exists: use the Edit tool to append the security baseline block to the end of `.gitignore`.
- If `.gitignore` does not exist: use the Write tool to create it with the full template below.
If Leave it as-is: skip.

**Full `.gitignore` template (for new files only):**

```
# ============================================================
# Security — never commit secrets or credentials
# ============================================================

# vibe-check security baseline start
{{SENSITIVE_GITIGNORE_BLOCK}}
# vibe-check security baseline end

{{GITIGNORE_BOILERPLATE}}
```

After any write or update: tell the user "If VS Code's Source Control panel still shows files that should now be ignored, click the **refresh icon** (↺) at the top of the Source Control panel — VS Code doesn't always pick up `.gitignore` changes automatically."

**Current security baseline block:**

```
# vibe-check security baseline start
{{SENSITIVE_GITIGNORE_BLOCK}}
# vibe-check security baseline end
```
