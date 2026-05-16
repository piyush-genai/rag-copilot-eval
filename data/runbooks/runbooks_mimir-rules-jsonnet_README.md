# Mimir recording rules

This directory contains the source files that will generate the recording rules on the directory [mimir-rules](https://gitlab.com/gitlab-com/runbooks/-/tree/master/mimir-rules?ref_type=heads).

Mimir uses the so called [tenant](https://grafana.com/docs/mimir/latest/references/glossary/#tenant) as an abstraction to a set of series (our recording rules). Each tenant is isolated from each other, allowing us to parallelize work as see fit to scale.

At GitLab, we use a combination of cluster, environment, service, and filename as a tenant. The helper function [separateMimirRecordingFiles](https://gitlab.com/gitlab-com/runbooks/-/blob/master/libsonnet/recording-rules/lib/mimir/separate-mimir-recording-files.libsonnet?ref_type=heads#L18) provides the building blocks to split the rules by tenants, generating the recording rule files with a valid unique name that works as a namespace for each rule group.

## Targeting specific tenants per service

A service can target a specific Mimir tenant. Simply provide the tenant names in the service definition, for example:

```diff --git a/metrics-catalog/services/thanos.jsonnet b/metrics-catalog/services/thanos.jsonnet
index a1a24d18f..9ce5d73b1 100644
--- a/metrics-catalog/services/thanos.jsonnet
+++ b/metrics-catalog/services/thanos.jsonnet
@@ -23,6 +23,7 @@ local thanosServiceSelector = { type: 'thanos', namespace: 'thanos' };
 metricsCatalog.serviceDefinition({
   type: 'thanos',
   tier: 'inf',
+  tenants: ['gitlab-ops'],

   tags: ['golang', 'thanos'],
```

This configuration will allow outputting recording rules only to the tenant(s) listed.

## Further reading

- [Grafana Mimir official docs](https://grafana.com/docs/mimir/latest/)
