## Local config

Silently attempt to read `.vibe-check/vc-local.conf` using the Read tool. Do not report success or failure to the user.

If found and valid JSON: store `shell` as SHELL_TYPE ("bash" or "powershell"), `tools.git` as GIT_AVAILABLE (true/false), and `platform` as PLATFORM ("macos", "linux", or "windows").

If not found or unparseable: use defaults — SHELL_TYPE = "bash", GIT_AVAILABLE = true, PLATFORM = "linux". Run `/vc-bootstrap` to generate the file.
