# CloudFlare Troubleshooting

## Links

- [Cloudflare Grafana Dashboard](https://dashboards.gitlab.net/d/sPqgMv9Zk/cloudflare-traffic-overview?orgId=1)
- [Cloudflare Dashboard](https://dash.cloudflare.net)
- [GitLab.com Firewall Overview](https://dash.cloudflare.com/852e9d53d0f8adbd9205389356f2303d/gitlab.com/firewall)
- [GitLab.com Traceback Tool](https://gitlab.com/cdn-cgi/trace)

## Symptoms

There are certain conditions which indicate a CloudFlare-specific problem.
For example, if there are elevated CloudFlare errors but not production errors,
the problem must be inside CloudFlare.

Here is a list of potential sources of errors

### Static objects cache

[Static objects cache][static-objects-cache-howto] for production is deployed
as a CloudFlare worker in the gitlab.net zone. If the alert you got indicated
the gitlab.net zone, and requests to `/raw/` or `/-/archive` endpoints are
failing then it's worth checking how the worker is operating. See its
[runbook][static-objects-cache-troubleshooting] for troubleshooting information.

[static-objects-cache-howto]: ../web/static-repository-objects-caching.md
[static-objects-cache-troubleshooting]: ../web/static-objects-caching.md

## False Positive Triage Process

The following information is intended help the process of the diagnosing and
remediating user reports of Cloudflare blocks due to WAF enforcement. With any
WAF product, there will be a small number of user impacting false positives; our
goal is to reduce those as much possible given the nature of the content hosted
on GitLab.com while still getting some benefit from the Cloudflare WAF product.

### Supporting Artifacts to Collect

- If an incident has already been created due to a large number of reports:
  - Copy the [generic trace template](#generic-trace-template) below and
      ask users to report their results.
  - If further details are required, direct users to create confidential
      [Cloudflare Troubleshooting Issue](https://gitlab.com/gitlab-com/gl-infra/-/issues/new?issuable_template=Cloudflare%20Troubleshooting.md) and link it to the
      incident issue.
- If the problem is a specific URI or request:
  - Direct them to create a [Cloudflare Troubleshooting Issue](https://gitlab.com/gitlab-com/gl-infra/-/issues/new?issuable_template=Cloudflare%20Troubleshooting.md), making it confidential if necessary.

### Confirming Cloudflare and other service Connectivity

1. Inspect [Cloudflare Grafana Dashboard](https://dashboards.gitlab.net/d/sPqgMv9Zk/cloudflare-traffic-overview?orgId=1) the for any major discrepancies in the returns codes between Cloudflare
   and `haproxy`.
1. Log in to [https://dash.cloudflare.com](https://dash.cloudflare.com) and search
   for the requests which are not working as expected. Are they being blocked
   or otherwise acted on by any of the Cloudflare services?
1. Search the `workhorse` and `rails` [production logs](https://log.gprd.gitlab.net)
   to determine for the corresponding requests to verify if the request is making
   to GitLab's services.
1. On a host experiencing connection issues, add `gitlab.com` to the `/etc/hosts`
   file with the IP of the origin and reattempt the requests to determine if the
   problem may be between Cloudflare and GCP.
   1. Attempt the same connections using both the DNS supplied addresses for `gitlab.com`
      and the hardcoded origin addresses from different GCP regions and/or other
      cloud providers to further narrow down specific paths exhibiting problems.

### Generic trace template

```
<p>
<details>
<summary>`curl http://gitlab.com/cdn-cgi/trace`</summary>

<pre><code>PASTE OUTPUT HERE</code></pre>

</details>
</p>

<p>
<details>
<summary>`curl https://gitlab.com/cdn-cgi/trace`</summary>

<pre><code>PASTE OUTPUT HERE</code></pre>

</details>
</p>

<p>
<details>
<summary>`curl -svo /dev/null https://gitlab.com`</summary>

<pre><code>PASTE OUTPUT HERE</code></pre>

</details>
</p>

## GeoIP Troubleshooting

We use CloudFlare rules to block access to gitlab.com from various locations.  When we need to torubleshoot these rules with CloudFlare support they will ask for a trace from the user being blocked.  The user simply has to visit [`/cdn-cgi/trace`](https://gitlab.com/cdn-cgi/trace) and then we provide the output in the support ticket.
```
