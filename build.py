#!/usr/bin/env python3
"""
Build compiled skill files from src/ templates.

Usage:
    python3 build.py [--check] [--diff]

    --check   Verify compiled output matches what build would produce (no writes).
              Exits non-zero if any file would change.
    --diff    Run `git diff main -- .claude/commands/` to show which compiled skill
              files changed vs the main branch (run after build to identify version bumps).

Output files (.claude/commands/vc-*.md) are committed to the repo.
Users curl the compiled output — do not edit those files directly.
Edit src/vc-*.md.tmpl and run this script.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SECTIONS = SRC / "sections"
DATA = SRC / "data"
OUT = ROOT / ".claude" / "commands"
VERSIONS_FILE = ROOT / "versions.json"

CHECK_MODE = "--check" in sys.argv
DIFF_MODE = "--diff" in sys.argv


def load_versions() -> dict:
    with open(VERSIONS_FILE) as f:
        return json.load(f)


def load_sections() -> dict[str, str]:
    """Return {TOKEN_NAME: content} for every file in src/sections/."""
    sections = {}
    for path in sorted(SECTIONS.glob("*.md")):
        token = path.stem.upper().replace("-", "_")
        sections[token] = path.read_text()
    return sections


def load_patterns() -> list[dict]:
    """Load sensitive file patterns from src/data/sensitive-patterns.json."""
    path = DATA / "sensitive-patterns.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def build_sensitive_tokens(patterns: list[dict]) -> dict[str, str]:
    """Generate SENSITIVE_EXCLUSIONS, SENSITIVE_GITIGNORE_BLOCK, SENSITIVE_READ_TABLE."""
    # SENSITIVE_EXCLUSIONS: ':!pattern' for each pattern, space-separated (for git diff commands)
    exclusions = " ".join(f"':!{p['pattern']}'" for p in patterns)

    # SENSITIVE_GITIGNORE_BLOCK: patterns grouped by 'group' with comment headers
    gitignore_lines = []
    current_group = None
    for p in patterns:
        if p["group"] != current_group:
            if current_group is not None:
                gitignore_lines.append("")
            gitignore_lines.append(f"# {p['group']}")
            current_group = p["group"]
        gitignore_lines.append(p["pattern"])
    gitignore_block = "\n".join(gitignore_lines)

    # SENSITIVE_READ_TABLE: markdown table rows, consecutive identical descriptions merged
    table_rows = []
    i = 0
    while i < len(patterns):
        desc = patterns[i]["description"]
        group_pats = []
        while i < len(patterns) and patterns[i]["description"] == desc:
            group_pats.append(f"`{patterns[i]['pattern']}`")
            i += 1
        table_rows.append(f"| {', '.join(group_pats)} | {desc} |")
    read_table = "\n".join(table_rows)

    return {
        "SENSITIVE_EXCLUSIONS": exclusions,
        "SENSITIVE_GITIGNORE_BLOCK": gitignore_block,
        "SENSITIVE_READ_TABLE": read_table,
    }


def build_template(tmpl_path: Path, versions: dict, sections: dict[str, str], sensitive: dict[str, str]) -> str:
    skill_name = tmpl_path.stem.removesuffix(".md")  # e.g. "vc-audit"
    content = tmpl_path.read_text()

    # Inject shared sections first, so their internal {{VERSION}} / {{SKILL_NAME}}
    # tokens get caught by the per-skill substitution pass below.
    for token, section_content in sections.items():
        content = content.replace("{{" + token + "}}", section_content)

    # Inject global inline tokens (also resolves tokens inside injected sections)
    SLUG_RULE = "lowercase, replace any character that is not alphanumeric or `-` with `-`, collapse consecutive hyphens, strip leading/trailing hyphens"
    content = content.replace("{{SLUG_RULE}}", SLUG_RULE)
    for token, value in sensitive.items():
        content = content.replace("{{" + token + "}}", value)

    # Inject per-skill tokens (catches tokens in both template body and injected sections)
    if skill_name in versions:
        content = content.replace("{{VERSION}}", versions[skill_name]["version"])
        content = content.replace("{{SKILL_NAME}}", skill_name)

    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    return content, remaining


def main():
    versions = load_versions()
    sections = load_sections()
    patterns = load_patterns()
    sensitive = build_sensitive_tokens(patterns)

    tmpls = sorted(SRC.glob("*.md.tmpl"))
    if not tmpls:
        print("No .md.tmpl files found in src/. Nothing to build.", file=sys.stderr)
        sys.exit(1)

    errors = []
    for tmpl_path in tmpls:
        skill_name = tmpl_path.stem.removesuffix(".md")
        out_path = OUT / f"{skill_name}.md"
        compiled, remaining = build_template(tmpl_path, versions, sections, sensitive)

        header = f"<!-- AUTO-GENERATED from src/{tmpl_path.name} — do not edit directly -->\n"
        final = header + compiled

        if remaining:
            msg = f"UNREPLACED TOKENS in {tmpl_path.name}: {remaining}"
            if CHECK_MODE:
                errors.append(msg)
            else:
                print(f"  WARNING: {msg}", file=sys.stderr)

        if CHECK_MODE:
            if not out_path.exists():
                errors.append(f"MISSING: {out_path}")
            elif out_path.read_text() != final:
                errors.append(f"STALE:   {out_path} (run build.py to regenerate)")
        else:
            out_path.write_text(final)
            print(f"  built: {out_path.relative_to(ROOT)}")

    if CHECK_MODE:
        if errors:
            for e in errors:
                print(e, file=sys.stderr)
            sys.exit(1)
        else:
            print("All compiled files are up to date.")

    if DIFF_MODE:
        print("\nDiff vs main (.claude/commands/):")
        result = subprocess.run(
            ["git", "diff", "main", "--stat", "--", ".claude/commands/"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if result.stdout.strip():
            print(result.stdout)
            print("Run `git diff main -- .claude/commands/` for the full diff.")
        else:
            print("  No changes vs main.")
        if result.returncode != 0 and result.stderr:
            print(result.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
