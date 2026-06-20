<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### PostgreSQL / SQL lenses (standalone, non-Supabase)

- **Authorization**: which roles can call this function or access this table? is `SECURITY
  DEFINER` used and is `search_path` locked? are column-level permissions correct?
- **SQL injection**: dynamic SQL built with string concatenation or `format()` — are all
  user-supplied values parameterized? `EXECUTE` with `USING` vs. string interpolation
- **Query correctness**: plan stability under data growth, `EXPLAIN` reviewed for sequential
  scans, `NULL` semantics in `WHERE` / `JOIN` conditions, aggregate edge cases (empty set,
  single row)
- **Transaction boundaries**: is this query inside the right transaction boundary? autocommit
  assumptions?
- **Row-level security**: Postgres supports RLS independently of Supabase; tables
  containing multi-tenant or user-scoped data should have RLS enabled with correct
  policies; `ALTER TABLE t ENABLE ROW LEVEL SECURITY` with no policies attached defaults
  to deny-all for non-superusers — verify that is intentional and not an accident
- **Connection security**: `pg_hba.conf` with `trust` authentication on local or network
  connections (any OS user connects as any Postgres role without a password); SSL not
  required for remote connections (`sslmode=disable` accepted); `listen_addresses = '*'`
  combined with a permissive `pg_hba.conf` exposes the DB to the network
- **Privilege escalation paths**: `GRANT` chains that allow an unprivileged application
  role to reach superuser-level operations; `COPY TO/FROM PROGRAM` available to a role
  that processes user-supplied input (OS command execution); `CREATE EXTENSION` granted to
  a non-superuser who can then load dangerous extensions (e.g. `plpythonu`)
- **Audit logging**: `log_statement` and `log_min_duration_statement` not configured (no
  visibility into slow or suspicious queries in production); connection attempt logging
  disabled; `pgaudit` extension not installed for compliance-grade audit trails
- **Index correctness**: partial index predicate does not match the actual query predicate
  — index exists but is never used; expression index on a mutable or volatile expression;
  missing indexes on FK columns used in joins causing full sequential scans; covering
  index opportunities missed on hot read paths
