# Reference Architecture Monitoring

This directory contains configuration to provide observability into other GitLab instances (not GitLab.com).

This is based off the same Service-Level Monitoring and Saturation Monitoring metrics used to monitor GitLab.com.

Each sub-directory contains a specific reference architecture, although for now, there is only one:

1. [`get-hybrid/`](get-hybrid/): this provides monitoring configuration, dashboards and alerts for a [GitLab Environment Toolkit (GET) Hybrid Kubernetes environment](https://gitlab.com/gitlab-org/quality/gitlab-environment-toolkit/-/blob/main/docs/environment_advanced_hybrid.md).

## Warning about Completeness

This is, at present, a work-in-progress. The plan is to start with a small subset of required metrics and expand it until the configuration covers all metrics critical to the operation of a GitLab instance.

The epic tracking this effort is here: <https://gitlab.com/groups/gitlab-com/-/epics/1721>. For up-to-date progress on the effort, consult the epic.

## How to use

From your chosen reference-architecture sub-directory, deploy:

* `config/prometheus-rules/*.yml` into your Prometheus
  * Multiple files exist here to prevent scenarios where the Prometheus Operator is unable to create ConfigMaps if files become too large in size.
* `config/dashboards/*.json` to Grafana

Details of how to deploy will vary by your chosen configuration management tooling which is beyond the scope of this documentation.

Ensure you are scraping the metrics from all required sub-systems, using the correct job name.  Precise details of what and how to scrape will vary by reference architecture, so the list below is to provide general guidance and commentary without being prescriptive, although it does assume you are using consul with `monitoring_service_discovery` enabled (see <https://docs.gitlab.com/ee/administration/monitoring/prometheus/>).  You may need to refer to the service definitions (`src/services/*.jsonnet`) to clarify some details.

| Service | Scrape details | Scrape job name required | Notes |
| ------- | -------------- | ------------------------ | ------ |
| consul | - | - | Looks for pods in the 'consul' namespace; monitoring is kubernetes-level only |
| gitaly | - | `gitaly` | `gitaly` consul service |
| gitlab-shell | - | - | Re-uses praefect metrics. This is a weak proxy until gitlab-shell has more accessible metrics (see [runbooks#88](https://gitlab.com/gitlab-com/runbooks/-/issues/88) |
| praefect | - | `praefect` | `praefect` consul service |
| redis | We provide client-side metrics emitted by any `rails` endpoint, webservice/sidekiq | - | - |
| registry | In kubernetes, the 'registry-prometheus' port | scrape job must be named `praefect` | - |
| sidekiq | - | /metrics | - |
| webservice (rails) | /-/metrics ; in kubernetes, on the `http-webservice` port | `gitlab-rails` | - |
| webservice (workhorse) | /metrics ; in kubernetes, on the `http-workhorse-exporter` port | `gitlab-rails` | - |

## Generating a Customized Set of Recording Rules, Alerts, and Dashboards

### Generation Steps

It's possible to customize the configuration of the reference architecture to suit your GitLab deployment.

* Step 1: Clone this repository locally: `git clone git@gitlab.com:gitlab-com/runbooks.git`

* Step 2: Check which version of `jsonnet-tool` is required by consulting the `.tool-versions` file, and install it from <https://gitlab.com/gitlab-com/gl-infra/jsonnet-tool/-/releases>. Alternatively, follow the **Contributor Onboarding** steps in [`README.md`](../README.md#contributor-onboarding) to setup your local development environment. This approach will use `asdf` to install the correct version of `jsonnet-tool` automatically.

* Step 3: create a directory which will contain your local overrides. `mkdir overrides`.

* Step 4: in the `overrides` directory, create an `gitlab-metrics-options.libsonnet` file containing the configuration options. Documentation around possible options is available in the [Options section](#options) later in the documentation. Reviewing the [default options](../libsonnet/reference-architecture-options/validate.libsonnet) can shed light on configuration options available.

* Step 5: optionally add local services in the `overrides` directory you want to include. Review some services defined in `/reference-architectures/get-hybrid/src/services` to understand how such a service would look like.

```jsonnet
// overrides/gitlab-metrics-options.libsonnet
{
  // Disable praefect
  praefect: {
    enable: false,
  }
  // Add your own locally defined services
  services: [
    import 'logging.libsonnet',
  ],
}
```

* Step 6: create a directory which will contain your custom recording rules and Grafana dashboards: `mkdir output`.

* Step 7: use the `generate-reference-architecture-config.sh` script to generate your custom configuration.

```shell
# generate a custom configuration, using the `get-hybrid` reference architecture,
# emitting configuration to the `output` directory, and reading overrides from the
# `overrides/` directory.
runbooks/scripts/generate-reference-architecture-config.sh \
    runbooks/reference-architectures/get-hybrid/src/ \
    output/ \
    overrides/
```

* Step 7: install the recording rules from `output/prometheus-rules/*.yml` into your [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/). Depending on the deployment, this can be done with the [Kube Prometheus Stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack) helm chart, local file deployment or another means.

* Step 8: install the Grafana dashboards from `output/dashboards/*.json` into your Grafana instance. The means of deployment will depend on the local configuration.

## Options

The following configuration options are available in `gitlab-metrics-options.libsonnet`.

| **Option** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `elasticacheMonitoring` | Boolean | `false` | Set to `true` to enable AWS Elasticache monitoring. |
| `minimumSamplesForMonitoring` | int | 3600 | Minimum operation rate thresholds. This is to avoid low-volume, noisy alerts. See [service-level-monitoring.md](../docs/metrics-catalog/service-level-monitoring.md) for more details. |
| `minimumOpsRateForMonitoring` | int | null | Minimum operation rate thresholds. This is to avoid low-volume, noisy alerts. See [service-level-monitoring.md](../docs/metrics-catalog/service-level-monitoring.md) for more details. |
| `praefect.enable` | Boolean | `true` | Set to `false` to disable Praefect monitoring. This is usually done when Praefect/Gitaly Cluster is disabled in GitLab Environment Toolkit with `praefect_node_count = 0` |
| `services` | Array | empty | Import any customized service monitoring. For examples see [`reference-architectures/get-hybrid/src/services/`](reference-architectures/get-hybrid/src/services/) |
| `saturationMonitoring` | Array | empty | Import any customized saturation monitoring. For examples see [`reference-architectures/get-hybrid/src/services/`](reference-architectures/get-hybrid/src/services/) |
| `rdsInstanceRAMGB` | int | null | Configure the size of the RAM for a given RDS instance. Specified in unit GB. |
| `rdsMaxStorageAllocationGB` | int | null | Configure the size of the maximum allocated storage for a given RDS instance. Specified in unit GB. |
| `rdsMaxConnections` | int | null | Configure the count of the maximum allowed connections for a given RDS instance. Specified as count. |
| `rdsMonitoring` | Boolean | `false` | Set to `true` to enable AWS RDS monitoring. |
| `useGitlabSSHD` | Boolean | `false` | Set to `true` to use GitLab SSHD instead of GitLab Shell. |
| `toolingLinks.opensearchHostname` | String | null | If provided, is the hostname of an OpenSearch instance with logs for the instance, and enables the generation of links to these logs from Grafana dashboards |
| `toolingLinks.defaultIndexPattern` | String | null | Mandatory if opensearchHostname is provided; the default index pattern where logs can be found in OpenSearch |
| `toolingLinks.indexPatterns` | Object | {} | Optional; is a map from index catalog entry names to OpenSearch index pattern names, to override the defaultIndexPattern if needed |
| `apdexThresholds.gitlabShell.satisfied` | float | 30.0 | Optional; sets the satisfied apdex threshold for the `gitlab-shell` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `apdexThresholds.gitlabShell.tolerated` | float | 60.0 | Optional; sets the tolerated apdex threshold for the `gitlab-shell` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `apdexThresholds.gitaly.satisfied` | float | 0.5 | Optional; sets the satisfied apdex threshold for the `gitaly` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `apdexThresholds.gitaly.tolerated` | float | 1.0 | Optional; sets the tolerated apdex threshold for the `gitaly` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `apdexThresholds.praefect.satisfied` | float | 0.5 | Optional; sets the satisfied apdex threshold for the `praefect` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `apdexThresholds.praefect.tolerated` | float | 1.0 | Optional; sets the tolerated apdex threshold for the `praefect` service. Must be one of the [defined prometheus buckets](https://gitlab.com/gitlab-org/gitaly/-/blob/master/config.toml.example). |
| `monitoring.sidekiq` | Object | {} | Optional. Empty `{}` means to use default thresholds for all SLIs. Otherwise, this is a map from SLI name to an object of shard name to a map of threshold overrides. Shards specified in this will be excluded from the default SLO and have a distinct SLO created for them with the override provided. Example:<br><pre lang="jsonnet">{<br>  sidekiq_execution: {<br>    'urgent-cpu-bound': {<br>      apdexScore: 0.995,<br>      errorRate: 0.9995<br>    }<br>  }<br>}</pre> |
| `monitoring.gitaly` | Object | {} | Optional. Empty `{}` means to use default thresholds. Otherwise, specify `monitoringThresholds` with `apdexScore` and/or `errorRatio` overrides. Example:<br><pre lang="jsonnet">{<br>  monitoringThresholds: {<br>    apdexScore: 0.998,<br>    errorRatio: 0.999<br>  }<br>}</pre> |
| `monitoring.webservice` | Object | {} | Optional. Empty `{}` means to use default thresholds. Otherwise, specify `monitoringThresholds` with `apdexScore` and/or `errorRatio` overrides. Example:<br><pre lang="jsonnet">{<br>  monitoringThresholds: {<br>    apdexScore: 0.997,<br>    errorRatio: 0.9995<br>  }<br>}</pre> |
| `monitoring.nginx` | Object | {} | Optional. Empty `{}` means to use default thresholds. Otherwise, specify `monitoringThresholds` with `apdexScore` and/or `errorRatio` overrides. Example:<br><pre lang="jsonnet">{<br>  monitoringThresholds: {<br>    apdexScore: 0.997,<br>    errorRatio: 0.9999<br>  }<br>}</pre> |
| monitoring.nginx.alertWindows | Array | ['1h', '6h', '3d'] | Configures which MWMBR alert windows are used for the nginx service. Valid values are 1h, 6h, 3d as defined in libsonnet/mwmbr/multiburn_factors.libsonnet. |
