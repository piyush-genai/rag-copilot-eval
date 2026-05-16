# PatroniGCSSnapshotDelayed

## Overview

We take GCS snapshots of the data disk of a Patroni replica periodically
(period specified by Chef's `node['gitlab-patroni']['snapshot']['cron']['hour']`).
Only one specific replica is used for the purpose of a snapshot, and this replica
does not receive any client connections nor participate in a leader election when
a failover occurs.

The replica is assigned a special Chef role `<env>-base-db-patroni-backup-replica`
in Terraform, here is an [example][tf-replica-example] from the production environment.

A cron job runs a Bash script (by default it is found in `/usr/local/bin/gcs-snapshot.sh`). The script run
the snapshot operation (i.e. `gcloud compute snapshot ...`) sandwiched between a `pg_start_backup` and `pg_stop_backup`
PostgreSQL calls, to ensure the integrity of the data. After a successful snapshot run, the script hits the local
Prometheus Pushgateway with the current timestamp for observability.

This alert monitors the time elapsed since the last successful Patroni GCS snapshot in the Production environment (gprd)/ Staging environment(gtsg) . If no successful snapshot is taken within the last 6 hours, and this condition persists for 30 minutes, the alert will fire

- If a failover or restart of patroni servers happen during execution of backup cronjob, the GCS snapshot might get halted (failed)

- This does not affect patroni service itself as it is a background job. However, our disaster recovery posture becomes questionable if we do not have a successful GCS snapshot.

- Try to determine root cause of failed GCS snapshot. If the snapshot failed due to failover of restart of patroni server, then re-run the bash script (/usr/local/bin/gcs-snapshot.sh) to create the latest GCS snapshot.

## Services

- [Patroni Service](../README.md)
- Team that owns the service: [Production Engineering : Database Reliability](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/core-platform/data_stores/database-reliability/)

## Metrics

- Bash script for GCS snapshot, pushes a job completion metric via push gateway, which is used for alerting.

- The cron job runs a Bash script (by default it is found in `/usr/local/bin/gcs-snapshot.sh`) runs every 6th hour , having the the alert to >=6h will only alert the on-call if it has failed twice in a row , [ref](https://gitlab.com/gitlab-com/runbooks/-/merge_requests/5114)

- This is how the [dashboard](https://dashboards.gitlab.net/goto/D0D9v3QIg?orgId=1) will look like when the alert is firing

[Alert](AlertConditionForGCSSnapshotDelayed.png)

- This is how the [dashboard](https://dashboards.gitlab.net/goto/A61jD3wIR?orgId=1) will look like under normal conditions

[Normal](NormalConditionForGCSSnapshotDelayed.png)

## Alert Behavior

- We can silence this alert by going [here](https://alerts.gitlab.net/#/alerts), finding the `PatroniGCSSnapshotDelayed` and click on silence option, Silencing might be required if GCS Snapshots were intentinally disabled for certain patroni node changes a good idea would be to refer the [Production](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=opened&first_page_size=100) issue board
- This alert should be fairly rare, and usually indicates that there is a query that is not behaving as we expect
- [Previous incidents of this alert firing](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=all&label_name%5B%5D=a%3APatroniGCSSnapshotDelayed&first_page_size=100)

## Severities

- If GCS back has been intentionally disabled it can be a `severity:4` issue otherwise it should be a `severity:3`
- Though this is not an immediate user-facing issue but it has repercussion for the customers as well because of bad recovery posture. Besides, we might be missing our internal targets of RTO and RPO for database recovery.

## Verification

- Prometheus link to [query](https://dashboards.gitlab.net/goto/A61jD3wIR?orgId=1) that          triggered the alert

## Recent changes

- [Recent Patroni Service change issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=updated_desc&state=opened&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniCI&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroni&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniRegistry&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniEmbedding&first_page_size=20)

- Recently closed issues to determine, if a CR was completed recently, which might be correlated:
[Recently Closed Issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=updated_desc&state=all&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniCI&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroni&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniRegistry&or%5Blabel_name%5D%5B%5D=Service%3A%3APatroniEmbedding&first_page_size=20)

## Troubleshooting

- If the snapshot operation failed for any reason, the script won't hit Prometheus Pushgateway, which will eventually
  trigger an alert.

  Check the logs for any clues, log file names have the following pattern `/var/log/gitlab/postgresql/gcs-snapshot-*`, check
  the last ones and see if an error is logged.

  Try running the script manually like this and see if it exits successfully:

  ```
  sudo su - gitlab-psql
  /usr/local/bin/gcs-snapshot.sh
  ```

  [tf-replica-example]: https://ops.gitlab.net/gitlab-com/gitlab-com-infrastructure/-/blob/235d69658055dd8174d774340d8a67734d997129/environments/gprd/main.tf#L825

- [Patroni Service Overview](https://dashboards.gitlab.net/d/patroni-main/patroni3a-overview?from=now-6h%2Fm&to=now%2Fm&var-PROMETHEUS_DS=mimir-gitlab-gprd&var-environment=gprd&var-stage=main&orgId=1)

- In case the GCS backup was halted , a new backup job can be started on the patroni server by running in a screen session

```bash
sudo su gitlab-sql
> /opt/wal-g/bin/backup.sh >> /var/log/wal-g/wal-g_backup_push.log 2>&1
#To check progress we can tail the logs on the Patroni server
```

## Possible Resolutions

- [Issue #17901](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/17901)
- [Issue #15652](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/15652)

## Dependencies

- GCS Snapshots might be deliberately disabled to make changes on a patroni node , or when a patroni node is scheduled to be destroyed

## Escalation

- If the recipient of this alert cannot determine the cause of the delayed GCS Snapshots and correct it using the troubleshooting steps above, it may be necessary to escalate
- Slack channels where help is likely to be found: #g_infra_database_reliability

## Definitions

- [Link to tune the alert](https://gitlab.com/gitlab-com/runbooks/-/blob/master/mimir-rules/gitlab-gprd/patroni/patroni-snapshot.yml)
- The threshold time should ideally be more than 6 hours becuase the cron job to backup the Patroni snapshots runs every six hours
- [Link to edit this playbook](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts/PatroniGCSSnapshotDelayed.md?ref_type=heads)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)

## Related Links

- [Related alerts](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts?ref_type=heads)
- > Related documentation
