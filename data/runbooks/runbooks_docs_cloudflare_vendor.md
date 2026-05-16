# Accessing and Using CloudFlare

Users that have been provisioned can access Cloudflare directly at
`https://dash.cloudflare.com`.

## Instructions for Access Provisioning

1. We have transitioned to Lumos for the following Cloudflare accounts

   - Gitlab
   - Runway
   - Gitlab Dedicated Production
   - Gitlab Dedicated Non-production

1. Access requests should now be self-served, requests are raised on a per account level, for example if somebody wanted to access both GitLab and Runway accounts they will have to raise two Lumos requests.
1. Make sure to add relevant issue and context in the comment section while raising the request to give the approver enough context
1. Lumos access request is a two step approval process, you would first need approval of your manager, and then based on the account you are requesting access for, there will be a set of approvers as follows

   - Gitlab : Network and Incident Management Team
   - Runway : Runway team
   - Gitlab Dedicated Production : `@denhams , @nitinduttsharma and @o-lluch`
   - Gitlab Dedicated Non-production : `@denhams , @nitinduttsharma and @o-lluch`

1. Approvers can choose to cancel a Lumos request with an appropriate reason.

### Deprovisioning

1. Deprovisioning via Lumos is not available at the moment , an AR with IT would need to be raised for this usecase
1. Please do not remove Cloudflare members manually from user groups in Cloudflare UI

#### Access to Gitlab Dedicated FedRAMP Cloudflare accounts

Access to **Gitlab Dedicated FedRAMP sandbox Cloudflare account** is still managed manually (soon to be transitioned to Lumos)

**Provisioning Steps:**

1. Add user to [`okta-cloudflare-users` google group](https://groups.google.com/a/gitlab.com/g/okta-cloudflare-users/members)
1. Create an MR in [Dedicated Cloudflare Organization](https://gitlab.com/gitlab-com/gl-infra/gitlab-dedicated/dedicated-organization-cloudflare/-/blob/main/environments/cloudflare_fedramp_sandbox/main.tfvars)
Access to **Gitlab Dedicated FedRAMP Cloudflare** account is provisioned via a separate [onboarding issue](https://gitlab.com/gitlab-com/gl-security/security-assurance/fedramp/fedramp-certification/-/blob/main/.gitlab/issue_templates/FedRAMP_Onboarding-New_Employees.md?ref_type=heads).

## Configuration

### Creating or Editing Custom Rules

[Cloudflare: Overview](./intro.md)

#### Managing Traffic (blocks, allowlists and abuse mitigation)

[Cloudflare: Managing Traffic](./cloudflare-managing-traffic.md)

### Managing Workers

[Cloudflare Workers](https://ops.gitlab.net/gitlab-com/gl-infra/terraform-modules/cloudflare_workers#configuration)

## Getting support from Cloudflare

### Contacting support

### Contact Numbers

Should we need to call Cloudflare, we were given these numbers to reach out to for help.

Those numbers are documented in the [internal handbook](https://internal.gitlab.com/handbook/engineering/infrastructure/vendor-contact/), or the internal Cloudflare support Slack channel

## Other References

- Implementation Epic: <https://gitlab.com/groups/gitlab-com/gl-infra/-/epics/94>
- Readiness review: <https://gitlab.com/gitlab-com/gl-infra/readiness/blob/master/cloudflare/README.md>
- Issue Tracker for Evaluation: <https://gitlab.com/gitlab-com/gl-infra/cloudflare/issues>
- Ongoing Cloudflare Epic: <https://gitlab.com/groups/gitlab-com/gl-infra/-/epics/1131>
- Managing Limits: <https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/rate-limiting/managing-limits/>
- Cloudflare terraform configuration: <https://gitlab.com/gitlab-com/gl-infra/terraform-modules/cloudflare>
