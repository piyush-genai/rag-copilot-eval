# OS Upgrade Reference Architecture

## Purpose

Define the architecture being used for the Patroni OS Upgrade as well as the steps to build and configure the infrastructure.

## Current Architecture

Current Production environment is composed of two Patroni Clusters:

* patroni-v12 (Primary Cluster)
* patroni-ci (Standby Cluster)

## Reference Architecture

### Patroni Cluster Architecture - Pre Upgrade

We will create additional cascade clusters on each environment to achieve the following architecture:

* `$ENV-patroni-main-pg12-1604` ( Main Primary Cluster - Source ) (Existing Cluster)
* `$ENV-patroni-main-pg12-2004` ( Main Standby Cluster - Target ) (New Cluster)
  * Replicates from `$ENV-patroni-main-pg12-1604`
* `$ENV-patroni-ci-pg12-1604` ( CI Standby Cluster - Source ) (Existing Cluster)
  * Replicates from `$ENV-patroni-main-pg12-1604`
* `$ENV-patroni-ci-pg12-2004` ( CI Standby Cluster - Target ) (New Cluster)
  * Replicates from `$ENV-patroni-main-pg12-2004`

![image pre-upgrade-architecture](./img/patroni-preupgrade-arch.png)

### Patroni Cluster Architecture - Post Upgrade

Once the upgrade is executed, we will have the following deployment:

* `$ENV-patroni-main-pg12-2004` (Primary - Patroni Main Cluster - Ubuntu 2004)
* `$ENV-patroni-ci-pg12-2004` (Standby - Patroni CI Cluster - Ubuntu 2004)
  * Replicates from `$ENV-patroni-main-pg12-2004`
* `$ENV-patroni-main-pg12-1604` (Standby Patroni Main Cluster - Ubuntu 1604)
  * Replicates from `$ENV-patroni-main-pg12-2004`
* `$ENV-patroni-ci-pg12-1604` (Standby - Patroni CI Cluster - Ubuntu 1604)
  * Replicates from `$ENV-patroni-main-pg12-1604`

![image post-upgrade-architecture](./img/patroni-postupgrade-arch.png)

## Infrastructure Provisioning

### Terraform definitions for the Reference Architecture

