# Making a manual clone of the DB for the data team

This page has information for making a manual clone of the database for the data team.
It was a process created in April 2022 related to [Reliability/15565](https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues/15565)
and is based on the notes from [Reliability](https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues/15574).

This machine currently needs to be remade daily and available by 00:00 UTC each day.
The steps should take a total of roughly 1-2 hours though most of that time is waiting.  The recreation of the VM should take ~30 min in Terraform.

Once things are complete, we have been commenting in Slack in #data-team-temp-database and on [issue 15574](https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues/15574). We have been mentioning Ved and Dennis like the comments here: <https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues/15574#note_907842307>

## How to recreate VM from the latest snapshot

The VM that will be destroyed and rebuilt is in the `db-benchmarking` environment.

First in Terraform:

```
tf destroy --target="module.patroni-data-analytics"
tf apply --target="module.patroni-data-analytics"
```

Note that there should be 10 items to be destroyed and rebuilt, but there are two null items (`module.gcp_database_snapshot.null_resource.contents` and `module.gcp_database_snapshot.null_resource.shell`) which will be destroyed and created on apply.  This looks strange, but it is fine.
<sample output> to show what is okay.

## Procedure to reconfigure the `patroni-data-analytics` cluster after recreating the VM

For SSH to the box:
a) make sure your ssh_config has the correct bastion:

```
Host *.gitlab-db-benchmarking.internal
ProxyCommand ssh lb-bastion.db-benchmarking.gitlab.com -W %h:%p
```

b) then ssh to `patroni-data-analytics-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal`
c) You may want to start up a tmux session for the rest of these steps...

1. Stop the Patroni service in the nodes with the command: `sudo systemctl stop patroni`
2. Get the cluster name: `sudo gitlab-patronictl list`
3. Remove the DCS entry from the cluster, executing : `sudo gitlab-patronictl remove patroni-data-analytics`
Answer the name of the cluster that will be removed: `patroni-data-analytics`
Answer the confirmation message: `Yes I am aware`
4. Change the ownership from the data and log folders in all cluster nodes:

```
sudo su -
cd /var/opt/gitlab/
chown -R gitlab-psql:gitlab-psql postgresql/
chown -R gitlab-psql:gitlab-psql patroni/
cd /var/log/gitlab/
chown -R gitlab-psql:gitlab-psql postgresql/
chown -R syslog:syslog patroni/
```

5 - Start Patroni:

```
sudo systemctl start patroni
```

6 - Monitor the patroni status and wait until the node is ready:

```
watch -n 1 sudo gitlab-patronictl list
```

7 - Once it is ready, collect this information to share:

```
sudo su -
gitlab-psql
select pg_last_xact_replay_timestamp();
exit
```
