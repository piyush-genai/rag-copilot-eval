# Custom PostgreSQL Package Build Process for Ubuntu Xenial 16.04

Postgres Development community is no longer building packages for Ubuntu Xenial 16.04.
This procedure explains the process of building custom PostgreSQL 12.X packages that we can use until we migrate off Xenial.

## Package Build Process

For building new versions, copy the [postgresql-12.9-1](https://gitlab.com/gitlab-com/gl-infra/database/postgresql/postgresql-12.9-1/-/blob/main/README.md) repo into a separate project (stay consistent with naming: postgresql-version in the database/postgresql hierarchy
Edit the build.sh script to:

* Update the Postgres version (PGVER)
find the appropriate tag to clone from <https://salsa.debian.org/postgresql/postgresql.git>
* Update the patch file to produce the usable debian/control and debian/rules files;
* check out pipeline output for errors.
  * In particular, watch out for patch application failures and compilation errors
* Let the pipelines do the rest.
* Download created artifactory from the pipeline.

## Upload and Publish packages to Aptly

Follow the instructions from the [Aptly Runbook](../uncategorized/aptly.md) to add new files to the gitlab-utils repository.

## Set required Chef attributes

Update chef roles attributes to use the Aptly server for installing PostgreSQL packages, as well as the correct debug info packages:

```
    "gitlab-patroni": {
      "postgresql": {
        "use_gitlab_aptly": true,
        "dbg_debug_package": false
      },
```
