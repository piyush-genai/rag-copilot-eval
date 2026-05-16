# Cloudflare for the on-call

- [Cloudflare Status](https://www.cloudflarestatus.com/)
- [Run a traceroute from the Cloudflare network](https://ops.gitlab.net/gitlab-com/gl-infra/cloudflare-traceroute)
- [Cloudflare is Down](./cloudflare-is-down.md)

## Using Cloudflare to look for problems

The security section of the Cloudflare web UI is a convenient way to filter
on specific meta-data to find problematic traffic. This interface is also
very useful to see what rules are being applied to traffic.

- [Understanding Cloudflare Security Analytics](https://developers.cloudflare.com/waf/security-analytics/)

## Using Cloudflare to stop problems

**During an incident, making changes to the firewall rules and page rules
is expected. But be certain you follow proper process afterwards to make
certain that the changes are reflected in the right locations and follow the
Cloudflare rules management processes.**

*Note:* For audit purposes, any manual changes in the UI must be documented in the associated incident or issue. Please note the ResourceID and add `~Cloudflare UI Change` label.

### Adding firewall rules

A firewall rule should be used for the following types of actions:

- Blocking an IP address
- Adding captcha challenges to a path
- Prevent WAF rules from blocking legitimate traffic

Firewall rules can match against many types of request attributes.

The rule **must adhere to the description format of Cloudflare rules** described in the [Naming Conventions](/intro.md)

*Note:* For audit purposes, any manual changes in the UI must be documented in the associated incident or issue. Please note the ResourceID and add `~Cloudflare UI Change` label.

- [Manage firewall rules in the Cloudflare UI](https://developers.cloudflare.com/firewall/cf-dashboard)

### Disabling firewall rules

Firewall rules can be disabled from the [security rules page](https://dash.cloudflare.com/852e9d53d0f8adbd9205389356f2303d/gitlab.com/security/security-rules) without deleting them.
These rules can also be managed via the Cloudflare API and [terraform](https://ops.gitlab.net/gitlab-com/gl-infra/config-mgmt).
Consider doing this if a rule is causing an incident that could be mitigated.
A `terraform apply` in the `gprd` environment will overwrite manual changes, an option for a post-incident fix.

### Adding page rules

A page rule should be used for the following types of actions:

- Redirecting requests of a certain URL to another location
- Modifying cache policy for certain URL

Keep in mind that page rules can only match on request paths.

- [Understanding and Configuring Cloudflare Page Rules](https://support.cloudflare.com/hc/en-us/articles/218411427-Understanding-and-Configuring-Cloudflare-Page-Rules-Page-Rules-Tutorial-)

## Opening Cloudflare Support Issues

In 1password, in the *Production* vault is an entry named *Cloudflare Contacts
and Escalation*. This contains escelation and support instructions.
