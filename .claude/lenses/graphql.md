<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### GraphQL lenses

- **Introspection enabled in production**: exposes the full schema — every type, field,
  argument, and relationship — to any unauthenticated caller; attackers use it to map the
  entire API surface before probing; disable or restrict introspection in production
- **No query depth limit**: `{ user { friends { friends { friends { ... } } } } }` is
  valid GraphQL; without a max depth, a single query generates exponential resolver calls
  and DB hits; set a depth limit (typically 5–7 for most schemas)
- **No query complexity limit**: depth limits alone are not enough — a wide query (100
  fields, each resolving 100 items) has low depth but high cost; assign a complexity score
  per field and reject queries that exceed a budget
- **Field-level authorization missing**: the entry-point resolver checks auth, but a
  nested field (e.g., `user.paymentMethods`, `order.internalNotes`) has no authorization
  check of its own; an attacker constructs a query that reaches the sensitive field through
  a permitted entry point
- **N+1 from resolvers**: each resolver fires independently; a list of 100 users each
  resolving a `posts` field makes 100 DB calls; use DataLoader or query batching to
  coalesce resolver calls — without it the endpoint is a denial-of-service vector
- **Mutation authorization separate from query**: being able to `query { user(id: X) }`
  does not mean the caller can `mutation { updateUser(id: X, ...) }`; check authorization
  independently on every mutation, not just on read operations
- **Batched query abuse**: if the server accepts an array of operations in one request,
  rate limits counted per-request are trivially bypassed; either disable batching or apply
  rate limits per operation within a batch
- **Error messages leaking internals**: default GraphQL error responses include resolver
  stack traces, SQL query text, internal field names, and file paths; production servers
  must map errors to safe messages and log details server-side only
- **Subscription authorization**: GraphQL subscriptions run over a persistent WebSocket;
  auth checked on the HTTP upgrade request but not validated on each subscription event;
  subscription filters enforced client-side only — a subscriber receiving all events and
  filtering locally sees all events before filtering; server must scope each subscription
  to the authenticated user
- **File upload security**: GraphQL multipart upload (`graphql-multipart-request-spec`)
  with no file size limit, no content-type or extension validation, and no path traversal
  check on the storage destination — same risks as any file upload endpoint but less
  visible because it's handled inside the GraphQL layer
- **Persisted queries not enforced in production**: server accepts arbitrary ad-hoc
  queries rather than only pre-registered persisted query IDs; persisted queries eliminate
  the depth/complexity/introspection attack surface entirely because only pre-approved
  queries are accepted; ad-hoc queries should be disabled in production if the client only
  ever needs a known set of operations
- **Federation / schema stitching boundary**: in a federated setup (Apollo Federation,
  GraphQL Mesh), each subgraph must enforce authorization independently; if only the
  gateway checks auth and a subgraph is directly reachable (misconfigured network, exposed
  internal port), all auth is bypassed entirely
