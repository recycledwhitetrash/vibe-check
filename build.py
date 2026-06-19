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
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SECTIONS = SRC / "sections"
DATA = SRC / "data"
OUT = ROOT / ".claude" / "commands"
VERSIONS_FILE = ROOT / "versions.json"

CHECK_MODE = "--check" in sys.argv
DIFF_MODE = "--diff" in sys.argv

VERSION_RE = re.compile(r"\d{4}-\d{2}-\d{2}\.\d+")


def load_versions() -> dict:
    with open(VERSIONS_FILE) as f:
        return json.load(f)


def save_versions(versions: dict) -> None:
    """Write versions.json preserving the aligned one-skill-per-line format."""
    max_len = max(len(k) for k in versions)
    lines = ["{"]
    items = list(versions.items())
    for i, (skill, info) in enumerate(items):
        pad = " " * (max_len - len(skill) + 1)
        comma = "," if i < len(items) - 1 else ""
        entry = f'{{ "version": "{info["version"]}", "critical": {str(info["critical"]).lower()} }}'
        lines.append(f'  "{skill}":{pad}{entry}{comma}')
    lines.append("}")
    VERSIONS_FILE.write_text("\n".join(lines) + "\n")


def next_version(current: str) -> str:
    """Bump to today.1, or increment the suffix if already today."""
    today = date.today().strftime("%Y-%m-%d")
    m = re.match(r"(\d{4}-\d{2}-\d{2})\.(\d+)", current)
    if m and m.group(1) == today:
        return f"{today}.{int(m.group(2)) + 1}"
    return f"{today}.1"


def content_changed(compiled: str, on_disk: str) -> bool:
    """True if the files differ on non-version lines."""
    strip = lambda s: [l for l in s.splitlines() if not VERSION_RE.search(l)]
    return strip(compiled) != strip(on_disk)


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


def build_template(tmpl_path: Path, versions: dict, sections: dict[str, str], sensitive: dict[str, str]) -> tuple[str, list[str]]:
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


def compile_all(tmpls, versions, sections, sensitive) -> dict[str, tuple[str, list[str], Path]]:
    """Return {skill_name: (final_content, remaining_tokens, out_path)}."""
    results = {}
    for tmpl_path in tmpls:
        skill_name = tmpl_path.stem.removesuffix(".md")
        out_path = OUT / f"{skill_name}.md"
        compiled, remaining = build_template(tmpl_path, versions, sections, sensitive)
        notice = f"<!-- AUTO-GENERATED from src/{tmpl_path.name} — do not edit directly -->\n"
        # Place notice after closing --- if file has YAML frontmatter
        if compiled.startswith("---\n"):
            end = compiled.index("\n---\n", 4) + 5
            final = compiled[:end] + notice + compiled[end:]
        else:
            final = notice + compiled
        results[skill_name] = (final, remaining, out_path)
    return results


def main():
    versions = load_versions()
    sections = load_sections()
    patterns = load_patterns()
    sensitive = build_sensitive_tokens(patterns)

    tmpls = sorted(SRC.glob("*.md.tmpl"))
    if not tmpls:
        print("No .md.tmpl files found in src/. Nothing to build.", file=sys.stderr)
        sys.exit(1)

    results = compile_all(tmpls, versions, sections, sensitive)

    # Auto-bump versions for skills whose non-version content changed vs on-disk.
    # Skipped in --check mode (check verifies the current state, doesn't mutate).
    bumped = {}  # skill_name -> (old, new)
    if not CHECK_MODE:
        for skill_name, (final, _, out_path) in results.items():
            if skill_name in versions and out_path.exists():
                if content_changed(final, out_path.read_text()):
                    old = versions[skill_name]["version"]
                    versions[skill_name]["version"] = next_version(old)
                    bumped[skill_name] = (old, versions[skill_name]["version"])
        if bumped:
            save_versions(versions)
            results = compile_all(tmpls, versions, sections, sensitive)

    errors = []
    for skill_name, (final, remaining, out_path) in results.items():
        if remaining:
            msg = f"UNREPLACED TOKENS in {skill_name}.md.tmpl: {remaining}"
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
            if skill_name in bumped:
                old, new = bumped[skill_name]
                print(f"  built: {out_path.relative_to(ROOT)}  [{old} → {new}]")
            else:
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
