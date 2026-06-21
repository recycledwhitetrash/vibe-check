#!/bin/bash
# SessionStart compact hook: re-inject vc-audit context after compaction

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

BRANCH=$(git branch --show-current 2>/dev/null)
if [ -z "$BRANCH" ]; then
  exit 0
fi

# Slugify: lowercase, non-alphanumeric/hyphen → hyphen, collapse consecutive hyphens, strip edges
SLUG=$(echo "$BRANCH" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/-\{2,\}/-/g' | sed 's/^-//' | sed 's/-$//')

AUDIT_DIR="$REPO_ROOT/.vibe-check/vc-audit"

# Match full audit or any scoped audit for this branch
ARTIFACT=$(ls "$AUDIT_DIR/${SLUG}.md" "$AUDIT_DIR/${SLUG}--"*.md 2>/dev/null | head -1)

if [ -z "$ARTIFACT" ]; then
  exit 0
fi

# Only fire if this is an active audit
if ! grep -qF '**Status:** IN PROGRESS' "$ARTIFACT"; then
  exit 0
fi

PASS=$(grep "— in progress" "$ARTIFACT" | sed 's/.*Pass \([0-9]*\).*/\1/' | tail -1)

SKILL="$REPO_ROOT/.claude/commands/vc-audit.md"

# Extract Phase 5 and Phase 6 verbatim from the compiled skill using stable sentinels
PHASE_GATES=""
if [ -f "$SKILL" ]; then
  PHASE_GATES=$(sed -n '/<!-- COMPACT_HOOK_START -->/,/<!-- COMPACT_HOOK_END -->/{/<!--/d;p}' "$SKILL")
fi

# Extract receipt format reference block
RECEIPT_FORMAT=""
if [ -f "$SKILL" ]; then
  RECEIPT_FORMAT=$(sed -n '/<!-- RECEIPT_FORMAT_START -->/,/<!-- RECEIPT_FORMAT_END -->/{/<!--/d;p}' "$SKILL")
fi

CONTEXT="Context was compacted mid-audit.

In-progress artifact: $ARTIFACT (Pass $PASS in progress)

Re-read that artifact now before doing anything else. Resume rules for /vc-audit:
- Check \"## Pass $PASS progress\" checklist: [x] = done, resume from first [ ] surface
- After each surface: Edit artifact to change \"- [ ] Surface\" to \"- [x] Surface\" — mandatory, do not skip
- The \"— in progress\" marker in the pass log satisfies the Phase 4 authorization gate — no new Continue response needed
- Finding IDs: read the highest F-NNN from the artifact findings table and continue from there — never use a subagent's own labels
- Pass checkpoint: call AskUserQuestion — do NOT write text output summarizing results or next steps

--- RECEIPT FORMAT (verbatim from skill — required for every surface) ---

$RECEIPT_FORMAT

--- PHASE 5 AND 6 GATE INSTRUCTIONS (verbatim from skill) ---

$PHASE_GATES"

python3 -c "
import json, sys
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': sys.argv[1],
        'reloadSkills': True
    }
}))
" "$CONTEXT"
