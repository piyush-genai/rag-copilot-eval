# PatroniLongRunningTransactionDetected

## Overview

This alert means that there are transactions older than 10 minutes running
on the server listed in the alert.

This could be caused by many things, most often a large sidekiq job.
The alert will tell you what endpoint is executing the long running transaction.

This is important as long running transactions can prevent Postgres from running routine vacuuming, which can lead to bloat and slowdowns of the database.

Long-running transactions are one of the main drivers for [`pg_txid_xmin_age`](../pg_xid_xmin_age_alert.md), and can result in severe performance degradation if left unaddressed.

The recipient of this alert should investigate what the long running transaction is, and whether it is going to
cause performance problems. In most cases we are going to want to cancel the transaction.

## Services

- [Patroni Service](../README.md)
- Team that owns the service: [Production Engineering : Database Reliability](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/core-platform/data_stores/database-reliability/)

## Metrics

- [Long Running Alerts Dashboard](https://dashboards.gitlab.net/d/alerts-long_running_transactions/alerts3a-long-running-transactions?orgId=1)
- This alert fires when we measure one or more transactions with an age greater than 9 minutes, AND we have been in this state for 1 minute - which gives a total of 10 minutes that a transaction can be active before alerting
- Under normal conditions this dashboard should show lists of transactions with ages less 1 minute. Occasionally, there will be transactions which have been running for longer, but very few shoud approach the threshold

## Alert Behavior

- This alert will clear once the long running transactions are no longer active. The alert should only be silenced during an open Change Reqeust
- This alert should be fairly rare, and usually indicates that there is a query that is not behaving as we expect.
- [Previous Incidents for alert](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=all&label_name%5B%5D=a%3APatroniLongRunningTransactionDetected)

## Severities

- This alert is unlikely to be causing active customer issues, and is most likely an S4
- However, this alert could evolve into performance issues for all of GitLab.com
- Check the [Patroni SLI Overview Dashboard](https://dashboards.gitlab.net/d/patroni-main/patroni3a-overview?orgId=1) to determine whether we are already experiencing performance issues

## Verification

- [Prometheus query](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%222u6%22:%7B%22datasource%22:%22mimir-gitlab-gprd%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22topk%20by%20%28environment,%20type,%20stage,%20shard%29%20%281,%20max%20by%20%28environment,%20type,%20stage,%20shard,%20application,%20endpoint,%20fqdn%29%20%28pg_stat_activity_marginalia_sampler_max_tx_age_in_seconds%7Bcommand%21%3D%5C%22autovacuum%5C%22,command%21~%5C%22%28%3Fi:ALTER%29%5C%22,command%21~%5C%22%28%3Fi:ANALYZE%29%5C%22,command%21~%5C%22%28%3Fi:CREATE%29%5C%22,command%21~%5C%22%28%3Fi:DROP%29%5C%22,command%21~%5C%22%28%3Fi:REINDEX%29%5C%22,command%21~%5C%22%28%3Fi:VACUUM%29%5C%22,env%3D%5C%22gprd%5C%22,shard%3D%5C%22default%5C%22,tier%3D%5C%22db%5C%22,type%21~%5C%22.%2Aarchive%5C%22,type%21~%5C%22.%2Adelayed%5C%22%7D%29%20%3E%20540%29%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22mimir-gitlab-gprd%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-3h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1)
- [Long running transactions dashboard](https://dashboards.gitlab.net/d/alerts-long_running_transactions/alerts3a-long-running-transactions?from=now-6h%2Fm&to=now-1m%2Fm&var-environment=gprd&orgId=1)

## Recent changes

- [Recent Patroni Service change issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=updated_desc&state=opened&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniCI&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroni&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniRegistry&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniEmbedding&first_page_size=20)
- [Recent Patroni Change Requests](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=closed&label_name%5B%5D=Service%3A%3APatroni&label_name%5B%5D=change)
- This alert is likely to have been triggered by a recent deployment, rather than a database related change.
- If there is a deployment causing the issue, roll back the change that was deployed
- If a change request caused the problem, follow the rollback instructions in the Change Request.

## Troubleshooting

### Getting the current query

The first step is to figure out what the long-running transaction is doing. The alert will tell you which host to look at. From there, it is possible to get a `query`, `pid`, `client_addr`, and `client_port`:

```
iwiedler@patroni-main-2004-01-db-gprd.c.gitlab-production.internal:~$ sudo gitlab-psql

gitlabhq_production=# \x
Expanded display is on.

gitlabhq_production=# \pset pager 0
Pager usage is off.

gitlabhq_production=# select *,
  now(),
  now() - query_start as query_age,
  now() - xact_start as xact_age
from pg_stat_activity
where
  state != 'idle'
  and backend_type != 'autovacuum worker'
  and xact_start < now() - '60 seconds'::interval
order by now() - xact_start desc nulls last
;
```

In the event that the alert has already cleared because the query in question has completed, or been canceled, it may still be possible to find the query in the Postgres [`pg_stat_activity` logs](https://log.gprd.gitlab.net/app/r/s/kcFjj). These transactions are dumped to Kibana every several minutes, so the same query may appear multiple times if it spans multiple dumps.

### Getting the pgbouncer instance

Usually postgres connections go through a pgbouncer. The `client_addr` and `client_port` will tell you which one.

In this case it was `pgbouncer-01-db-gprd` as discovered via the `client_port` of `42792`:

```
iwiedler@patroni-main-2004-01-db-gprd.c.gitlab-production.internal:~$ sudo netstat -tp | grep 42792

tcp        0    229 patroni-main:postgresql pgbouncer-01-db-g:42792 ESTABLISHED 3889825/postgres: g
```

### Resolving pgbouncer port to client

Now that we have the pgbouncer address and port, we can log into that pgbouncer box and get the actual client.

This can be done by first running `show sockets` on the pgbouncer admin console, and finding the metadata for the backend port:

```
iwiedler@pgbouncer-01-db-gprd.c.gitlab-production.internal:~$ sudo pgb-console -c 'show sockets' | grep 42792

 type |     user      |      database       |   state   |     addr      | port  | local_addr | local_port |      connect_time       |      request_time       |   wait   | wait_us | close_needed |      ptr       |      link      | remote_pid | tls | recv_pos | pkt_pos | pkt_remain | send_pos | send_remain | pkt_avail | send_avail
 S    | gitlab        | gitlabhq_production | sv_active | 10.220.21.101 |  5432 | 10.217.4.3 |      42792 | 2022-10-28 08:33:46 UTC | 2022-10-28 09:19:56 UTC |        0 |       0 |            0 | 0x1906c30      | 0x7fc9a694e498 |    3889825 |     |        0 |       0 |          0 |        0 |           0 |         0 |          0
```

Using this information we can then grab the `link` column. And join it against `show clients` to discover the actual client:

```
iwiedler@pgbouncer-01-db-gprd.c.gitlab-production.internal:~$ sudo pgb-console -c 'show clients' | grep 0x7fc9a694e498

 type |   user    |      database       | state  |     addr      | port  | local_addr | local_port |      connect_time       |      request_time       |   wait   | wait_us | close_needed |      ptr       |   link    | remote_pid | tls
 C    | gitlab    | gitlabhq_production | active | 10.218.5.2    | 49266 | 10.217.4.5 |       6432 | 2022-10-28 09:01:06 UTC | 2022-10-28 09:20:51 UTC |        0 |       0 |            0 | 0x7fc9a694e498 | 0x1906c30 |          0 |
```

Double checking connections, and this tells us that it's `console-01-sv-gprd`:

```
iwiedler@pgbouncer-01-db-gprd.c.gitlab-production.internal:~$ sudo netstat -tp | grep 49266

tcp        0     35 10.217.4.5:6432         console-01-sv-gpr:49266 ESTABLISHED 19532/pgbouncer
```

### Resolving client address and port to process and user

Now that we've confirmed it's a console user, we can look up which process on the console host holds that connection:

```
iwiedler@console-01-sv-gprd.c.gitlab-production.internal:~$ sudo ss -tp | grep 49266

ESTAB      0      194             10.218.5.2:49266              10.217.4.5:6432  users:(("ruby",pid=3226026,fd=10))
```

And we can feed the pid into `pstree` to see the process hierarchy:

```
systemd(1)───sshd(1369)───sshd(3225836)───sshd(3226021,arihant-rails)───bash(3226022)───script(3226024)───sudo(3226025,root)───ruby(3226026,git)─┬─{ruby}(3226033)
                                                                                                                                                 ├─{ruby}(3226039)
                                                                                                                                                 ├─{ruby}(3226040)
                                                                                                                                                 ├─{ruby}(3226050)
                                                                                                                                                 ├─{ruby}(3228019)
                                                                                                                                                 ├─{ruby}(3228021)
                                                                                                                                                 ├─{ruby}(3228022)
                                                                                                                                                 ├─{ruby}(3228023)
                                                                                                                                                 ├─{ruby}(3228024)
                                                                                                                                                 └─{ruby}(3228025)
```

In this case it was user `arihant-rails` who was running a script via rails console.

### Cancelling the query

In most cases, we will want to cancel the query. If it's a single long-running query, this can be done via `pg_cancel_backend` (passing in the `pid`):

```
gitlabhq_production=# select pg_cancel_backend(<pid>);
 pg_cancel_backend
-------------------
 t
```

However, if we are dealing with a long-running transaction consisting of many short-lived queries, it may be necessary to terminate the backend instead:

```
gitlabhq_production=# select pg_terminate_backend(<pid>);
 pg_terminate_backend
----------------------
 t
```

## Possible Resolutions

- [2023-02-01: long postgres transaction](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/8339) was a long running transaction in a rails console session.
- [2021-08-18: Long running transaction on database](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/5379) was expected behavior as a foreign key was being added.
- [2023-10-21: Long Postgres transactions Vulnerabilities::MarkDroppedAsResolvedWorker](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/17011) was an application issue that warrented an InfraDev issue.
- [Other incidents for this alert](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=all&label_name%5B%5D=a%3APatroniLongRunningTransactionDetected)

## Dependencies

- Background migrations
- Sidekiq jobs

## Escalation

- If the recipient of this alert cann't determine the cause of the long running transaction and correct it using the troubleshooting steps above, it may be necessary to escalate
- Slack channels where help is likely to be found: `#g_infra_database_reliability`

## Definitions

- [Link to the definition of this alert for review and tuning](../../../libsonnet/alerts/patroni-cause-alerts.libsonnet)
- The main parameter that we can tune is the amount of time we allow before alerting. It is currently set to 10 minutes. We can also exclude certain types of transactions from alerting
- [Link to edit this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/patroni/alerts/PatroniLongRunningTransactionDetected.md?ref_type=heads)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)

## Related Links

- [Related alerts](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts?ref_type=heads)
- [Previous Incidents involving this alert](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=all&search=PatroniLongRunningTransactionDetected&not%5Blabel_name%5D%5B%5D=Status%20Report)
- [Wraparound status](../check_wraparound.md)
- [Handling unhealthy patroni replica](../unhealthy_patroni_node_handling.md)
- [Troubleshooting performance degredation](../performance-degradation-troubleshooting.md)
- [Postgres Long Runniong Transaction](../postgres-long-running-transaction.md)
