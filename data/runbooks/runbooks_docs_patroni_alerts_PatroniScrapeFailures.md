# PatroniScrapeFailures

## Overview

- This alert fires when a configured Prometheus scrape target is not responding.
- System load, a node or the exporter processes being offline, or otherwise unresponsive may be contributing factors that result in this alert.
- When this alert fires, it may indicate a severe problem with the host, or that we are blind to future problem detection due to lack of metrics.

## Services

- This particular alert is scoped only to nodes supporting the [Patroni service](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/patroni/README.md?ref_type=heads).

## Metrics

- This uses the internal `up()` function provided by Prometheus, which indicates whether or not the most recent scrape attempt of a given job was successful or not.
- It is expected that the return of the query will always be an empty result. Note that we filter the pgbouncer scrape job in [the query](), due to this being incorrectly configured via the Mimir prometheus-agent ScrapeConfig.

## Alert Behavior

- This alert is intended to fire regardless of a host's power state. Because of this, a silence should be created in Alertmanager prior to powering off any instances to avoid unwanted alerts.
- This alert will fire if any single scrape target on a host is failing to be scraped. You can determine the specific scrape jobs by removing the `min()` aggregator from the prometheus query. [Example](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%22sgo%22:%7B%22datasource%22:%22mimir-gitlab-gprd%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22up%7Bfqdn%3D~%5C%22patroni.%2A%5C%22,%20job%21~%5C%22.%2Apgbouncer%5C%22,%20env%3D%5C%22gprd%5C%22%7D%20%3D%3D%200%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22mimir-gitlab-gprd%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1)

## Severities

- If this fires and you aren't intentionally powering down a VM, always assume this is a high severity alert.
- When this fires we either have a node that has failed in a way that could directly impact our customers, or we become blind to future issues as future metrics collection will not be working.

## Verification

- Verify whether it is a single exporter, or all that are failing to be scraped on the host using this [example query](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%22sgo%22:%7B%22datasource%22:%22mimir-gitlab-gprd%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22up%7Bfqdn%3D~%5C%22patroni.%2A%5C%22,%20job%21~%5C%22.%2Apgbouncer%5C%22,%20env%3D%5C%22gprd%5C%22%7D%20%3D%3D%200%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22mimir-gitlab-gprd%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1).
- Check that the host is responsive to SSH connections.
- Check the GCP console for any system logs that may indicate a problem.

## Troubleshooting

- Check that the host is responsive to ping, SSH connections, etc.
- Check the GCP console for any system logs that may indicate a problem.
- If you can get an SSH connection to the host, check for OOM kills that may have impacted running exporters.

## Possible Resolutions

- Attempt to restart the exporter services on the machine if the host is responsive and handling query traffic normally.
- If the machine is locked up or unresponsive, a reboot may be necessary.

## Escalation

- Slack channel: `#g_database_operations`
- Slack group: `@dbo`

## Definitions

- [Alert definition](https://gitlab.com/gitlab-com/runbooks/-/blob/master/mimir-rules/gitlab-gprd/patroni/PatroniScrapeFailures.yml)
- [Link to edit this playbook](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts/PatroniScrapeFailures.md?ref_type=heads)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)

## Related Links

- > [Related alerts](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts?ref_type=heads)
