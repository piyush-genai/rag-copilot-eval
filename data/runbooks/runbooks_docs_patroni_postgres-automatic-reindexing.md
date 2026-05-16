# GitLab application-side reindexing

GitLab comes with an application-side cronjob to execute database reindexing automatically and in background. This runbook links a couple relevant resources and documentation for this and contains steps to cancel reindexing actions during an emergency.

## What is reindexing?

Please refer to [pg_repack.md#what-is-bloat](pg_repack.md#what-is-bloat) for more background on bloat. Application-side reindexing is a background process that automatically deals with standard btree postgres indexes. It currently only supports "non-special" indexes, i.e. it does not support primary key indexes, unique indexes, expression indexes etc.. However, the majority of indexes is supported.

From a workflow perspective, when the reindexing kicks off, it estimates index bloat for all supported indexes using a heuristic. It then chooses the top N indexes by their bloat level and starts to recreate those. The recreating phase is similar to what `pg_repack` does under the hoods:

1. It creates a new temporary index on the sides and
1. then performs a renaming operation to swap indexes.

(1) is low-risk in terms of locks but incurs additional disk IO to create the replacement index. (2) needs a elevated lock on the table to perform the renaming operations. We have guards in place, so this does not end up stalling the site for a longer period of time. If this guard doesn't work out, the process is cancelled and cleaned up automatically (so we are not forcing the lock). It will be retried upon the next invocation.

## Schedule

The schedule is configured through Chef on the deploy VMs. The cronjob configuration is managed by Omnibus GitLab via the `database_reindexing` setting in `gitlab.rb`.

**Configuration location:**

- The cronjob is defined in `/var/opt/gitlab/crond/database-reindexing` on deploy VMs
- Configuration is set via `gitlab_rails['database_reindexing']` in `gitlab.rb`
- The Omnibus recipe that enables this is `gitlab::database_reindexing_enable`

**Schedule:**

- Runs on deploy VMs in `gprd` and `gstg` environments
- Schedule: `12 * * * 0,6` (every hour at 12 minutes past, on Saturdays and Sundays) - [definition](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/5d349ade7cc3ec1250e96222cd2ddbfa1d9b075c/roles/gprd-base-deploy-node.json#L92)
- Executes: `/opt/gitlab/bin/gitlab-rake gitlab:db:reindex`

**Important notes:**

- The deploy VMs connect directly to the primary database node (not through PgBouncer)
- The `gitlab:db:reindex` task performs both automatic reindexing and async index creation operations
  - This Rake task has limitations on the job's workload that are defined inside [the GitLab codebase](https://gitlab.com/gitlab-org/gitlab/blob/d1a3831ac355cf2e269d32a5c2d768c908262fe3/lib/tasks/gitlab/db.rake#L365-365)
  - It will create at most 2 async indexes and re-index at most 2 existing indexes
  - The Rake task [identifies](https://gitlab.com/gitlab-org/gitlab/blob/d1a3831ac355cf2e269d32a5c2d768c908262fe3/lib/gitlab/database/reindexing.rb#L48-57) what to re-index using an index bloat heuristic
- Logs are available in `/var/log/gitlab/crond/` on the deploy VMs and are ingested into Kibana
  - Reindexing logs: <https://log.gprd.gitlab.net/app/r/s/3rNMD>
  - Async index creation logs: <https://log.gprd.gitlab.net/app/r/s/g460p>

**Future migration:**

- There is an ongoing effort to migrate these operations from deploy VMs to Kubernetes
- See [delivery#21650](https://gitlab.com/gitlab-com/gl-infra/delivery/-/issues/21650) for details on the migration plan

## How automation picks indexes

In order to pick relevant indexes for reindexing, the job uses a bloat heuristic to determine bloat levels for all indexes. Any run of the job picks the 2 most bloated indexes by their relative bloat level.

The bloat heuristic is only available for btree and GiST indexes, GIN indexes are not supported.

Overall, the following limitations apply currently:

1. Type: Only btree and GiST indexes
1. Maximum size: Automatic reindexing only for indexes < 100 GB current size.

### Explicit reindexing queue

In order to schedule specific reindexes for a rebuild, we can enqueue those indexes in the "reindexing queue". This queue is consumed and emptied before any indexes are being picked from the bloat heuristic described above. This can be handy for indexes that are not supported, e.g. GIN indexes or indexes beyond a certain size (see above).

As an example, let's schedule `public.index_merge_request_diff_commits_on_sha` for a rebuild:

```ruby
$ gitlab-rake gitlab:db:enqueue_reindexing_action[public.index_merge_request_diff_commits_on_sha]

Queued reindexing action: queued action [ id = 1, index: public.index_merge_request_diff_commits_on_sha ]
There are 1 queued actions in total.
```

After having enqueued the index for a rebuild, the subsequent run of `gitlab-rake gitlab:db:reindex` is going to execute the rebuild for this and other queued indexes, if any (up to 2 indexes in total per execution). If the queue is empty, we fall back to picking indexes automatically.

The queue can be examined, for example:

```sql
gitlabhq_production=# select * from postgres_reindex_queued_actions WHERE state = 0;
 id |                       index_identifier                        | state |          created_at           |          updated_at
----+---------------------------------------------------------------+-------+-------------------------------+-------------------------------
  1 | public.index_merge_request_diff_commits_on_sha                |     0 | 2021-11-04 10:35:05.396064+00 | 2021-11-04 10:35:05.396064+00
```

States for these queued actions include:

```
state = 0: queued
state = 1: done
state = 2: failed
```

## How to monitor

Grafana gets annotations for any reindexing action that is happening. As an example, the [PostgreSQL Overview](https://dashboards.gitlab.net/d/000000144/postgresql-overview?orgId=1) has those enabled for production. Annotations have tags `reindex` and `gprd` or `gstg` among others, so this can be filtered upon.

In order to understand ongoing and historic reindexing actions, one can also peek at the tracking table in PostgreSQL (using a psql session):

```sql
gitlabhq_production=# select * from postgres_reindex_actions order by action_start desc limit 10;
  id  |         action_start          |          action_end           | ondisk_size_bytes_start | ondisk_size_bytes_end | state |                         index_identifier                          | bloat_estimate_bytes_start
------+-------------------------------+-------------------------------+-------------------------+-----------------------+-------+-------------------------------------------------------------------+----------------------------
 1252 | 2021-01-29 13:00:18.806929+00 | 2021-01-29 13:00:26.122366+00 |               156024832 |              75317248 |     1 | public.index_projects_on_last_repository_check_failed             |                   80945152
 1251 | 2021-01-29 12:57:15.52368+00  | 2021-01-29 13:00:18.666019+00 |               806748160 |             800751616 |     1 | public.index_ci_builds_on_auto_canceled_by_id                     |                  326344704
 1250 | 2021-01-29 12:20:39.034396+00 | 2021-01-29 12:20:49.181661+00 |               163807232 |             161005568 |     1 | public.index_label_links_on_target_id_and_target_type             |                    9543680
 1249 | 2021-01-29 12:14:32.051548+00 | 2021-01-29 12:20:38.900695+00 |              2526797824 |            2544500736 |     1 | public.index_notes_on_discussion_id                               |                  190005248
 1248 | 2021-01-29 11:18:23.072552+00 | 2021-01-29 11:18:38.730528+00 |               123117568 |             112795648 |     1 | public.index_merge_requests_on_created_at                         |                   10723328
 1247 | 2021-01-29 11:14:24.531267+00 | 2021-01-29 11:18:22.915425+00 |              2256084992 |            2244321280 |     1 | public.index_ci_builds_on_commit_id_and_type_and_name_and_ref     |                  185147392
 1246 | 2021-01-29 10:14:56.482897+00 | 2021-01-29 10:15:25.278484+00 |               180912128 |             180207616 |     1 | public.index_issues_on_project_id_and_closed_at                   |                   50782208
 1245 | 2021-01-29 10:14:13.057911+00 | 2021-01-29 10:14:56.421322+00 |               537165824 |             536363008 |     1 | public.index_ci_pipelines_on_project_id_and_ref_and_status_and_id |                   66338816
 1244 | 2021-01-29 09:14:31.813057+00 | 2021-01-29 09:14:37.906965+00 |                76464128 |              75309056 |     1 | public.index_project_pages_metadata_on_artifacts_archive_id       |                   31367168
 1243 | 2021-01-29 09:14:25.056542+00 | 2021-01-29 09:14:31.749049+00 |                76832768 |              75309056 |     1 | public.index_project_pages_metadata_on_pages_deployment_id        |                   31506432
(10 rows)
```

The `state` column [translates](https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/database/reindexing/reindex_action.rb#L10) as follows:

1. 0 - `started`
1. 1 - `finished`
1. 2 - `failed`

## How to stop

In order to disable the cronjob, we can disable the `database_reindexing` feature flag (set to false). Further invocations of the cronjob will become a no-op until it is enabled again.

However, this does *not* affect an ongoing reindexing operation. If this operation needs to be stopped in an emergency situation, the following steps can be considered:

### Cancel the postgres backend performing the index rebuild

1. Log into the postgres primary using psql
1. Check current activity: `select pid, query from pg_stat_activity where query ~* 'create index';`
1. In order to cancel the index build, signal the PG backend: `select pg_cancel_backend(pid) from pg_stat_activity where query ~* 'create index' and pid <> pg_backend_pid()`
1. As a last resort, terminate the PG backend (this translates to `SIGKILL` and should be used only as a last resort and upon review): `select pg_terminate_backend(pid) from pg_stat_activity where query ~* 'create index' and pid <> pg_backend_pid()`

### Cancel the process on the deploy node

Log into the deploy host and terminate the reindexing process: `pgrep -f gitlab:db:reindex| xargs kill`

## Documentation

1. [Omnibus docs](https://docs.gitlab.com/omnibus/settings/database.html#automatic-database-reindexing)
1. [GitLab docs (draft)](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/50369)

## Metrics

1. [Long-term tamland forecast](https://gitlab-com.gitlab.io/gl-infra/tamland/patroni.html#patroni-service-pg_btree_bloat-resource-saturation) (internal link)
