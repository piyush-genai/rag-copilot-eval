# Conventions

## Commit Messages

Conventional Commits (`fix:`, `feat:`, `BREAKING CHANGE:`) — triggers semantic versioning and Docker image builds.

## Formatting

- **Jsonnet**: `jsonnetfmt --string-style s -n 2` (enforced by CI)
- **Shell**: `shfmt -i 2 -ci` (enforced by CI)

## Naming

- **Dashboards**: `<name>.dashboard.jsonnet` in `dashboards/<folder>/`
- **Shared dashboards**: `.shared.jsonnet` extension for multi-dashboard files
- **Protected dashboards**: Add `protected` label or list in `protected-grafana-dashboards.jsonnet`

## Testing

### Jsonnet Unit Tests

Same directory as source, with `_test.jsonnet` suffix:

- `services/stages.libsonnet` -> `services/stages_test.jsonnet`

### RSpec Integration Tests

Mirror directory structure under `spec/`, with `_spec.rb` suffix:

- `libsonnet/toolinglinks/grafana.libsonnet` -> `spec/libsonnet/toolinglinks/grafana_spec.rb`
