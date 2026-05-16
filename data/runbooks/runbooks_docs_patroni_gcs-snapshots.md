# Patroni GCS Snapshots

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

## Manual GCS Snapshots

Occasionally as part of maintenance activities or during an emergency, we may need to manually snapshot the Patroni cluster.

The GCS snapshots are a high I/O demanding operation since we are making a copy of the whole disk. It is not recommended to execute in a database receiving traffic, and never on the primary node from a Patroni cluster. To execute this snapshot we suggest to use one of these two options:

a) Currently we have one node Patroni-08, that has the Patroni flags :

- `no-loadbalancer`: to not receive traffic.
- `no-failover`: to not be promoted as a primary.

b) Provision a new node to the cluster with the tags mentioned above. Or add the tags a node to execute the snapshot.

The optimal procedure is getting the database in a backed-up state, using the commands `pg_start_backup` and `pg_stop_backup`, which will allow a consistent disk snapshot.

Here are the steps to take following the best practices and allowing us to safely conduct a manual snapshot, on a host without production traffic:

- Start a session with a pg_start_backup, that will start the backup mode:
  - Execute the following command in `gitlab-psql`:

    ```sql
    SELECT pg_start_backup('Manual GCS snapshot', TRUE, FALSE);
    ```

- In a second session on this host execute the GCS snapshot:
  - gcloud compute disks snapshot ${disk} --description "manual GCS snapshot $(date +%Y-%m-%dT%H:%M:%S%z)" --snapshot-names=${disk}-manual-snapshot --zone=${zone}
  - disk example= `patroni-01-db-gprd-data`
  - zone example= `us-east1-c`

- Stop the backup command, in the same session you started the backup mode:
  - Execute the following command  `gitlab-psql`:

    ```sql
    SELECT pg_stop_backup(FALSE, FALSE);
    ```

## Troubleshooting

### "Last Patroni GCS snapshot did not run successfully" alert

If the snapshot operation failed for any reason, the script won't hit Prometheus Pushgateway, which will eventually
trigger an alert.

Check the logs for any clues, log file names have the following pattern `/var/log/gitlab/postgresql/gcs-snapshot-*`, check
the last ones and see if an error is logged.

Try running the script manually like this and see if it exits successfully:

```
sudo su - gitlab-psql
/usr/local/bin/gcs-snapshot.sh
```

[tf-replica-example]: https://ops.gitlab.net/gitlab-com/gitlab-com-infrastructure/-/blob/235d69658055dd8174d774340d8a67734d997129/environments/gprd/main.tf#L825
