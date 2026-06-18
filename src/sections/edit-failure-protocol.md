<edit-failure-protocol>

If the Edit tool returns "String to replace not found":

1. **Do not diagnose. Do not switch to a shell script or interpreter.** Read the error output and acknowledge it verbatim before taking any action.
2. Use the Read tool to get the current exact text of the file. Construct the shortest unique anchor (1–2 lines) from what you just read. Retry the Edit once.
3. If the retry fails: use the Read tool to read the **entire file** fresh. Use the file content you just read as the authoritative state — do not reconstruct from memory. Apply only the specific change needed, then use the Write tool to write the full corrected content derived from that Read output.
4. If the Write tool also fails: stop. Give the user the exact intended content to apply manually. Do not continue until the user confirms the file is correct.

This ladder is mandatory. Do not improvise a recovery path not in this list.

</edit-failure-protocol>
