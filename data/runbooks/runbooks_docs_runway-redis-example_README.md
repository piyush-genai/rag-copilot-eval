<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# Example Runway-managed Redis Service

* [Service Overview](https://dashboards.gitlab.net/d/runway-redis-example-main/runway-redis-example-overview)
* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22runway-redis-example%22%2C%20tier%3D%22db%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::RunwayRedisExample"


<!-- END_MARKER -->

## Summary

This service represents an example Runway-managed Redis instance. The IAC definition for the Redis instances can be found in the [provisioner project](https://gitlab.com/gitlab-com/gl-infra/platform/runway/provisioner/-/blob/main/memorystore.tf).

The Redis instances are [GCP Memorystore Redis instances](https://cloud.google.com/memorystore/docs/redis/memorystore-for-redis-overview).

## Architecture

Refer to [Runway Redis blueprint](https://runway-docs-4jdf82.runway.gitlab.net/reference/blueprints/redis/) for more information.

<!-- ## Performance -->

<!-- ## Scalability -->

<!-- ## Availability -->

<!-- ## Durability -->

<!-- ## Security/Compliance -->

<!-- ## Monitoring/Alerting -->

<!-- ## Links to further Documentation -->
