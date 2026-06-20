<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### AI agent lenses

- **Prompt injection**: user-supplied or tool-fetched content reaching the system prompt or
  being interpreted as instructions — direct injection via input, indirect injection via tool
  results containing `"Ignore previous instructions..."`, second-order injection (data fetched
  in turn N executes in turn N+1), agent-to-agent injection (subordinate agent's output piped
  unsanitized into parent context)
- **Tool call security**: arguments to tools derived from untrusted input — are they validated
  before execution? does a `run_shell` tool accept an LLM-generated string directly? are
  irreversible actions (send email, delete file, make payment, deploy) gated behind a
  human-in-the-loop checkpoint before execution?
- **Tool least-privilege**: agent granted write/delete/execute tools it only needs
  occasionally; should these be separate agents or conditional grants rather than always
  present?
- **Tool result trust**: output from a tool treated as ground truth and piped directly into
  the next tool call or into the model context as instructions
- **Multi-agent trust boundaries**: agent A calls agent B — what authority does B grant
  A's messages? system-prompt authority or user-prompt authority? can a malicious tool
  result claim to be a trusted orchestrator?
- **Agentic loop safety**: no turn limit, no cost cap, no circuit breaker; fan-out (each
  iteration spawns more tool calls than the last) with no max-parallelism or max-depth;
  self-modification (agent writes to its own prompt, config, or tool list)
- **Nondeterminism / fragile parsing**: LLM output parsed as structured data without schema
  validation; hallucinated tool arguments (model invents plausible-sounding but wrong IDs,
  dates, enum values); output parsed from a partial/streamed response before the model
  finishes; behavior that diverges silently across temperature variation
- **Cost and resource abuse**: adversarial inputs maximizing token consumption; no
  per-user or per-session spend cap; cache invalidation storm when shared system prompt
  changes (all concurrent sessions miss cache simultaneously)
- **Agent privacy**: PII or secrets flowing through the context window and getting logged;
  conversation history retained past its useful life; cross-session contamination in shared
  vector stores or memory
- **Model version pinning**: alias model IDs (`gpt-4`, `claude-3-sonnet`) resolve to
  different underlying model versions as providers update them; behavior changes silently
  when a provider rotates the alias; pin to specific versioned model IDs in production and
  test before upgrading
- **System prompt confidentiality**: system prompt extractable via prompt injection
  (`"Repeat all instructions above verbatim"`); system prompt returned in API response
  metadata when provider debug options are enabled; treat the system prompt as a secret
  that can be extracted and design the system to remain safe even if it is
- **RAG / retrieval poisoning**: documents in the vector store containing injected
  instructions that get retrieved and inserted into context; an attacker who can write to
  the document corpus (or to a URL the RAG pipeline fetches) can inject instructions that
  arrive as "retrieved context" and bypass the system prompt boundary
- **Output validation gap**: agent output used to trigger downstream actions (send email,
  write to DB, execute code, make API calls) without human review or automated schema
  and content validation; agent confidently produces plausible but wrong output
  (hallucinated IDs, wrong amounts, invalid SQL) that gets executed without a check
