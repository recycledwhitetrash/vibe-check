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

# The lens catalog is NOT a slash command — it is a data file read selectively at audit
# time. Its source template is split per-stack into .claude/lenses/ (outside commands/, so
# Claude Code does not register it). Each Phase 0 stack loads only its own lens file.
LENS_TEMPLATE = "vc-audit-lenses"          # src/vc-audit-lenses.md.tmpl stem
LENS_OUT_DIR = ROOT / ".claude" / "lenses"

CHECK_MODE = "--check" in sys.argv
DIFF_MODE = "--diff" in sys.argv


def slugify(s: str) -> str:
    """Lens-file slug: lowercase, non-alphanumerics -> '-', collapse, strip."""
    s = re.sub(r"[^a-z0-9]+", "-", s.lower())
    return s.strip("-")

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

    # Inject skill-specific companion download steps (used by version-check section)
    COMPANION_DOWNLOADS = {
        "vc-audit": (
            "   Also refresh the per-stack lens catalog in `.claude/lenses/`. Fetch the manifest, then download each listed file:\n"
            "   - bash/zsh:\n"
            "     ```bash\n"
            "     mkdir -p \"[project-root]/.claude/lenses\"\n"
            "     curl -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt | while read -r f; do\n"
            "       curl -fsSL \"https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$f\" -o \"[project-root]/.claude/lenses/$f\"\n"
            "     done\n"
            "     ```\n"
            "   - PowerShell:\n"
            "     ```powershell\n"
            "     New-Item -ItemType Directory -Force -Path \"[project-root]\\.claude\\lenses\" | Out-Null\n"
            "     (curl.exe -fsSL https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/manifest.txt) -split \"`n\" | Where-Object { $_ } | ForEach-Object {\n"
            "       curl.exe -fsSL \"https://raw.githubusercontent.com/recycledwhitetrash/vibe-check/main/.claude/lenses/$_\" -o \"[project-root]\\.claude\\lenses\\$_\"\n"
            "     }\n"
            "     ```\n"
        ),
    }
    content = content.replace("{{COMPANION_DOWNLOADS}}", COMPANION_DOWNLOADS.get(skill_name, ""))

    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    return content, remaining


def compile_all(tmpls, versions, sections, sensitive) -> dict[str, tuple[str, list[str], Path]]:
    """Return {skill_name: (final_content, remaining_tokens, out_path)}.

    The lens catalog template is handled separately by split_lenses() — skip it here.
    """
    results = {}
    for tmpl_path in tmpls:
        skill_name = tmpl_path.stem.removesuffix(".md")
        if skill_name == LENS_TEMPLATE:
            continue
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


def split_lenses(versions, sections, sensitive) -> tuple[dict[Path, str], str]:
    """Split the lens catalog template into per-stack files under .claude/lenses/.

    Each `### ` section is tagged in the source with `<!-- stack: NAME -->` where NAME is
    the exact Phase 0 stack-detection name. Returns:
      - files: {output_path -> content} for every lens file plus manifest.txt
      - manifest_md: a markdown table mapping each stack to its lens file, injected into
        the vc-audit skill via the {{LENS_MANIFEST}} token.
    """
    tmpl_path = SRC / f"{LENS_TEMPLATE}.md.tmpl"
    content, _ = build_template(tmpl_path, versions, sections, sensitive)
    notice = f"<!-- AUTO-GENERATED from src/{tmpl_path.name} — do not edit directly -->\n"

    # Walk lines, grouping into sections that start at each `### ` header.
    current = None
    sections_out = []  # list of {"stack": str|None, "body": [lines]}
    tag_re = re.compile(r"^<!--\s*stack:\s*(.+?)\s*-->\s*$")
    for line in content.splitlines(keepends=True):
        if line.startswith("### "):
            current = {"stack": None, "body": [line]}
            sections_out.append(current)
            continue
        if current is None:
            continue  # preamble before the first header (none expected)
        m = tag_re.match(line)
        if m and current["stack"] is None:
            current["stack"] = m.group(1)
            continue  # tag is build metadata — do not write it to the lens file
        current["body"].append(line)

    files: dict[Path, str] = {}
    manifest_names = []          # all filenames, for manifest.txt (download loop)
    manifest_rows = []           # (stack, filename) for the markdown table
    for sec in sections_out:
        stack = sec["stack"] or "universal"
        fname = f"{slugify(stack)}.md"
        body = "".join(sec["body"]).rstrip() + "\n"
        files[LENS_OUT_DIR / fname] = notice + body
        manifest_names.append(fname)
        if stack.lower() != "universal":
            manifest_rows.append((stack, fname))

    # manifest.txt: newline list of every lens filename (universal first), for the
    # install / auto-update download loops.
    files[LENS_OUT_DIR / "manifest.txt"] = "\n".join(manifest_names) + "\n"

    # Markdown manifest table for the skill: stack -> lens file path.
    md = ["| Stack (detected in Phase 0) | Lens file to read |", "|---|---|"]
    for stack, fname in manifest_rows:
        md.append(f"| {stack} | `.claude/lenses/{fname}` |")
    manifest_md = "\n".join(md)

    return files, manifest_md


def main():
    versions = load_versions()
    sections = load_sections()
    patterns = load_patterns()
    sensitive = build_sensitive_tokens(patterns)

    tmpls = sorted(SRC.glob("*.md.tmpl"))
    if not tmpls:
        print("No .md.tmpl files found in src/. Nothing to build.", file=sys.stderr)
        sys.exit(1)

    # Split the lens catalog first — it produces the {{LENS_MANIFEST}} token that the
    # vc-audit skill needs, so it must run before compile_all.
    lens_files, lens_manifest = split_lenses(versions, sections, sensitive)
    sensitive["LENS_MANIFEST"] = lens_manifest

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

    # Per-stack lens files + manifest.txt (data files, not versioned skills).
    for lens_path, lens_content in sorted(lens_files.items()):
        if CHECK_MODE:
            if not lens_path.exists():
                errors.append(f"MISSING: {lens_path}")
            elif lens_path.read_text() != lens_content:
                errors.append(f"STALE:   {lens_path} (run build.py to regenerate)")
        else:
            lens_path.parent.mkdir(parents=True, exist_ok=True)
            lens_path.write_text(lens_content)
    if not CHECK_MODE:
        # Remove orphaned lens files (a stack was renamed/removed in the source).
        if LENS_OUT_DIR.exists():
            keep = {p.name for p in lens_files}
            for existing in LENS_OUT_DIR.iterdir():
                if existing.is_file() and existing.name not in keep:
                    existing.unlink()
        print(f"  built: {LENS_OUT_DIR.relative_to(ROOT)}/ ({len(lens_files)} lens files)")

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
