# Postgres maintenance

## Prevent DDL operations before a database maintenance with `disallow_database_ddl_feature_flags`

During database maintenances, DDL statements should be ceased to avoid conflicts with the common maintenance operations like logical replication, maintenance DDLs, etc..
Each of these flags controls specific processes that can interfere with maintenance tasks:

- `partition_manager_sync_partitions`
- `execute_batched_migrations_on_schedule`
- `execute_background_migrations`
- `database_reindexing`
- `database_async_index_operations`
- `database_async_foreign_key_validation`
- `database_async_index_creation`

As the list of flags is quite extensive, and, each one needs to be manually disabled, a single feature flag called `disallow_database_ddl_feature_flags`
was added, to prevent DDL statements from happening in the database.

The feature flag `disallow_database_ddl_feature_flags` can enable or disable all of these flags as a group. This flag:

- Prevents DDL operations from happening in the database.
- Gives better support during a maintenance window

## Disable DDL operations before Postgres maintenance

To _disable_ all DDL operations, set `disallow_database_ddl_feature_flags` feature flag to `true`:

```shell
/chatops gitlab run feature set disallow_database_ddl_feature_flags true
```

## Re-enable DDL operations after Postgres maintenance

After maintenance is over, disable the `disallow_database_ddl_feature_flags` feature flag. If you do not, some processes will not be resumed:

```shell
/chatops gitlab run feature set disallow_database_ddl_feature_flags false
```
