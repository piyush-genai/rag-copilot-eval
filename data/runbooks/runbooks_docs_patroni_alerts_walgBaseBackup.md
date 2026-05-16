# walgBaseBackupDelayed, WALGBaseBackupFailed

## Overview

- walgBaseBackupDelayed alert indicates that the `base_backup` for WAL-G has not finished in a certain amount of time.
- WALGBaseBackupFailed means the most recent `base_backup` has failed.
- This can be due to load on the database servers, network conditions, or problems with GCS.
- This is not a user impacting alert.
- When this alert fires, it is expected that the recipient of the alert will check in on the `base_backup` and try to determine what has interrupted or failed the backup.

## Services

- [Service Overview](../README.md)
- Team that owns the service: [Production Engineering : Database Reliability](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/core-platform/data_stores/database-reliability/)

## Metrics

### walgBaseBackupDelayed

- walgBaseBackupDelayed fires if the most recent `base_backup` is older than 30 hours.
- This is recorded via the `gitlab_com:last_walg_successful_basebackup_age_in_hours` recording rule.

### WALGBaseBackupFailed

- walgBaseBackupDelayed fires if the most recent `base_backup` is older than 30 hours.
- This is determined by the metric `gitlab_job_failed{resource="walg-basebackup", type!~".+logical.+", env="gprd"} == 1`

## Alert Behavior

- This alert can be silenced if the process is determined to be running and actually working. It shouldn't be silenced for longer than the expected time to finish the backup.
- This alert is expected to be rare.

## Severities

- The severity of this alert is generally going to be a ~severity::4.
- There is no user impact at all. The impact will be in the amount of time it would take to recover should we need to do so.

## Verification

- [Prometheus Query for Alert](https://dashboards.gitlab.net/explore?schemaVersion=1&panes=%7B%229yb%22:%7B%22datasource%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22,%22queries%22:%5B%7B%22refId%22:%22A%22,%22expr%22:%22gitlab_com:last_walg_successful_basebackup_age_in_hours%20%3E%3D%2030%22,%22range%22:true,%22instant%22:true,%22datasource%22:%7B%22type%22:%22prometheus%22,%22uid%22:%22e58c2f51-20f8-4f4b-ad48-2968782ca7d6%22%7D,%22editorMode%22:%22code%22,%22legendFormat%22:%22__auto%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D%7D&orgId=1)

## Recent changes

- [Recent Patroni Production Change/Incident Issues](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/?sort=created_date&state=all&label_name%5B%5D=Service%3A%3APatroni&first_page_size=20)
- [Recent chef-repo Changes](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/merge_requests?scope=all&state=merged)
- [Recent k8s-workloads Changes](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-com/-/merge_requests?scope=all&state=merged)

## Troubleshooting

- Check `/var/log/wal-g/wal-g_backup_push.log` and/or `/var/log/wal-g/wal-g_backup_push.log.1` on patroni nodes. Unfortunately WAL-G logs are not sent to Kibana at this time.
- This will give you information on what is happening. A finished backup will look something like this:

    ```
    <13>Sep  2 00:00:01 backup.sh: INFO: 2021/09/02 08:20:54.669692 Finished writing part 14245.
    <13>Sep  2 00:00:01 backup.sh: INFO: 2021/09/02 08:20:56.337685 Wrote backup with name base_000000050005E38E000000A1
    <13>Sep  2 00:00:01 backup.sh: end backup pgbackup_pg12-patroni-cluster_20210902.
    ```

## Possible Resolutions

- [Another process using CPU causing the backup to slow down](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/16403)
- [base_backup started on a node that later became unavailable](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/17710)
- [The generating cluster isn't in production, but still alerting](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/15918)

## Dependencies

- The `base_backup` requires Google Cloud Storage to be available.

## Escalation

- Slack channels where help is likely to be found: `#g_infra_database_reliability`

## Definitions

- [Alert Definition](https://gitlab.com/gitlab-com/runbooks/-/blob/master/legacy-prometheus-rules/gitlab-walg-backups.yml#L42-53)
- [Update the template used to format this playbook](https://gitlab.com/gitlab-com/runbooks/-/edit/master/docs/template-alert-playbook.md?ref_type=heads)

## Related Links

- [Related alerts](https://gitlab.com/gitlab-com/runbooks/-/tree/master/docs/patroni/alerts?ref_type=heads)
- [PostgreSQL Backup Docs](../postgresql-backups-wale-walg.md)
