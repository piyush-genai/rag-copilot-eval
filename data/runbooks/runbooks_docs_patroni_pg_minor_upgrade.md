# Postgresql minor upgrade

This runbook describes all the steps to execute a Postgresql minor upgrade.

**Important!** Please read the release notes before getting started (for all minor versions after the current version of postgresql) - <https://www.postgresql.org/docs/12/release.html>

Considering the database, one of the most critical components from our infrastructure, we want to execute the upgrade node by node by executing tests, monitoring the performance and behavior after the upgrade in each node.

Those changes are automated on the following playbook:

```
..\pg_minor_upgrade.yml
```

## The main steps

The main steps on the read-only replicas, are:

* Disable chef-client.

* Execute the command: `sudo chef-client-disable`

Add the `no-failover` and `no-loadbalance` tags in Patroni ( in the config file patroni.yml).

* Reload patroni: `sudo systemctl reload patroni`

### Pre checks

Wait until the traffic is drained.

* Verify the connection status with the commad on pg_stat_activity:
`select count(*) from pg_stat_activity where backend_type = 'client backend' and state <> 'idle';`

Execute a checkpoint. Command: `gitlab-psql -c "checkpoint;"`

Shutdown PostgreSQL. Command: `sudo systemctl stop patroni`

### Main actions

Update the binaries:

```shell
# get a list of installed packages
sudo dpkg -l | grep postgres
# retrieve new lists of packages
sudo apt-get update -y
# update postgresql packages:
sudo apt-get install -y postgresql-client-12 postgresql-12 postgresql-server-dev-12 --only-upgrade
# update extensions packages:
sudo apt-get install -y postgresql-12-repack --only-upgrade
​# optional:
sudo apt-get install -y postgresql-common postgresql-client-common --only-upgrade
Start PostgreSQL. Command: `sudo systemctl start patroni && sudo systemctl status patroni`
```

Update extensions, on the primary database node:

```shell
`sudo gitlab-psql`
```sql
-- Get a list of installed and available versions of extensions in the current database:
select ae.name, installed_version, default_version,
case when installed_version <> default_version then 'OLD' end as is_old
from pg_extension e
join pg_available_extensions ae on extname = ae.name
order by ae.name;

-- Update 'OLD' extensions (example):
ALTER EXTENSION pg_stat_statements UPDATE;

### Post checks
1. Check connectivity with the command: `gitlab-psql -c "select pg_is_in_recovery();"`
2. Verify the version with the command: `gitlab-psql -c "select version();"`
3. Check Patroni and PostgreSQL logs
4. Verify replication lag is < 100 MB. Command: `sudo gitlab-patronictl list -t -W`
5. Restore the traffic by starting chef, which will remove the tags on the node, with the command: `sudo chef-client-enable`



After restoring the traffic, monitor the performance for 30 minutes from the node and the logs.

After executing the above process, to upgrade the primary node we could execute a switchover first.
