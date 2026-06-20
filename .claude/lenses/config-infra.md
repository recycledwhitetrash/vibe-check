<!-- AUTO-GENERATED from src/vc-audit-lenses.md.tmpl — do not edit directly -->
### Infrastructure / config lenses

- **Secret sprawl**: secrets in environment variables that get logged, in config files
  committed to git, in build artifacts, in container images
- **Blast radius of misconfiguration**: what is the worst-case impact if this config value
  is wrong in production? is there a validation step before the config is applied?
- **Terraform / IaC**: resource recreation vs. update (destroys live data?), missing
  `prevent_destroy`, state drift between plan and apply, IAM over-permissioning
- **Container / image**: running as root when not needed, secrets baked into image layers,
  base image not pinned, no health check, ports exposed unnecessarily
- **Network security**: security groups or firewall rules with `0.0.0.0/0` inbound on
  sensitive ports (22 SSH, 3306 MySQL, 5432 Postgres, 6379 Redis, 27017 MongoDB); no
  egress filtering — any compromised workload can exfiltrate data or establish a C2
  callback; VPC peering with no traffic restriction between peers (full mesh access)
- **IAM / access control**: IAM policies with `Action: "*"` or `Resource: "*"`;
  service accounts with project-level or account-level permissions when resource-scoped
  permissions would suffice; long-lived access keys with no rotation policy and no
  last-used monitoring; MFA not enforced for console access or privilege-escalation API
  calls
- **Kubernetes security**: pods running as root (`runAsNonRoot` not set); `hostNetwork:
  true`, `hostPID: true`, or `privileged: true` granting host-level access; `hostPath`
  mounts exposing the host filesystem to container workloads; Kubernetes Secrets not
  encrypted at rest (etcd encryption not configured); RBAC with `cluster-admin` bound too
  broadly; no `NetworkPolicy` resources — any pod can reach any other pod on any port
- **Logging and monitoring**: no centralized log aggregation; logs stored only on the host
  they describe (lost on instance termination); CloudTrail / GCP Audit Logs / Azure
  Activity Log disabled or retention set too short; no alerting on privilege escalation
  events, new IAM policy attachments, or access from unexpected regions or IPs
- **CI/CD pipeline security**: secrets in CI environment variables printed in build logs
  when a step fails or when `set -x` is active; pipeline steps running with repo-wide
  write permissions instead of scoped tokens; GitHub Actions workflows triggered by
  `pull_request_target` from forked repos with `secrets` accessible — allows a fork's PR
  to exfiltrate repository secrets
- **Backup and recovery**: no automated backup policy for stateful resources (managed
  databases, object storage without versioning); backups never tested with a restore drill
  (backup exists but may not be restorable); single-region deployment with no cross-region
  replication or failover plan for data that must survive a regional outage
