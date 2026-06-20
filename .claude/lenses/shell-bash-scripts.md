<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Shell / bash script lenses

- **Shell hygiene**: `set -euo pipefail` absent or incomplete; unquoted variable expansions
  (word splitting and glob expansion on `$var` and `"$@"`); arrays used where they should be
  vs. space-split strings; `[[ ]]` vs `[ ]` correctness; `local` missing in functions
- **Injection & traversal**: unvalidated input used in command strings; `eval` on
  user-controlled data; PATH not locked down in scripts run as root or from cron; `..` in
  file paths accepted from input; heredoc content with user data injected
- **Temp files**: created with `mktemp`, not predictable names in `/tmp`; `trap EXIT`
  cleans up; world-readable permissions on files containing sensitive data
- **Concurrency (scripts)**: no `flock` on shared resource writes; PID files checked and
  written non-atomically (two instances start simultaneously); signal handlers call
  non-async-signal-safe functions
- **Exit code contract**: every called subprocess's exit code checked; `VAR=$(cmd)` failure
  silently makes `VAR` empty — checked after; `||` / `&&` chains that hide failures
- **Cron / scheduled context**: PATH may be minimal; environment variables may differ from
  interactive shell; no output destination for errors (stderr goes nowhere)
- **CLI UX** (if this script is user-facing): `--help` present; `--dry-run` available for
  destructive scripts; progress output for long operations; SIGINT handled cleanly; output
  machine-parseable when piped
- **Secrets in debug output**: `set -x` enabled in a script that handles credentials or
  tokens — logs every command with all expanded variable values, including secrets, to
  stdout/stderr which is captured by CI logs, systemd journal, and monitoring systems;
  credentials echoed in success or error messages
- **Network operations**: `curl` or `wget` without `--fail` or `--fail-with-body` — HTTP
  4xx/5xx responses exit with code 0 and an empty or error body silently processed as
  success; `-k`/`--insecure` disabling TLS certificate verification; fetching and piping
  directly to `bash` (`curl https://... | bash`) without verifying a checksum or
  signature first
- **Symlink attacks**: writing to a file path without checking if it is a symlink first;
  an attacker with local write access creates a symlink from the expected temp path to a
  sensitive system file (`/etc/passwd`, a config file), and the script overwrites it;
  use `set -o noclobber`, `O_NOFOLLOW`-equivalent checks, or `mktemp` for all temp paths
