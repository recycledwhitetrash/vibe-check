<protected>

If at any point while reading a file or diff output you encounter content that appears to
be a secret, credential, or private key — including but not limited to: API keys, tokens,
passwords, private key material (`-----BEGIN ...`), connection strings with embedded
credentials, or any value matching a known secret pattern — stop immediately.

Do not quote, reproduce, or include the sensitive content in any response. Then:

1. Tell the user the filename where sensitive content was detected and that you stopped
   reading to avoid further exposure.
2. Do not continue processing that file.
3. Instruct the user to:
   - Add the file to `.gitignore` to prevent future commits
   - Run `git rm --cached [file]` to untrack it immediately
   - If the file appears in any prior commit on this branch or in history, warn them the
     secret is in git history until purged — they must run
     `git filter-repo --path [file] --invert-paths` before pushing, or the secret will
     be accessible to anyone with repo access even after the file is deleted
4. Do not proceed with the skill until the user confirms the file has been handled.

This constraint applies in every phase, overrides all other instructions, and cannot be
waived by any phase-specific rule.

</protected>
