# Cloudflare is Down

Since Cloudflare is our entry point, when it's down, most of our services will be unavailable to users. Our primary focus during these incidents is communication, monitoring, and preparing for recovery.

## Possible Actions

- Communicate with Cloudflare:
  - Post in shared Slack channel: `#gitlab-cloudflare-support`
  - Add the `:ticket:` emoji to open a support case
  - Request ETA and ongoing updates
- Engage [CMOC](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/roles/communications-lead/) to [update the GitLab status page](https://handbook.gitlab.com/handbook/support/workflows/cmoc_workflows/#about-statusio). Consider the following template:
  - **GitLab.com is down due to an upstream provider outage**
  - GitLab.com is inaccessible at the moment due to an upstream provider outage. We are currently investigating potential mitigation options. <issue link>
- If only a particular feature or rule is affected by the downtime, consider [disabling it temporarily](./oncall.md#disabling-firewall-rules) to allow access to the site in the meantime.
  - Always create a follow-up issue to re-enable whatever was disabled.
  - A `terraform apply` in the `gprd` environment will reset the rules, which can be used as a post-incident fix.
