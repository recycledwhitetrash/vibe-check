<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Supabase / PostgREST lenses

- **Security & authorization**: RLS `USING` vs `WITH CHECK` asymmetries (a row readable ≠
  row writable — check both); column-level GRANTs missing; `SECURITY DEFINER` functions
  without explicit `search_path`; JWT claim trust (which claims does your RLS actually verify
  and where could they be spoofed?); signed URL leakage; role/tier escalation paths;
  multi-tenant row isolation — can user A ever see user B's rows?
- **Attack vectors / bypasses**: UPDATE-defeats-INSERT-check (INSERT policy blocks a row but
  UPDATE policy allows transforming an existing row into that state); cascade-vs-immutability
  collisions (FK cascade deletes rows the policy was supposed to protect); RLS-vs-RPC duality
  (a `SECURITY DEFINER` function runs as the defining role, bypassing the caller's RLS
  entirely — is that intentional?); clone/table-inheritance bypasses; side channels (timing,
  error message differences, behavioral differences that reveal row existence); audit-bypass
  via column un-set instead of hard delete
- **Concurrency & races (database)**: TOCTOU — check then act with no lock; transaction
  isolation level too low for the operation; missing `SELECT FOR UPDATE` where needed;
  idempotency on retries; lost updates (last-write-wins when it shouldn't); double-fire on
  triggers; trigger on wrong event (AFTER vs BEFORE, row vs statement)
- **Data integrity**: missing CHECK constraints, missing FK, missing UNIQUE, NOT NULL gaps
  where null would violate a business rule, denormalization drift (cached column disagrees
  with source), orphan rows when parent is deleted, soft-delete invariants not enforced at
  DB level
- **Performance (database)**: N+1 queries in RPC or edge function; missing indexes on FK,
  filter, and sort columns; oversized payloads with no `LIMIT`; function volatility wrong
  (`VOLATILE` when `STABLE` is safe); sequential scans on hot paths; redundant `SELECT`s;
  statement-level trigger where row-level is needed (or vice versa); lock contention
- **Migration safety**: DDL that takes a lock blocking writes on large tables; `NOT VALID`
  needed for constraint backfills; rollback path for each migration; data backfills that can
  fail mid-flight leaving partial state; ordering of dependent migrations; can the migration
  be re-run safely?
- **API & contract (Supabase)**: breaking response shape changes, edge function CORS/auth
  headers, request size limits, RPC signatures that have drifted from generated TypeScript
  types
- **Realtime channel auth**: Supabase Realtime subscriptions require channel-level
  authorization separate from Postgres RLS; RLS policies on the table do not automatically
  protect realtime event streams; a client can subscribe to a table's changes and receive
  rows that a direct query would deny; verify channel filters and auth checks in Realtime
  subscription handlers
- **Storage policies**: Supabase Storage has its own policy system independent of Postgres
  RLS; objects in a public bucket are accessible at a predictable URL regardless of the
  user's auth state; signed URLs generated with no expiry or a very long expiry (default
  can be up to 1 year) provide permanent access after the sharing context expires; Storage
  policies are often left at permissive defaults
- **Auth configuration**: OAuth redirect URIs not locked down in the Supabase dashboard —
  any redirect target accepted (open redirect); email confirmation disabled, allowing
  unverified addresses to access protected data immediately; magic link expiry set too long;
  PKCE flow not enforced for OAuth (auth code interception attack possible without it)
- **pg_net / pg_cron attack surface**: `pg_net` (HTTP requests from inside Postgres)
  available to non-superuser roles enables SSRF from the database tier to internal
  services or cloud metadata endpoints; `pg_cron` jobs executing SQL as a privileged role
  on a schedule — is the job SQL static or influenced by table data an attacker can write?
  both extensions are enabled by default in many Supabase projects
