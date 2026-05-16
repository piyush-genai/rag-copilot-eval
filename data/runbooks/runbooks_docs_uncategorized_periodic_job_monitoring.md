# Periodic Job Monitoring

We have lots of jobs that run regularly. We use Prometheus & Alertmanager to monitor and alert on jobs that are either still running and taking too long to finish, or that have completed but took longer than expected ([details](./job_completion.md)). This type of alerting relies on jobs actually starting to be able to alert on them. **What about jobs that quietly fail to trigger when they're supposed to?**

[Dead Man's Snitch](https://deadmanssnitch.com) (or DMS) is a third-party monitoring tool for periodic processes, and we use this service for alerting us when jobs fail to trigger when they're expected to.

## How does it work?

You create a "snitch", which is a unique URL for a job to be monitored and the interval that the job is expected to run (or _smart_ mode to figure out the interval based on when the job checks in). Every time the job runs, it needs to hit the unique URL. If it doesn't hit the URL within the expected interval, it triggers an alert.

## What receivers does it support?

It can send an email and/or trigger one of the supported integrations (e.g., Slack, PagerDuty, etc).

## What integrations have we got configured?

Currently we have:

- PagerDuty configured for any snitches tagged `pager`
- Slack `#alerts` for all snitches
- Slack `#database` for any snitches tagged `database`

This list may be out-of-date so best refer to the DMS [integrations](https://deadmanssnitch.com/cases/7cd95b63-4eb9-4752-8e53-bf335c621103/integrations) page for an up-to-date listing.

## How are snitches configured?

They are manually configured. We're aware that there's a [Terraform provider](https://github.com/plukevdh/terraform-provider-dmsnitch) for DMS, but we haven't tried it yet.
