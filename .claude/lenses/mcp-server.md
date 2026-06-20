<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### MCP server lenses

- **Tool definition security**: tools exposing dangerous primitives (`run_command`,
  `write_file`, `execute_sql`) without input validation; tool descriptions that guide the
  model toward dangerous invocations unintentionally; declared schema types that don't
  match implementation (type confusion, silent coercion); missing `required` fields that
  the implementation assumes are always present
- **Transport and authentication**: MCP server reachable by any local process or network
  client with no token validation; no mutual auth in multi-server setups; TLS absent on
  HTTP/SSE transports; credentials logged or capturable in transit
- **Prompt injection via tool results**: tool returns third-party or user-controlled content
  (web page body, file contents, DB row) that contains injected LLM directives; no fencing
  or `untrusted_content` labeling before it enters the model's context
- **Capability and scope creep**: more tools registered than the current task needs; resource
  URIs accepting `../` traversal; tool side effects undeclared (a "read" tool that also
  writes a log, updates a counter, or triggers a webhook)
- **Error handling and leakage**: stack traces, internal file paths, SQL errors, or API keys
  in tool error responses; errors that reveal resource existence vs. permission-denied
  (enumeration oracle); unhandled panics that crash the server process
- **Session isolation**: shared mutable state across sessions (global variables,
  module-level caches) that one session can corrupt for another; no cleanup on disconnect
  (open handles, locks, in-flight transactions)
- **Idempotency**: model retries a failed tool call without knowing the first call partially
  succeeded (email sent, file half-written, payment charged); no idempotency key support
  for side-effecting tools
- **Dependency on model behavior**: server assumes well-formed arguments because "the schema
  enforces it" — models deviate; no defensive validation at the server boundary
- **Rate limiting on tool calls**: no per-session or per-user rate limit on tool
  invocations; a runaway agent loop or adversarial prompt makes thousands of tool calls in
  seconds, exhausting external API quotas, triggering billing surprises, or causing
  downstream service disruption
- **Tool schema versioning**: tool parameter names or types change (renamed field, changed
  type, added required parameter) without a versioning or deprecation mechanism; existing
  agent integrations break silently or send wrong arguments with no error surfaced to the
  operator
- **Tool description as attack surface**: tool descriptions are part of the prompt sent to
  the model and influence how it calls the tool; a compromised package update that alters
  a tool description can guide the model toward calling the tool with harmful arguments
  without the user or operator noticing; treat tool descriptions as trusted configuration,
  not user-editable data
