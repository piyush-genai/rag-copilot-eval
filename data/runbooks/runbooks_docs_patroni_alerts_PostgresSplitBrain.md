# PostgresSplitBrain

## Overview

- This alert `PostgresSplitBrain`, is designed to detect a split-brain scenario in a PostgreSQL cluster managed by Patroni. It validates if each Patroni cluster has only one Primary node ie: each `type` of Patroni cluster only has one Primary node accepting R/W requests.
- An incorrect consul configuration or Patroni configuration can trigger this , Incorrect health check results can cause Patroni to incorrectly promote a new leader or fail to demote a current leader.

## Services

- [Postgres Overview](https://dashboards.gitlab.net/d/000000144/postgresql-overview)
- [Patroni Service](../README.md)
- [Consul](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/consul/interaction.md?ref_type=heads#some-commands-interesting-for-patroni)
- Team that owns the service: [Production Engineering : Database Reliability](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/core-platform/data_stores/database-reliability/)

## Metrics

- [Link to the metrics catalogue](https://gitlab.com/gitlab-com/runbooks/-/blob/master/mimir-rules/gitlab-gprd/patroni/patroni.yml#L53)
- This Prometheus expression counts the number of PostgreSQL instances in the gprd/gstg environment that are not in replica mode   `(pg_replication_is_replica == 0)`. If this count is greater than 1, it triggers the alert. This condition indicates that more than one PostgreSQL instance is operating in read-write mode within a cluster.This condition must be true for at least 1 minute to trigger the alert.
- In both `gstg` and `gprd` environments we have 3 patroni clusters (main, ci and registry at the time of writing) and as such we should expect 3 total primary nodes. Be sure to check the `type` field to distinguish the Patroni clusters and ensure there is only 1 per type. If we see more than three different `type` of clusters it might suggest a `PatroniConsulMultipleMaster` situation.

## Alert Behavior

- We can silence this alert by going [here](https://alerts.gitlab.net/#/alerts), finding the `PostgresSplitBrain` and click on silence option
- This is a very rare and critical event
- There might be a sudden spike in the gitlab_schema_prevent_write errors , [Link to dashboard]("https://log.gprd.gitlab.net/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:'2023-06-13T15:48:47.826Z',to:'2023-06-13T16:43:35.482Z'))&_a=h@46feaf4")

## Severities

- This alert might create S1 incidents.
- Who is likely to be impacted by this cause of this alert?
  - Depending on the database it could be some or all customers. If it is the `main` or `ci` database then we expect nearly all customers would be impacted. If it is the `registry` database then it would be a subset of customers that are depending on the registry.
- Review [Incident Severity Handbook](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#incident-severity) page to identify the required Severity Level

## Verification

- To validate if a Patroni cluster has more than one leader , a quick view through [this](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%2280n%22:%7B%22datasource%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22count%20by%20%28type%29%20%28pg_replication_is_replica%7Btype%21%3D%5C%22%5C%22,%20env%3D%5C%22gprd%5C%22%7D%20%3D%3D%200%29%5Cn%5Cn%5Cn%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-6h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1) dashboard should give you that information regarding the `type` of the Patroni cluster which has more than one leader if any

- On executing the query `pg_replication_is_replica{type="<type of cluster with more than one replica>", env="<gstg/gprd>"}` on your grafana dashboard should tell you the cluster and the fqdn of the leader nodes , please note the `pg_replication_is_replica` value for leader nodes would be 0

## Recent changes

- [Recent Patroni Service change issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=updated_desc&state=opened&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniCI&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroni&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniRegistry&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniEmbedding&first_page_size=20)

- Recently closed issues to determine, if a CR was completed recently, which might be correlated:
[Recently Closed Issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=updated_desc&state=all&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniCI&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroni&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniRegistry&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniEmbedding&first_page_size=20)

## Troubleshooting

- First step is to figure out which Patroni cluster has more than one leader , a quick view through [this](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%2280n%22:%7B%22datasource%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22count%20by%20%28type%29%20%28pg_replication_is_replica%7Btype%21%3D%5C%22%5C%22,%20env%3D%5C%22gprd%5C%22%7D%20%3D%3D%200%29%5Cn%5Cn%5Cn%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-6h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1) dashboard should give you that information regarding the `type` of the Patroni cluster which has more than one leader

- On executing the query `pg_replication_is_replica{type="<type of cluster with more than one replica>", env="gprd"}` on your grafana dashboard should tell you the cluster and the fqdn of the leader nodes , please note the `pg_replication_is_replica` value for leader nodes would be 0

- It might be helpful to look in recent MRs to see if any changes rolled out recently related to Patroni clusters in [chef repo](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/merge_requests), or [config-mgmt](https://ops.gitlab.net/gitlab-com/gl-infra/config-mgmt/-/merge_requests?scope=all&state=merged)

- Steps that can be used via the Patroni CLI to remediate . For example:

```bash
#(Untested steps proceed with extreme caution)
# We ssh into one of the replicas
ssh patroni-main-v14-03-db-gprd.c.gitlab-production.internal
# Verify the members in the cluster and find the erroneus leader
sudo gitlab-patronictl list
# Pausing the incorrect/erroneus leader , this will make Postgres stop on the node
sudo mv /var/opt/gitlab/postgresql/data12 /var/opt/gitlab/postgresql/data"<find the number going into the directory>"_dontstart_see_production_"<Issue_number>"
# Once unreachable manually promote a new node to leader
sudo gitlab-patronictl failover
```

- [Helpful gitlab-patronictl commands](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/patroni/patroni-management.md)

## Possible Resolutions

- [Issue 15773](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/15773)

## Dependencies

- Internal dependencies like issues with Patroni configuration , Consul configuration , false positive healthchecks of nodes may cause
a splitbrain situation

- External dependencies like networ outage or high network latency may also cause a splitbrain situation.

## Escalation

- Please use /devoncall <incident_url> on Slack for any escalation that meets the [criteria](https://handbook.gitlab.com/handbook/engineering/development/processes/infra-dev-escalation/process/#scope-of-process).
- Slack channels where help is likely to be found: `#g_infra_database_reliability`, `#database`

## Definitions

- [Link to the definition of this alert for review and tuning](https://gitlab.com/gitlab-com/runbooks/-/blob/master/mimir-rules/gitlab-gprd/patroni/patroni.yml#L53)
- [Link to edit this playbook](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts/PostgresSplitBrain.md?ref_type=heads)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)

## Related Links

- [Related alerts](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/patroni/alerts/)
- [Postgres Runbook docs](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/postgres)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)
