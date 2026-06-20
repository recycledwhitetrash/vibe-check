<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### ETL / data pipeline lenses

- **Idempotency**: can the pipeline be re-run after a failure without double-loading,
  duplicating records, or corrupting state? is there a natural key or dedup strategy?
- **Watermarking / incremental correctness**: can records be skipped or double-loaded when
  the source changes during a run? is the high-water mark written atomically with the data?
- **Checkpoint atomicity**: if the job crashes at 80%, does it resume from the right offset,
  or does it restart from zero and double-load the first 80%? is the checkpoint file written
  atomically (write-then-rename) or in-place?
- **Dead-letter handling**: where do rejected or unparseable records go? are they observable?
  is there a threshold beyond which the job fails rather than silently dropping rows?
- **Schema evolution**: what happens when the source adds, removes, or renames a column?
  does the pipeline fail hard, silently drop the new column, or handle it gracefully?
- **Row-count / hash reconciliation**: is there a check that source row count equals
  destination row count after load? is there a hash or checksum check?
- **Data type coercion**: silent truncation (`BIGINT` → `INT`), float precision loss,
  string-to-date parsing with wrong locale or format, null vs. empty string conflation
- **Large dataset handling**: streaming vs. buffering — does the pipeline load the full
  dataset into memory? chunking strategy? disk exhaustion on temp output?
- **Rollback**: if the load fails mid-flight, what state is the destination in? is there
  a rollback procedure, or do you need to manually clean up?
- **Source credential security**: credentials for source systems (DB connection strings,
  API keys for data providers) hardcoded in pipeline config, DAG definitions, or
  `dbt profiles.yml` committed to git; no rotation mechanism for long-lived pipeline
  credentials; service accounts with read access to production data used by dev/staging
  pipelines
- **PII in pipeline metadata**: raw PII appearing in error messages, dead-letter records,
  Airflow task instance logs, or monitoring dashboards; pipeline operators can read PII
  via the monitoring UI without being authorized to access production data; PII should be
  masked or tokenized in all metadata and observability outputs
- **Cross-environment data leakage**: pipeline configured to read from production but
  write to staging, or vice versa; environment-specific connection config not validated
  at startup; accidental write of production PII to a staging database with different (or
  absent) access controls
- **Out-of-order record handling**: pipeline assumes records arrive in source order;
  late-arriving or out-of-order events cause incorrect aggregations, window computations,
  or state transitions; no out-of-order tolerance window or late-event handling strategy
  defined
- **Secrets in orchestration tools**: Airflow `Connection` objects storing plaintext
  passwords exportable via the Airflow REST API or visible in the UI to any DAG author;
  Prefect blocks or Dagster resources not using the secrets manager integration; pipeline
  run parameters containing credentials logged by the orchestrator
