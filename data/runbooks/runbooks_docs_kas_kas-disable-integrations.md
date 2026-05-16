# `kas` Disable Integrations

In case of incidents where kas might be inadvertently be affecting services it
integrates with including API, Gitaly, and Redis, it is possible to temporary
disable these integrations until proper diagnosis and remediation of problems
can occur.

## Disabling access to API

There are multiple ways to do this, but one of the simplest is to use the
[Kubernetes Network Policy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
to stop the `kas` pods from being able to access to Gitlab API. To do this
change the helm value `gitlab.kas.networkpolicy.egress.rules` to remove the
rule that allows access to Gitlab API through a merge request and apply to production.

When this access is disabled, all Gitlab users `agentk` agents will be unable
to authenticate to `kas` and thus will be unable to leverage any and all functionality
that `kas` provides.

## Disabling access to Gitaly

If access to all Gitaly nodes needs to be temporarily disabled, this can be done
through changing the [Kubernetes Network Policy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
to stop the `kas` pods from being able to access Gitaly.  To do this
change the helm value `gitlab.kas.networkpolicy.egress.rules` to remove the
rule that allows access to Gitaly through a merge request and apply to production.

When this access is disabled, Gitlab users will be unable to use most features of `agentk`
since `kas` will not be able to fetch agents configuration.

## Disabling access to Redis

If access to Redis needs to be temporarily disabled, this can be done
through changing the [Kubernetes Network Policy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
to stop the `kas` pods from being able to access Redis. To do this
change the helm value `gitlab.kas.networkpolicy.egress.rules` to remove the
rule that allows access to Redis through a merge request and apply to production.

When this is disabled, it would stop `kas` from being able to do token-based rate limiting,
instead falling back to a global rate limit for all operations which might bottleneck users.
Request proxying will work only partially too.
