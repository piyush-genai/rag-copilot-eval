<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# SAST Scanner Service for SAST in the IDE

* [Service Overview](https://dashboards.gitlab.net/d/sast-service-main/sast-service-overview)
* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22sast-service%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::SastService"

## Logging

* [sast-service](https://console.cloud.google.com/run/detail/us-central1/sast-service/logs?project=gitlab-runway-staging)

<!-- END_MARKER -->

## Summary

The SAST Scanner Service is stateless service that runs SAST scans to provide
SAST in the IDE. This service is currently used by "SAST IDE Integration"
feature, managed by the Secure:Static Analysis team.

The service deployments are being [managed by Runway](https://gitlab.com/gitlab-org/gitlab/-/issues/462808).

The source code repository for the service is available
[here](https://gitlab.com/gitlab-org/secure/sast-scanner-service) and the
runway deployment configuration is located
[here](https://gitlab.com/gitlab-org/secure/sast-ide-integration/-/blob/main/.runway/runway.yml?ref_type=heads).
Note, that we use different projects for managing the source code and for
deploying the service.

## Architecture

The architecture documentation is available [here](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/sast_ide_integration/).

## Performance

The benchmarking system is explained [here](https://gitlab.com/gitlab-org/secure/sast-ide-integration/-/blob/main/docs/benchmark.md?ref_type=heads).

## Scalability

The SAST Scanner service is deployed using Runway and its scaling is handled by Cloud Run and configured as part of Runway deployment ([doc](https://docs.runway.gitlab.com/reference/scalability/)).

## Availability

The SAST Scanner service is accessible by Ultimate tier users. The the service is
currently deployed to `us-central1` and `europe-west1` regions.

## Security/Compliance

The service is stateless; it does not log/store any customer-related data.

## Monitoring/Alerting

The service is deployed using Runway so that we can use the built-in
observability features particularly [monitoring stack](https://docs.runway.gitlab.com/reference/observability/). Default Runway
metrics for the service is available at [Runway Service Metrics dashboard](https://dashboards.gitlab.net/d/sast-service-main).

## Links to further Documentation

* [Design Document](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/sast_ide_integration/)
* [SAST IDE Integration Project that includes further documentation](https://gitlab.com/gitlab-org/secure/sast-ide-integration)
* [Static Analysis: real-time IDE SAST technical investigations and development](https://gitlab.com/groups/gitlab-org/-/epics/13753)