* [db-benchmarking](https://ops.gitlab.net/gitlab-com/gl-infra/config-mgmt/-/blob/main/environments/db-benchmarking/main.tf#L975-1239).

### Deploying the infrastructre via Terraform

**Patroni Main Clusters**

```
tf plan --target="module.patroni-main-pg12-1604" --target="module.patroni-main-pg12-2004" --out=patroni-main.plan
tf apply patroni-main.plan
```

**Patroni CI Clusters**

```
tf plan --target="module.patroni-ci-pg12-1604" --target="module.patroni-ci-pg12-2004" --out=patroni-ci.plan
tf apply patroni-ci.plan
```

### Chef Roles

**db-benchmarking environment:**

* [db-benchmarking-base-db-patroni-main-pg12-1604](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-patroni-main-pg12-1604.json)
* [db-benchmarking-base-db-patroni-main-pg12-2004](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-patroni-main-pg12-2004.json)
* [db-benchmarking-base-db-patroni-ci-pg12-1604](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-patroni-ci-pg12-1604.json)
* [db-benchmarking-base-db-patroni-ci-pg12-2004]( https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-patroni-ci-pg12-2004.json)
* [db-benchmarking-base-db-pgbouncer-main](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-pgbouncer-main.json)
* [db-benchmarking-base-db-pgbouncer-main-sidekiq](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-pgbouncer-main-sidekiq.json)
* [db-benchmarking-base-db-pgbouncer-ci](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-pgbouncer-ci.json)
* [db-benchmarking-base-db-pgbouncer-ci-sidekiq](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/db-benchmarking-base-db-pgbouncer-ci-sidekiq.json)

## Setup Patroni Clusters

Standby clusters are created from a Snapshot of the Primary Cluster. We need to reconfigure the DCS for them to work as expected. The following is an example of the procedure for the `db-benchmarking` environment:

### Reset Cluster Configs and Permissions

> Reconfiguring the existing `patroni-main` and `patroni-ci` clusters is not needed for `gstg` and `gprd`. We perform these steps on `db-benchmarking because we are deploying all clusters from scratch.

### Execute steps [1-3] on all 01 nodes of the following clusters

* `patroni-main-pg12-1604`
* `patroni-main-pg12-2004`
* `patroni-ci-pg12-1604`
* `patroni-ci-pg12-2004`

1 - Stop the Patroni service in all the nodes with the command:
```sudo systemctl stop patroni```

2 - Get the cluster name:
```sudo gitlab-patroni list```

3 - Remove the DCS entry from the cluster, executing :
`gitlab-patronictl remove db-benchmarking-patroni-main-pg12-1604`

Answer the name of the cluster that will be removed:
`db-benchmarking-patroni-main-pg12-1604`

Answer the confirmation message:
`Yes I am aware`

### Execute steps [4-6] in all nodes for all clusters

4 - Change the ownership from the data and log folders in all cluster nodes:

```
cd /var/opt/gitlab/
chown -R gitlab-psql:gitlab-psql postgresql/
chown -R gitlab-psql:gitlab-psql patroni/
cd /var/log/gitlab/
chown -R gitlab-psql:gitlab-psql postgresql/
chown -R syslog:syslog patroni/
```

5 - Delete recovery.conf config file if exists, for all nodes in all clusters:

```
sudo rm -rf /var/opt/gitlab/postgresql/data12/recovery.conf
```

6 - delete the patroni.dynamic.json file in all the nodes:

```
sudo rm -rf /var/opt/gitlab/postgresql/data12/patroni.dynamic.json
```

### Initialize Patroni clusters

> We execute the next steps in order since we want to ensure the `patroni-main-pg12-1604-01` node is the primary from the Source Cluster and `patroni-main-pg12-2004-01` is the Cascade Cluster Standby Leader.

**Initialize Patroni Main Cluster**

7 - Start the Patroni service on `patroni-main-pg12-1604-01` primary node:
```sudo systemctl start patroni```

8 - check the cluster status: `sudo gitlab-patronictl list`

Output:

```
mchacon@patroni-main-pg12-1604-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal:/var/log/gitlab$ sudo systemctl start patroni
mchacon@patroni-main-pg12-1604-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal:/var/log/gitlab$ sudo gitlab-patronictl list
+ Cluster: db-benchmarking-patroni-main-pg12-1604 (6959847276950353765) ---------+---------------+---------+----------+----+-----------+
| Member                                                                         | Host          | Role    | State    | TL | Lag in MB |
+--------------------------------------------------------------------------------+---------------+---------+----------+----+-----------+
| patroni-main-pg12-1604-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.28.101 | Replica | starting |    |   unknown |
+--------------------------------------------------------------------------------+---------------+---------+----------+----+-----------+
```

9 - Start the Patroni service on the Patroni Main Cluster secondaries: `sudo systemctl start patroni` after 30 seconds from starting the `patroni-main-pg12-1604-01` node. You do not need to wait for source 01 to be started completely.

10 - check the status: `sudo gitlab-patronictl list`

Output:

```
mchacon@patroni-main-pg12-1604-02-db-db-benchmarking.c.gitlab-db-benchmarking.internal:/var/log/gitlab$ sudo systemctl start patroni
mchacon@patroni-main-pg12-1604-02-db-db-benchmarking.c.gitlab-db-benchmarking.internal:/var/log/gitlab$ sudo gitlab-patronictl list
+ Cluster: db-benchmarking-patroni-main-pg12-1604 (6959847276950353765) ---------+---------------+---------+----------+----+-----------+
| Member                                                                         | Host          | Role    | State    | TL | Lag in MB |
+--------------------------------------------------------------------------------+---------------+---------+----------+----+-----------+
| patroni-main-pg12-1604-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.28.101 | Replica | starting |    |   unknown |
| patroni-main-pg12-1604-02-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.28.102 | Replica | starting |    |   unknown |
+--------------------------------------------------------------------------------+---------------+---------+----------+----+-----------+
```

**Initialize Patroni Cascade Clusters**

11 - Start the Patroni service on the Cascade Clusters primary nodes:
> You can start Patroni on these nodes 30 seconds after the secondaries from the source cluster. You do not need to wait for the secondaries 01 to be started completely. Wait 30 seconds between hosts.

* `patroni-main-pg12-2004-01`
* `patroni-ci-pg12-1604-01`
* `patroni-ci-pg12-2004-01`

`sudo systemctl start patroni`.

12 - Check the leader assumed: `sudo gitlab-patronictl list`
Output:

```
mchacon@patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal:/var/log/gitlab$ sudo gitlab-patronictl list
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+
| Member                                                                         | Host          | Role           | State   | TL | Lag in MB |
+ Cluster: db-benchmarking-patroni-main-pg12-2004 (6959847276950353765) ---------+---------------+----------------+---------+----+-----------+
| patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.16.101 | Standby Leader | running |  6 |           |
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+

```

13 - Start the Patroni service on the Cascade Cluster secondary nodes:

* `patroni-main-pg12-2004-02`
* `patroni-ci-pg12-1604-02`
* `patroni-ci-pg12-2004-02`

14 - Start the Patroni service on the standby clusters secondaries:
> You can start these host 30 seconds after the primaries from the standby clusters. You do not need to wait for the standby clusters 01 nodes to be started completely.

* `patroni-main-pg12-2004-02`
* `patroni-ci-pg12-1604-02`
* `patroni-ci-pg12-2004-02`

 `systemctl start patroni`.

15 - Check the leader assumed: `gitlab-patronictl list`

Output:

```
mchacon@patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal:~$ sudo gitlab-patronictl list
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+
| Member                                                                         | Host          | Role           | State   | TL | Lag in MB |
+ Cluster: db-benchmarking-patroni-main-pg12-2004 (6959847276950353765) ---------+---------------+----------------+---------+----+-----------+
| patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.16.101 | Standby Leader | running |  6 |           |
| patroni-main-pg12-2004-02-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.16.102 | Replica        | running |  6 |         0 |
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+
```

16 - Check and wait until the  standby clusters are completely online : `watch -n 2 sudo gitlab-patronictl list`

Output:

```
mchacon@patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal:~$ sudo gitlab-patronictl list
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+
| Member                                                                         | Host          | Role           | State   | TL | Lag in MB |
+ Cluster: db-benchmarking-patroni-main-pg12-2004 (6959847276950353765) ---------+---------------+----------------+---------+----+-----------+
| patroni-main-pg12-2004-01-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.16.101 | Standby Leader | running |  6 |           |
| patroni-main-pg12-2004-02-db-db-benchmarking.c.gitlab-db-benchmarking.internal | 10.255.16.102 | Replica        | running |  6 |         0 |
+--------------------------------------------------------------------------------+---------------+----------------+---------+----+-----------+

```
