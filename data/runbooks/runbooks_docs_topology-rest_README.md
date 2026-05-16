<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# Topology Service Rest

* [Service Overview](https://dashboards.gitlab.net/d/topology-service-main/topology-service-overview)
* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22topology-rest%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::TopologyServiceRest"

## Logging

* [stg](https://dashboards.gitlab.net/goto/XBaVEuCHR?orgId=1)
* [prod](https://dashboards.gitlab.net/goto/AFzSEXCHR?orgId=1)

<!-- END_MARKER -->

## Summary

The Topology Service implements a limited set of functions responsible for providing essential
features for Cells to operate.

Deployment and service configuration is managed in a separate [topology-service-deployer repository](https://gitlab.com/gitlab-com/gl-infra/cells/topology-service-deployer).

Deployment configuration including scaling is managed using a [Runway service manifest](https://docs.runway.gitlab.com/reference/service-manifest/) in the [topology-service-deployer](https://gitlab.com/gitlab-com/gl-infra/cells/topology-service-deployer) repository (see `runway.yml` in `.runway/*`).

Configuration for the service is managed in `config.toml`, which is provided as an environment variable as part of
deployment in the [topology-service-deployer](https://gitlab.com/gitlab-com/gl-infra/cells/topology-service-deployer) repository (see the `CONFIG_TOML` environment variable defined in `env-*.yml` in `.runway/*`). Details on the configuration syntax found [here](https://gitlab.com/gitlab-org/cells/topology-service/-/blob/main/docs/config.md).

## Architecture

Topology service is a Go container deployed using Runway. It sits in its own GCP project and responds
to router requests for information pertaining to Cells.

More detailed documentation found [here](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/cells/topology_service/#architecture).

<!-- ## Performance -->

## Scalability

Topology service is deployed using Runway and its scaling is handled by Cloud Run and configured as part of Runway deployment ([doc](https://docs.runway.gitlab.com/reference/scalability/)).

## Availability

Topology service is deployed to multiple regions. In future, when storing data, the storage system (Cloud Spanner)
will also be configured in multiple regions.

## Security/Compliance

Currently, no customer data is stored in Cells or in the topology service and is available as a public endpoint.

## Monitoring/Alerting

Topology service is deployed using Runway, which [supports observability by integrating with the monitoring stack](https://docs.runway.gitlab.com/reference/observability/). You can see the metrics via the general [Runway Service Metrics dashboard](https://dashboards.gitlab.net/d/runway-service/runway3a-runway-service-metrics).

## Breakglass

* [Topology Service Access Procedure](./breakglass.md)
