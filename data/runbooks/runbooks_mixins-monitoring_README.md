
# Understanding Mixins

This readme includes the basic of how to create new mixin.

## Mixins

A mixin is a set of Grafana dashboards and Prometheus rules and alerts, packaged together in a reuseable and extensible bundle. Mixins are written in jsonnet, and are typically installed and updated with jsonnet-bundler. This promotes consistency, efficiency, and maintainability across your monitoring infrastructure.

### Benefits of Mixins

- **Modularity:** Break down configurations into reusable components.
- **Maintainability:** Easier to update and manage individual mixins.
- **Code Reusability:** Share common configurations across different environments.
- **Organization:** Keep your code well-structured and improve readability.

### Further Reading

The [monitoring.mixins.dev website](https://monitoring.mixins.dev/) has excellent further reading, as does [the docs section on the monitoring-mixins repo](https://github.com/monitoring-mixins/docs) on GitHub.
This is a really good [video introduction](https://promcon.io/2018-munich/talks/prometheus-monitoring-mixins/) to mixins and jsonnet.

## Mixtool

Mixtool is a command-line tool designed to simplify working with mixins. It helps you:

- **Manage mixins:** Install, update, and remove mixins.
- **Generate output:** Generate the final configuration files for Grafana and Prometheus.

### Setting Up Mixtool

You can install mixtool by running the script `./scripts/prepare-dev-env.sh`.

### Using Mixins

Mixins offer a modular approach to building configurations for Prometheus and Grafana. Here's a basic workflow:

1. Create Configuration File (config.libsonnet): This file defines your main configuration and utilizes mixins:

```jsonnet
{
    _config+:: {
    gitlabMetricsConfig+:: gitlabServiceMetricsConfig,
    # Other configurations also go here
    },

    prometheusRulesGroups+:: aggregationRulesForServices(self._config),
    prometheusAlertsGroups+:: alertsForServices(self._config)

}
```

- `gitlabMetricsConfig+::`: containing service definiation metrics configurations.
- `prometheusRulesGroups+::` Uses the `aggregationRulesForServices` to generate Prometheus rules based on the `gitlabMetricsConfig`.
- `prometheusAlertsGroups+::` Uses the `alertsForServices` mixin to generate alert rules based on the `gitlabMetricsConfig`.

2. Create Mixin File (mixin.libsonnet): This file combines all your individual mixins:

```jsonnet
(import 'config.libsonnet') +
(import 'alerts/alerts.libsonnet') +
(import 'dashboards/dashboards.libsonnet') +
(import 'rules/rules.libsonnet')
```

3. The `generate-mixin.sh` script is designed to generate Prometheus configurations (alerts, rules, dashboards) using `mixtool` based on the provided `mixin.libsonnet` file. The outputs are stored in directories under `generated/{MIXIN_DIR}`.

```sh
./generate-mixin.sh  {alerts|rules|dashboards|all}  MIXIN_DIR
```
