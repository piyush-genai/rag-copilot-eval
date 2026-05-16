# AGENTS.md - GitLab On-Call Runbooks

## Overview

This is the `gitlab-com/runbooks` project — the source of truth for GitLab.com's monitoring, alerting, dashboards, and on-call runbooks. Everything is managed as code using **Jsonnet** (not Terraform).

- **GitLab URL**: <https://gitlab.com/gitlab-com/runbooks>
- **Grafana**: <https://dashboards.gitlab.net>
- **Mirrored to**: <https://ops.gitlab.net/gitlab-com/runbooks> (deployments happen from ops)

See also:

- [ARCHITECTURE.md](ARCHITECTURE.md) — system design, data flows, lifecycles
- [CONVENTIONS.md](CONVENTIONS.md) — coding standards, formatting, naming, testing

## Grafana Dashboards

This project also manages Grafana dashboards deployed to <https://dashboards.gitlab.net>. Dashboard source files live in `dashboards/` — see [`dashboards/AGENTS.md`](dashboards/AGENTS.md) for the development guide.

## Common Commands

```bash
# Install dependencies
./scripts/prepare-dev-env.sh    # First-time setup
make jsonnet-bundle             # Download jsonnet vendor deps

# Generate all outputs
make generate                   # Generate rules, dashboards, etc.

# Validate
make verify                     # Shellcheck + format check
make test                       # Full test suite (dashboards, rules, jsonnet tests)
make validate-mimir-rules       # Validate Mimir rules per tenant
make test-alertmanager          # Validate alertmanager config

# Test specific files
scripts/jsonnet_test.sh <file>_test.jsonnet          # Jsonnet unit test
bundle exec rspec spec/<path>_spec.rb                # RSpec integration test

# Format
make fmt                        # Format all (jsonnet + shell)
make jsonnet-fmt                # Format jsonnet only
```

## CI/CD Structure

CI runs on **both** gitlab.com and ops.gitlab.net (mirrored). Key jobs:

| Job                                    | Stage    | Where                       | What                                       |
| -------------------------------------- | -------- | --------------------------- | ------------------------------------------ |
| `ensure-generated-content-up-to-date`  | test     | gitlab.com                  | Verifies `make generate` produces no diff  |
| `test-jsonnet`                         | test     | gitlab.com                  | Runs jsonnet unit tests                    |
| `test-dashboards`                      | test     | gitlab.com                  | Dry-run dashboard upload                   |
| `deploy-dashboards`                    | deploy   | gitlab.com (main only)      | Uploads dashboards to Grafana              |
| `validate-mimir-rules`                 | validate | ops.gitlab.net              | `mimirtool rules check`                    |
| `deploy-mimir-rules`                   | deploy   | ops.gitlab.net (main only)  | `mimirtool rules sync`                     |
| `deploy-alertmanager`                  | deploy   | ops.gitlab.net (main only)  | Deploys alertmanager config                |
