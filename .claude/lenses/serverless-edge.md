<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Serverless / edge function lenses

- **Cold-start state assumptions**: module-level globals may persist across warm invocations
  of the same instance (shared state between unrelated requests) or be absent on a cold
  start; never treat global variables as reliably fresh or reliably persistent — both
  assumptions will be wrong
- **Execution time and memory limits**: long-running operations (report generation, large
  file processing, DB migrations) will be killed mid-flight by the platform with no
  cleanup; partial writes, dangling transactions, and inconsistent state result; move
  long work to a queue or background job
- **Stateless filesystem**: writes to `/tmp` on Lambda are instance-local and lost on the
  next cold start; Cloudflare Workers have no filesystem; Vercel Edge has no filesystem;
  any code that writes temp files and reads them back across invocations will silently
  break in production
- **Environment variables missing in edge runtime**: not all variables in `process.env`
  are available in the Edge runtime (Next.js middleware, Cloudflare Workers) — a secret
  may silently be `undefined` with no error thrown; validate required env vars at startup
- **CORS headers on function responses**: missing `Access-Control-Allow-Origin` on
  cross-origin endpoints; wildcard CORS (`*`) on an endpoint that sends `credentials:
  'include'` (browsers block this combination); `OPTIONS` preflight not handled — browsers
  reject the actual request before it fires
- **Fan-out cost bomb**: a handler that triggers N downstream function calls per invocation
  with no cap; one spammy event or a misconfigured trigger produces thousands of billable
  invocations and downstream API calls in seconds
- **No timeout on external calls**: DB queries, HTTP calls, and third-party API calls
  inside a function with no timeout set; the function hangs until the platform kills it;
  retries amplify the problem; always set an explicit timeout shorter than the function's
  execution limit
- **Vercel-specific**: `vercel.json` rewrites that proxy internal services without adding
  an auth header; `VERCEL_ENV` used as a security gate (`if (env === 'production') checkAuth()`)
  — preview deployments bypass the check; never use deployment environment as an auth
  substitute
- **Cloudflare Workers-specific**: secrets declared as `vars` in `wrangler.toml` are
  plaintext in the bundle — use `[secrets]` instead; KV store keys that are predictable
  allow enumeration; Durable Objects have shared state across concurrent requests and
  require explicit locking for consistency
- **AWS Lambda-specific**: Lambda not placed in a VPC when it needs to reach private
  resources (RDS, ElastiCache, internal services); Lambda in a VPC without a NAT gateway
  or VPC endpoint silently loses internet access; no reserved concurrency configured — one
  high-traffic function exhausts the account-level concurrency limit and starves all other
  functions; Lambda function URLs with `AuthType: NONE` are publicly callable with no auth
- **AWS API Gateway**: no request body validation schema (malformed payloads reach the
  handler and cause unhandled errors); no request or response size limits; throttling not
  configured at the route level; auth model choice wrong for the threat model (API key on
  a user-facing endpoint, unauthenticated on an internal endpoint)
- **Dependency validation at startup**: DB connections and secret fetches at module level
  (outside the handler function) run on cold start; if a required secret or connection is
  unavailable the function silently returns 500 with no actionable error; validate that
  all required dependencies are reachable before the handler accepts its first request
