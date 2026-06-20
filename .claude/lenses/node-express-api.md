<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Node / Express API lenses

- **Async handler errors are not caught (Express 4)**: a `throw` or rejected promise inside
  an `async (req, res)` route handler is NOT caught by Express 4's error pipeline — it
  becomes an unhandled rejection. The request hangs until the client times out, and on
  newer Node the process may crash. Every async handler needs try/catch (with `next(err)`)
  or an async wrapper (`express-async-handler`, or a `Promise.resolve(fn).catch(next)`
  helper). Express 5 fixes this — confirm which major version is in use before trusting it.
- **Error-handling middleware signature**: error handlers MUST take four args
  `(err, req, res, next)`. With three args Express treats it as a normal middleware and the
  error falls through to the default handler — which in non-production leaks the stack trace
  to the client. Verify the error handler is registered LAST (after all routes) and has the
  4-arg signature.
- **Response not returned / sent twice**: code after `res.send()`/`res.json()` keeps
  executing because the call does not stop the function — a missing `return` leads to a
  second send and `ERR_HTTP_HEADERS_SENT`, or to logic running after the response. Also the
  inverse: a branch that never sends a response and never calls `next()` leaves the request
  hanging until timeout.
- **`next()` misuse**: not calling `next()` in a middleware (request hangs); calling `next()`
  AND sending a response (double-handling); calling `next(err)` then also sending a response.
- **Untrusted request fields fed straight to a sink**: `req.body`, `req.query`, `req.params`,
  and `req.headers` are all attacker-controlled. Mass assignment (`Model.create(req.body)` /
  `Object.assign(record, req.body)`) lets a caller set fields they shouldn't (role, ownerId,
  isAdmin). `req.params.id` interpolated into SQL or a filesystem path is injection / path
  traversal.
- **Query/body type confusion**: Express parses `?a=1&a=2` into an array and (with the
  `extended` query parser, the default) `?a[b]=c` into an object. Handler code that assumes
  a string then calls `.trim()`/`.toLowerCase()` throws on the array/object form; a value
  passed to a NoSQL query (`{ user: req.query.user }`) becomes an operator-injection vector
  (`?user[$ne]=`). Validate and coerce types at the boundary (zod/joi/express-validator).
- **No body size limit**: `express.json()` / `express.urlencoded()` without a `limit` accept
  arbitrarily large payloads — a single request can exhaust memory. Missing body parser
  entirely leaves `req.body` undefined and downstream destructuring throws.
- **Middleware ordering bugs**: auth/authorization middleware registered AFTER the route it
  should protect (route runs first); `express.static()` mounted before auth, exposing files;
  a catch-all (`app.use((req,res)=>...)` or `app.all('*')`) registered before real routes,
  shadowing them; body parser mounted after a route that needs `req.body`.
- **Event-loop blocking in the request path**: synchronous crypto (`crypto.pbkdf2Sync`,
  sync bcrypt), `fs.readFileSync`, `JSON.parse` on large payloads, or any CPU-heavy loop in
  a handler blocks ALL concurrent requests on that instance, not just the current one. Move
  heavy/sync work to async APIs or a worker thread/queue.
- **`trust proxy` and client IP spoofing**: behind a proxy/load balancer, `req.ip` and
  rate-limit/logging keyed on it are wrong unless `app.set('trust proxy', ...)` is configured
  to match the actual hop count. Setting `trust proxy` to `true` (trust everything) lets a
  client spoof `X-Forwarded-For` to bypass IP-based rate limits or poison logs.
- **CORS misconfiguration**: `cors()` with no options reflects/allows any origin; reflecting
  the request origin together with `credentials: true` is effectively `*` with cookies —
  any site can make authenticated cross-origin calls. Lock the allowlist and only enable
  credentials for trusted origins.
- **Missing rate limiting on expensive/auth routes**: login, password-reset, signup, search,
  and report endpoints with no rate limit invite brute-force and cost-abuse. An in-memory
  limiter (default `express-rate-limit` store) resets on restart and does not coordinate
  across instances — use a shared store (Redis) in multi-instance deployments.
- **Sessions and cookies**: `express-session` with a hardcoded/default `secret`, the default
  `MemoryStore` in production (leaks memory, breaks across instances), or cookies missing
  `httpOnly` / `secure` / `sameSite`. JWT in `localStorage` (XSS-readable) when an httpOnly
  cookie was the safer choice for the threat model.
- **Unhandled stream / emitter errors crash the process**: piping a request or file stream
  without an `'error'` listener — an emitted `'error'` with no handler throws and takes the
  process down. Same for `req`/`res` aborted mid-stream and for any `EventEmitter` in the
  hot path.
- **No graceful shutdown**: no `SIGTERM`/`SIGINT` handler to stop accepting connections,
  drain in-flight requests, and close DB pools — deploys and autoscaling drop live requests
  and can leave transactions half-applied. Process-level `unhandledRejection` /
  `uncaughtException` handlers that log-and-continue leave the process in a corrupt state;
  prefer log-and-exit (let the supervisor restart) over swallowing.
- **Regex route ReDoS**: a user-influenced value matched against a regex with catastrophic
  backtracking (nested quantifiers like `(a+)+`), whether in a route pattern or validation,
  lets one crafted input peg a CPU core and stall the event loop.
