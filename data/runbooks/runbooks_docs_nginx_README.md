<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# NGINX Service

* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22nginx%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::NGINX"

## Logging

* [Kubernetes](https://log.gprd.gitlab.net/goto/88eab835042a07b213b8c7f24213d5bf)
* [Error Logs](https://cloudlogging.app.goo.gl/neeqq5jQEKWsxZRx8)

<!-- END_MARKER -->

## Summary

NGINX sits in front of our Puma services.  It provides a bit of protection
between end users and puma workers to prevent saturation of threads.

## Architecture

For Virtual Machines, this is deployed via our Omnibus package and runs as a
service that recieves traffic.

For Kubernetes, this is deployed using the NGINX Ingress controller managed by
our helm chart.  <https://docs.gitlab.com/charts/charts/nginx/>

### Configuration

<https://docs.gitlab.com/omnibus/settings/nginx.html>

<!-- ## Performance -->

<!-- ## Scalability -->

<!-- ## Availability -->

<!-- ## Durability -->

<!-- ## Security/Compliance -->

<!-- ## Monitoring/Alerting -->

<!-- ## Links to further Documentation -->
