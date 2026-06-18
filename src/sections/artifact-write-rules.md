<artifact-write-rules>

Shell and interpreter scripts may never write to `.vibe-check/**`. Use the Edit or Write tool only.

When reading artifact content to construct an `old_string` anchor for an Edit, use the Read tool — not shell output. Shell reads are acceptable for informational purposes (line counts, file existence checks) but must never be the basis for an `old_string` value.

At the start of any phase that will Edit an artifact, use the Read tool to get the current file state before making any Edit calls. Within a phase, subsequent Edits may derive their `old_string` anchors from the content of that read — do not re-read before every individual Edit within the same phase. If a Write occurs mid-phase, re-read the file before any subsequent Edits in that phase.

</artifact-write-rules>
