<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Universal lenses — always apply

- **Correctness**: off-by-one, wrong branch taken, illegal state transitions, NULL/nil
  handling, comparison operators, ordering, default values that violate invariants,
  logic errors in conditions; integer overflow/underflow on arithmetic involving user-
  supplied values (amounts, counts, offsets); type confusion where the same variable holds
  different types across branches; boundary conditions on empty collections and single-
  element collections specifically (off-by-one is most common at the edges);
  algorithmic complexity — O(n²) or worse from nested loops over the same collection,
  `find`/`filter` inside `map`/`forEach`, repeated sorting of the same list, or string
  concatenation in a loop; consider whether a hash/set/map lookup would replace a
  linear scan
- **Error handling**: swallowed exceptions/errors, non-fatal treatment of fatal conditions,
  partial failure leaving inconsistent state, missing rollback, fallbacks that silently mask
  bugs; for scripts: exit codes not checked, `pipefail` absent, `2>/dev/null` on errors
  that should be fatal; retryable vs non-retryable errors not distinguished — retrying a
  non-retryable error forever wastes resources and delays failure, dropping a retryable
  error silently loses work; panic/crash recovery boundary wrong (`recover` in Go,
  `catch_unwind` in Rust) — panic caught too broadly masking bugs, or not caught at the
  right boundary causing process crash
- **Observability & audit**: missing log points where forensics will need them, sensitive
  actions not recorded, audit records that can be erased or overwritten, metrics gaps on
  hot paths, no way to correlate events after an incident; unstructured log messages that
  can't be queried in production incident tools; correlation/trace IDs not propagated
  across service or function calls (can't reconstruct a full request path post-incident);
  health check or readiness endpoint returning 200 even when the service is degraded
  (downstream load balancer keeps sending traffic to a broken instance)
- **Privacy & compliance**: PII in logs, errors, or payloads; data retained longer than
  promised; exports or responses that include more than the caller needs; cross-tenant or
  cross-user data leakage in shared resources; GDPR/CCPA right-to-erasure — does a delete
  actually remove data from all stores (backups, audit logs, caches, analytics pipelines)
  or only the primary DB? data minimization at collection — is the system collecting more
  fields than it needs?
- **Configuration & deploy**: env vars referenced but not declared; secrets in code, logs,
  or error messages; feature flags with no kill switch; assumptions about deploy environment
  baked into logic; config validated at startup (fail fast, clean error) vs at first use
  (fails mid-request, partial state); behavior differences across environments that mask
  bugs (e.g. a dev default that hides a prod misconfiguration)
- **Dependencies & supply chain**: lockfile drift vs. pinned versions, deprecated APIs,
  risky transitive packages, packages with known CVEs; typosquatting — package name one
  character off from a popular one (e.g. `lodahs` instead of `lodash`); `postinstall`
  scripts in npm/yarn packages executing arbitrary code at install time — check unfamiliar
  packages for these; `git+https://` dependencies where the commit can be force-pushed
  after your audit; `--frozen-lockfile` / `--ci` / `npm ci` not used in the build pipeline
  so the lockfile can drift silently between dev and CI
- **Test integrity**: tests that pass without actually exercising the claim, mocks that hide
  real production behavior, snapshot tests that auto-update (`--updateSnapshot`) without human
  diff review — they always pass because they overwrite their own expected output; tests
  asserting on implementation details (private method calls, internal state) rather than
  observable behavior — pass when the bug exists; flaky tests marked `.skip`, `xit`, or
  `@pytest.mark.skip` without a tracking issue or removal deadline; missing teardown that
  causes test pollution; bad async handling (`setTimeout` instead of `act()`). **Scope
  limit:** do NOT enumerate missing test scenarios or coverage gaps in test files — that is a
  vc-ship quality gate concern, not an audit finding. Only correctness issues in existing
  tests qualify.
- **Documentation & comments**: contradicts the code, references removed code, claims
  invariants that are no longer true, missing where a future reader would otherwise make a
  wrong assumption
- **Encoding / serialization**: JSON/CSV/XML injection when building output from user input,
  numeric precision loss across serialization (float → string → float), length limits not
  enforced before writing, character encoding assumptions (UTF-8 vs Latin-1 vs system
  locale); Python `yaml.load()` on user-controlled input executes arbitrary code —
  must be `yaml.safe_load()`; XML External Entity (XXE) injection when parsing XML from
  untrusted sources without disabling external entity resolution; prototype pollution in
  JavaScript via `JSON.parse()` on objects with `__proto__` or `constructor` keys (affects
  object-spread and property access on shared prototypes)
- **Resource management**: file descriptor or socket leaks on error paths, DB connections
  not returned to pool, temp files not cleaned up, no size or quota check before writing
  large output, cleanup missing on SIGTERM/SIGKILL; connection pool exhaustion under
  sustained load — all connections checked out, new requests queue indefinitely or time
  out; goroutine or thread leaks from spawned workers that are never joined or cancelled;
  memory leaks from closures capturing large objects that are never released
- **Maintainability**: dead code — variables assigned but never read, functions defined
  but never called (check with the Grep tool across the repo), imports no longer
  referenced after this change; magic numbers — bare numeric literals used in logic
  (thresholds, limits, retry counts, timeouts) that should be named constants; hardcoded
  URLs, hostnames, or ports that belong in config; DRY violations — similar code blocks
  (3+ lines) copy-pasted in the diff where a shared helper would remove the duplication;
  conditional side effects — one branch updates a related record, emits an event, or
  writes a log but a sibling branch silently skips that same step; module boundary
  violations — a caller reaching into another module's internals directly, or database
  queries placed in layers (controller, view, route handler) that don't own data access
- **API contract**: applies when the diff touches routes, endpoints, or response shapes —
  regardless of language or framework (Node/Express, Python/Flask/FastAPI/Django REST,
  Go, Ruby/Rails, etc.); breaking changes to response shape — removed or renamed fields,
  changed field types (string → number, object → array), new required request parameters
  added without a default; changed HTTP methods or status codes on existing endpoints;
  versioning strategy inconsistency (mixing URL-path `/v1`, header, and query-param
  versioning in the same API); error response format inconsistent with other endpoints in
  the codebase; list endpoints with no pagination and no `LIMIT` that grow unboundedly
  with data; rate limiting absent on an endpoint where similar endpoints have it; API
  documentation (OpenAPI/Swagger spec, README) not updated to match changed behavior;
  backwards compatibility for clients that can't force-update (mobile apps, third-party
  integrations, older SDK versions that may still be in use)
- **Cryptographic misuse**: weak hashing algorithms (MD5, SHA1) used for security-sensitive
  operations such as password storage or token generation; predictable randomness
  (`Math.random()`, Python `random`, `rand()`) used to generate tokens, session IDs,
  nonces, or CSRF values — must use a cryptographically secure RNG; non-constant-time
  comparison (`==`, `===`, `string.compare()`) on secrets, HMAC digests, or API tokens
  enables timing attacks that reveal whether a guess is correct; hardcoded encryption
  keys or initialization vectors; missing salt in password hashing (bcrypt/argon2 handle
  this automatically; hand-rolled hashing often forgets it)
- **Anything else**: if it smells wrong and doesn't fit a category, surface it. The lenses
  are a starting point, not a scope boundary.
