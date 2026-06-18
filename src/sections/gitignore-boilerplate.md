# ============================================================
# Installed packages and dependencies (never commit these)
# ============================================================

node_modules/
.venv/
venv/
env/
.env/
__pycache__/
*.pyc
.bundle/
vendor/bundle/
.gradle/
build/
dist/
target/

# ============================================================
# Framework and build tool caches
# ============================================================

.vite/
.next/
.nuxt/
.svelte-kit/
.parcel-cache/
.turbo/
.cache/

# ============================================================
# Test output
# ============================================================

coverage/
.nyc_output/
playwright-report/
test-results/
cypress/videos/
cypress/screenshots/
*.tsbuildinfo
.eslintcache
.stylelintcache
.pytest_cache/
.mypy_cache/
.ruff_cache/

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
# vibe-check local config (machine-specific, not for sharing)
# ============================================================

.vibe-check/vc-local.conf

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
