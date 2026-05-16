[TOC]

# GitLab On-call Run Books

This project provides a guidance for Infrastructure Reliability Engineers and Managers who are starting an on-call shift or responding to an incident. If you haven't yet, review the [Incident Management](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/index.html) page in the handbook before reading on.

## On-Call

GitLab Reliability Engineers and Managers provide 24x7 on-call coverage to ensure incidents are responded to promptly and resolved as quickly as possible.

### Shifts

We use [incident.io](https://app.incident.io/gitlab/on-call/) to manage our on-call
schedule and incident alerting. We currently have one schedule for [Production Incidents][incident-io-eoc-schedule] staffed by SREs. We also have

Currently, rotations are weekly and the day's schedule is split 8/8/8 hours with engineers
on call as close to daytime hours as their geographical region allows.

### Joining the On-Call Rotation

When a new engineer joins the team and is ready to start shadowing for an on-call rotation,
they should add themselves to the [incident.io schedule][incident-io-eoc-schedule] on the relevant
shadow rotation.

## Checklists

- [Engineer on Call (EOC)](on-call/checklists/eoc.md)
- [Incident Manager on Call (IMOC)](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#incident-manager-on-call-imoc-responsibilities)
- [Communications Manager on Call (CMOC)](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#communications-manager-on-call-cmoc-responsibilities)

To start with the right foot let's define a set of tasks that are nice things to do before you go any further in your week

By performing these tasks we will keep the [broken window
effect](https://en.wikipedia.org/wiki/Broken_windows_theory) under control, preventing future pain
and mess.

## Things to keep an eye on

### Issues

First check [the on-call issues][on-call-issues] to familiarize yourself with what has been
happening lately. Also, keep an eye on the [#production][slack-production] and
[#incident-management][slack-incident-management] channels for discussion around any on-going
issues.

### Alerts

Start by checking how many alerts are in flight right now

- go to the [fleet overview dashboard](https://dashboards.gitlab.net/d/RZmbBr7mk/gitlab-triage) and check the number of Active Alerts, it should be 0. If it is not 0
  - go to the alerts dashboard and check what is being triggered
    - [gprd prometheus][prometheus-gprd]
    - [gprd prometheus-app][prometheus-app-gprd]
  - watch the [#production][slack-production] channel for alert notifications; each alert here should point you to the right [runbook][runbook-repo] to fix it.
  - if they don't, you have more work to do.
  - be sure to create an issue, particularly to declare toil so we can work on it and suppress it.

### Prometheus targets down

Check how many targets are not scraped at the moment. alerts are in flight right now, to do this:

- go to the [fleet overview dashboard](https://dashboards.gitlab.net/d/RZmbBr7mk/gitlab-triage) and check the number of Targets down. It should be 0. If it is not 0
  - go to the [targets down list] and check what is.
    - [gprd prometheus][prometheus-gprd-targets-down]
    - [gprd prometheus-app][prometheus-app-gprd-targets-down]
  - try to figure out why there is scraping problems and try to fix it. Note that sometimes there can be temporary scraping problems because of exporter errors.
  - be sure to create an issue, particularly to declare toil so we can work on it and suppress it.

## Incidents

First: don't panic.

If you are feeling overwhelmed, escalate to the [IMOC](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#incident-manager-on-call-imoc-responsibilities).
Whoever is in that role can help you get other people to help with whatever is needed.  Our goal is to resolve the incident in a timely manner, but sometimes that means slowing down and making sure we get the right people involved.  Accuracy is as important or more than speed.

Roles for an incident can be found in the [incident management section of the handbook](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/)

If you need to declare an incident, [follow these instructions located in the handbook](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#reporting-an-incident).

## Communication Tools

If you do end up needing to post and update about an incident, we use [Status.io](https://status.io)

On status.io, you can [Make an incident](https://app.status.io/dashboard/5b36dc6502d06804c08349f7/incident/create) and Tweet, post to Slack, IRC, Webhooks, and email via checkboxes on creating or updating the incident.

The incident will also have an affected infrastructure section where you can pick components of the GitLab.com application and the underlying services/containers should we have an incident due to a provider.

You can update incidents with the Update Status button on an existing incident, again you can tweet, etc from that update point.

Remember to close out the incident when the issue is resolved.  Also, when possible, put the issue and/or google doc in the post mortem link.

# Production Incidents

## [Reporting an incident](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#reporting-an-incident)

## Roles

During an incident, we have [roles defined in the handbook](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#roles-and-responsibilities)

## General guidelines for production incidents

- Is this an emergency incident?
  - Are we losing data?
  - Is GitLab.com not working or offline?
  - Has the incident affected users for greater than 1 hour?
- Join the `#incident management` channel
- If the _point person_ needs someone to do something, give a direct command: _@someone: please run `this` command_
- Be sure to be in sync - if you are going to reboot a service, say so: _I'm bouncing server X_
- If you have conflicting information, **stop and think**, bounce ideas, escalate
- Gather information when the incident is done - logs, samples of graphs, whatever could help figuring out what happened
- use `/security` if you have any security concerns and need to pull in the Security Incident Response team

### PostgreSQL

- [PostgreSQL](docs/patroni/postgres.md)
- [more postgresql](docs/patroni/postgresql.md)
- [PgBouncer](docs/pgbouncer/pgbouncer-1.md)
- [PostgreSQL High Availability & Failovers](docs/patroni/pg-ha.md)
- [PostgreSQL switchover](howto/postgresql-switchover.md)
- [Read-only Load Balancing](docs/uncategorized/load-balancing.md)
- [Add a new secondary replica](docs/patroni/postgresql-replica.md)
- [Database backups](docs/patroni/postgresql-backups-wale-walg.md)
- [Database backups restore testing](docs/patroni/postgresql-backups-wale-walg.md#database-backups-restore-testing)
- [Rebuild a corrupt index](docs/patroni/postgresql.md#rebuild-a-corrupt-index)
- [Checking PostgreSQL health with postgres-checkup](docs/patroni/postgres-checkup.md)
- [Reducing table and index bloat using pg_repack](docs/patroni/pg_repack.md)
- [Start a read-only psql console](docs/teleport/Connect_to_Database_Console_via_Teleport.md)
- [Maintenance](docs/patroni/postgres-maintenance.md)

### Frontend Services

- [GitLab Pages returns 404](docs/pages/gitlab-pages.md)
- [HAProxy is missing workers](docs/fleet-management/config_management/chef-troubleshooting.md)
- [Worker's root filesystem is running out of space](docs/monitoring/filesystem_alerts.md)
- [GitLab registry is down](docs/registry/gitlab-registry.md)
- [Sidekiq stats no longer showing](docs/sidekiq/sidekiq_stats_no_longer_showing.md)
- [Gemnasium is down](docs/uncategorized/gemnasium_is_down.md)
- [Blocking a project causing high load](docs/uncategorized/block-high-load-project.md)

### Supporting Services

- [Redis](docs/redis/redis.md)
- [Sentry is down](docs/monitoring/sentry-is-down.md)

### Gitaly

- [Gitaly error rate is too high](docs/gitaly/gitaly-error-rate.md)
- [Gitaly latency is too high](docs/gitaly/gitaly-latency.md)
- [Sidekiq Queues are out of control](docs/sidekiq/large-sidekiq-queue.md)
- [Workers have huge load because of cat-files](docs/uncategorized/workers-high-load.md)
- [Test pushing through all the git nodes](docs/git/git.md)
- [How to gracefully restart gitaly-ruby](docs/gitaly/gracefully-restart-gitaly-ruby.md)
- [Debugging gitaly with gitaly-debug](docs/gitaly/gitaly-debugging-tool.md)
- [Gitaly token rotation](docs/gitaly/gitaly-token-rotation.md)
- [Praefect is down](docs/praefect/praefect-startup.md)
- [Praefect error rate is too high](docs/praefect/praefect-error-rate.md)

### Importers

- [Importers runbooks](docs/importers/README.md)

### CI

- [Large number of CI pending builds](docs/ci-runners/ci_pending_builds.md)
- [The CI runner manager report a high number of errors](troubleshooting/ci_runner_manager_errors.md)

### Geo

- [Geo database replication](docs/patroni/geo-patroni-cluster.md)

### ELK

- [`mapper_parsing_exception` errors](troubleshooting/elk_mapper_parsing_exception.md)

## Non-Critical

- [SSL certificate expires](docs/haproxy/ssl_cert.md)
- [Troubleshoot git stuck processes](docs/git/git-stuck-processes.md)

## Non-Core Applications

- [version.gitlab.com](docs/version/version-gitlab-com.md)

### Chef/Knife

- [General Troubleshooting](docs/fleet-management/config_management/chef-troubleshooting.md)
- [Error executing action `create` on resource 'directory[/some/path]'](docs/uncategorized/stale-file-handles.md)

### Certificates

- [Certificate runbooks](certificates/README.md)

## Learning

### Alerting and monitoring

- [GitLab monitoring overview](docs/monitoring/README.md)
- [How to add alerts: Alerts manual](docs/monitoring/alerts_manual.md)
- [How to add/update deadman switches](docs/uncategorized/deadman-switches.md)
- [How to silence alerts](howto/silence-alerts.md)
- [Alert for SSL certificate expiration](docs/uncategorized/alert-for-ssl-certificate-expiration.md)
- [Working with Grafana](monitoring/grafana.md)
- [Working with Prometheus](monitoring/prometheus.md)
- [Upgrade Prometheus and exporters](docs/monitoring/upgrades.md)
- [Use mtail to capture metrics from logs](docs/uncategorized/mtail.md)
- [Mixins](docs/monitoring/mixins.md)

### CI

- [Introduction to Shared Runners](troubleshooting/ci_introduction.md)
- [Understand CI graphs](troubleshooting/ci_graphs.md)

### Access Requests

- [Deal with various kinds of access requests](docs/uncategorized/access-requests.md)

### Deploy

- [Get the diff between dev versions](docs/uncategorized/dev-environment.md#figure-out-the-diff-of-deployed-versions)
- [Deploy GitLab.com](https://ops.gitlab.net/gitlab-cookbooks/chef-repo/blob/master/doc/deploying.md)
- [Rollback GitLab.com](https://gitlab.com/gitlab-org/release/docs/-/blob/master/runbooks/rollback-a-deployment.md)
- [Deploy staging.GitLab.com](https://ops.gitlab.net/gitlab-cookbooks/chef-repo/blob/master/doc/staging.md)
- [Refresh data on staging.gitlab.com](https://ops.gitlab.net/gitlab-cookbooks/chef-repo/blob/master/doc/staging.md)
- [Background Migrations](https://gitlab.com/gitlab-org/release/docs/-/blob/master/runbooks/background-migrations.md)
- [Migration Skipping](docs/uncategorized/migration-skipping.md)

### Work with the fleet and the rails app

- [Reload Puma with zero downtime](docs/uncategorized/manage-workers.md#reload-puma-with-zero-downtime)
- [How to perform zero downtime frontend host reboot](docs/uncategorized/manage-workers.md#how-to-perform-zero-downtime-frontend-host-reboot)
- [Gracefully restart sidekiq jobs](docs/uncategorized/manage-workers.md#gracefully-restart-sidekiq-jobs)
- [Start a read-only rails console](docs/teleport/Connect_to_Rails_Console_via_Teleport.md)
- [Start a rails console in the staging environment](docs/uncategorized/staging-environment.md#run-a-rails-console-in-staging-environment)
- [Start a redis console in the staging environment](docs/uncategorized/staging-environment.md#run-a-redis-console-in-staging-environment)
- [Start a psql console in the staging environment](docs/uncategorized/staging-environment.md#run-a-psql-console-in-staging-environment)
- [Force a failover with postgres](docs/patroni/patroni-management.md#failoverswitchover)
- [Force a failover with redis](docs/uncategorized/manage-pacemaker.md#force-a-failover)
- [Use aptly](docs/uncategorized/aptly.md)
- [Disable PackageCloud](docs/uncategorized/stop-or-start-packagecloud.md)
- [Re-index a package in PackageCloud](docs/uncategorized/reindex-package-in-packagecloud.md)
- [Access hosts in GCP](docs/uncategorized/access-gcp-hosts.md)

### Restore Backups

- [Deleted Project Restoration](docs/uncategorized/deleted-project-restore.md)
- [PostgreSQL Backups: WAL-E, WAL-G](docs/patroni/postgresql-backups-wale-walg.md)
- [Work with GCP Snapshots](docs/uncategorized/gcp-snapshots.md)
- [PackageCloud Infrastructure And Recovery](docs/uncategorized/packagecloud-infrastructure.md)

### Work with storage

- [Understanding GitLab Storage Shards](docs/gitaly/storage-sharding.md)
- [How to re-balance GitLab Storage Shards](docs/gitaly/storage-rebalancing.md)
- [Build and Deploy New Storage Servers](docs/gitaly/storage-servers.md)
- [Manage uploads](docs/uncategorized/uploads.md)

### Mangle front end load balancers

- [Isolate a worker by disabling the service in the LBs](docs/haproxy/block-things-in-haproxy.md#disable-a-whole-service-in-a-load-balancer)
- [Deny a path in the load balancers](docs/haproxy/block-things-in-haproxy.md#deny-a-path-with-the-delete-http-method)
- [Purchasing/Renewing SSL Certificates](docs/haproxy/ssl_cert-1.md)

### Work with Chef

- [Create users, rotate or remove keys from chef](docs/fleet-management/config_management/manage-chef.md)
- [Speed up chefspec tests](docs/fleet-management/config_management/chefspec.md#tests-are-taking-too-long-to-run)
- [Chef Guidelines](docs/fleet-management/config_management/chef-guidelines.md)
- [Chef Vault](docs/fleet-management/config_management/chef-vault.md)
- [Debug failed provisioning](docs/fleet-management/config_management/debug-failed-chef-provisioning.md)

### Work with CI Infrastructure

- [Runners fleet configuration management](docs/ci-runners/fleet-configuration-management/README.md)
- [Investigate Abuse Reports](docs/ci-runners/ci-investigate-abuse.md)
- [Create runners manager for GitLab.com](docs/ci-runners/create-runners-manager-node.md)
- [Update docker-machine](docs/uncategorized/upgrade-docker-machine.md)
- [CI project namespace check](docs/ci-runners/ci-project-namespace-check.md)

### Work with Infrastructure Providers (VMs)

- [Getting Support from GCP](docs/uncategorized/externalvendors/GCP-rackspace-support.md)

### Manually ban an IP or netblock

- [Ban a single IP using Redis and Rack Attack](docs/redis/ban-an-IP-with-redis.md)
- [Ban a netblock on HAProxy](docs/haproxy/ban-netblocks-on-haproxy.md)

### Dealing with Spam

- [General procedures for fighting spam in snippets, issues, projects, and comments](https://docs.google.com/document/d/1V0X2aYiNTZE1npzeqDvq-dhNFZsEPsL__FqKOMXOjE8)

### ElasticStack (previously Elasticsearch)

Selected elastic documents and resources:

- docs/
  - elastic/
    - [elastic-cloud.md](docs/elastic/elastic-cloud.md) (hosted ES provider docs)
    - [exercises](docs/elastic/exercises) (e.g. cluster performance tuning)
    - [kibana.md](docs/elastic/kibana.md)
    - [README.md](docs/elastic/README.md) (ES overview)
    - troubleshooting/
      - [README.md](docs/elastic/troubleshooting/README.md) (troubleshooting overview)
  - [scripts/](elastic/scripts) (api calls used for admin tasks documented as bash scripts)
  - watchers/

### Advanced search integration in Gitlab (indexing Gitlab data)

[advanced-search-in-gitlab.md](docs/elastic/advanced-search-in-gitlab.md)

### Zoekt integration in Gitlab (indexing code, BETA)

[zoekt-integration-in-gitlab.md](docs/zoekt/)

### Logging

Selected logging documents and resources:

- docs/
  - logging/
    - [exercises](docs/logging/exercises) (e.g. searching logs in Kibana)
    - [README.md](docs/logging/README.md) (logging overview)
      - [quick-start](docs/logging/README.md#quick-start)
      - [what-are-we-logging](docs/logging/README.md#what-are-we-logging)
      - [searching-logs](docs/logging/README.md#searching-logs)
      - [logging-infrastructure-overview](docs/logging/README.md#logging-infrastructure-overview)
    - troubleshooting/
      - [README.md](docs/logging/troubleshooting/README.md)

### Internal DNS

- [Managing internal DNS](docs/uncategorized/internal_dns.md)

### Debug and monitor

- [Tracing the source of an expensive query](docs/uncategorized/tracing-app-db-queries.md)
- [Work with Kibana (logs view)](docs/logging/README.md#searching-logs)

### Secrets

- [Working with Google Cloud secrets](docs/uncategorized/working-with-gcloud-secrets.md)

### Security

- [Working with the CloudFlare WAF/CDN](howto/externalvendors/cloudflare.md)
- [OSQuery](docs/uncategorized/osquery.md)

### Other

- [Register new domain(s)](docs/uncategorized/domain-registration.md)
- [Manage DNS entries](docs/uncategorized/manage-dns-entries.md)
- [Setup and Use my Yubikey](docs/uncategorized/yubikey.md)
- [Purge Git data](docs/git/purge-git-data.md)
- [Getting Started with Kubernetes and GitLab.com](docs/kube/k8s-gitlab.md)
- [Using Chatops bot to run commands across the fleet](docs/uncategorized/deploycmd.md)

### Manage Package Signing Keys

- [Manage Repository Metadata Signing Keys](docs/packagecloud/manage-repository-metadata-signing-keys.md)
- [Manage Package Signing Keys](docs/packaging/manage-package-signing-keys.md)

### Adding runbooks rules

- Make it quick - add links for checks
- Don't make me think - write clear guidelines, write expectations
- Recommended structure
  - Symptoms - how can I quickly tell that this is what is going on
  - Pre-checks - how can I be 100% sure
  - Resolution - what do I have to do to fix it
  - Post-checks - how can I be 100% sure that it is solved
  - Rollback - optional, how can I undo my fix

# Running helper scripts from runbook

Inside of the [bin](bin) directory you can find a list of scripts that can help
running repetitive commands or setting up your machine to debug the
infrastructure. These scripts can be bash, ruby, python or any other executable.

`glsh` in the single entrypoint to interact with the [`bin`](bin) directory. For
example if you can `glsh hello` it will check if `hello` file exists inside of
[`bin`](bin) directory and execute it. You can also pass multiple arguments, that the
script will have access to.

Demo: <https://youtu.be/RsGgxm55YBg>

```shell
glsh hello arg1 arg2
```

## Install

```shell
git clone git@gitlab.com:gitlab-com/runbooks.git
cd runbooks
sudo make glsh-install
```

## Update

```shell
glsh update
```

## Create a new command

1. Create a new file inside of [`bin`](bin) directory: `touch bin/hello`
1. Populate the file with the contents that you want. The command below updates the file with a simple `echo` command.

    ```
    cat > bin/hello <<EOF
    #!/usr/bin/env bash

    echo "Hello from glsh"
    EOF
    ```

1. Make it executable: `chmod +x bin/hello`
1. Run it: `glsh hello`

# Developing in this repo

## Summary

Usually, following a change to the rules, you can test your new additions using:

```shell
make verify
```

Then, regenerate the rules using:

```shell
make generate
```

### Troubleshooting `make generate`

If you get errors while doing any of these steps try installing any missing dependencies:

```shell
make jsonnet-bundle
```

You may also run into errors around `jsonnet-tool` not being installed, even though it already is. These seem especially common after upgrading from `asdf` to `mise`. To re-install the tool, run:

```
rm -rf ~/.local/share/mise/downloads/jsonnet-tool
mise plugin add --force jsonnet-tool https://gitlab.com/gitlab-com/gl-infra/asdf-gl-infra.git
```

If the errors persist, read on for more details on how to set up your local environment.

## Generating a new runbooks image

To generate a new image you must follow the git commit guidelines below, this
will trigger a semantic version bump which will then cause a new pipeline
that will build and tag the new image.

:warning: **Note that Docker builds only occur when this repo is tagged.  When built, we also build the `${CI_DEFAULT_BRANCH}` and `latest` tags.  This also means that there's the potential that latest version of our Docker image **may not** match the latest code base in the repository.**

### Git Commit Guidelines

This project uses [Semantic Versioning](https://semver.org). We use commit
messages to automatically determine the version bumps, so they should adhere to
the conventions of [Conventional Commits (v1.0.0-beta.2)](https://www.conventionalcommits.org/en/v1.0.0-beta.2/).

#### TL;DR

- Commit messages starting with `fix:` trigger a patch version bump
- Commit messages starting with `feat:` trigger a minor version bump
- Commit messages starting with `BREAKING CHANGE:` trigger a major version bump.
- If you don't want to publish a new image, do not use the above starting
  strings.

### Automatic versioning

Each push to `master` triggers a [`semantic-release`](https://semantic-release.gitbook.io/semantic-release/)
CI job that determines and pushes a new version tag (if any) based on the
last version tagged and the new commits pushed. Notice that this means that if a
Merge Request contains, for example, several `feat:` commits, only one minor
version bump will occur on merge. If your Merge Request includes several commits
you may prefer to ignore the prefix on each individual commit and instead add
an empty commit summarizing your changes like so:

```
git commit --allow-empty -m '[BREAKING CHANGE|feat|fix]: <changelog summary message>'
```

## Tool Versioning

This project has adopted [`asdf version-manager`](https://github.com/asdf-vm/asdf) for tool versioning. Using `asdf` is recommended, although not mandatory. Please note that if you chose not to use `asdf`, you'll need to ensure that all the required binaries, an the correct versions, are installed and on your path.

## Contributor Onboarding

If you would like to contribute to this project, follow these steps to get your local development environment ready-to-go:

1. Follow the common environment setup steps described in <https://gitlab.com/gitlab-com/gl-infra/common-ci-tasks/-/blob/main/docs/developer-setup.md>.
1. Run the `./scripts/prepare-dev-env.sh` to download and install development dependencies, configure [`pre-commit` hooks](#pre-commit-hooks) etc.
1. That's it. You should be ready!

### Dependencies and required tooling

Following tools and libraries are required to develop dashboards locally:

- Go programming language
- Ruby programming language
- `go-jsonnet` - Jsonnet implementation written in Go
- `jsonnet-bundler` - package manager for Jsonnet
- `jq` - command line JSON processor

You can install most of them using `asdf` tool.

### Manage your dependencies using `asdf`

Before using `asdf` for the first time, install all the plugins by running:

```console
./scripts/install-asdf-plugins.sh
```

Running this command will automatically install the versions of each tool, as specified in the `.tool-versions` file.

```console
$ # Confirm everything is working with....
$ asdf current
go-jsonnet     0.16.0   (set by ~/runbooks/.tool-versions)
golang         1.14     (set by ~/runbooks/.tool-versions)
ruby           2.6.5    (set by ~/runbooks/.ruby-version)
```

You don't need to use `asdf`, but in such case you will need install all
dependencies manually and track their versions.

### Keeping Versions in Sync between GitLab-CI and `asdf`

`asdf` (and `.tool-versions` generally) is the SSOT for tool versions used in this repository.
To keep `.tool-versions` in sync with `.gitlab-ci.yml`, there is a helper script,
`./scripts/update-asdf-version-variables.sh`.

#### Process for updating a tool version

1. Update the version in `.tool-versions`
1. Run `asdf install` to install latest version
1. Run `./scripts/update-asdf-version-variables.sh` to update a refresh of the `.gitlab-ci-asdf-versions.yml` file
1. Commit the changes

### Go, Jsonnet

We use `.tool-versions` to record the version of go-jsonnet that should be used
for local development. The `asdf` version manager is used by some team members
to automatically switch versions based on the contents of this file. It should
be kept up to date. The top-level `Dockerfile` contains the version of
go-jsonnet we use in CI. This should be kept in sync with `.tool-versions`, and
a (non-gating) CI job enforces this.

To install [go-jsonnet](https://github.com/google/go-jsonnet), you have a few
options. We recommend using `asdf` and installing via `./scripts/install-asdf-plugins.sh`.

```shell
./scripts/install-asdf-plugins.sh
```

Alternatively, you could follow that project's README to install manually. Please ensure that you install the same version as specific in `.tool-versions`.

Or via homebrew:

```shell
brew install go-jsonnet
```

### `jsonnet-tool`

[`jsonnet-tool`](https://gitlab.com/gitlab-com/gl-infra/jsonnet-tool) is a small home-grown tool for
generating configuration from Jsonnet files. The primary reason we use it is because it is much faster
than the bash scripts we used to use for the task. Some tasks have gone from 20+ minutes to 2.5 minutes.

We recommend using asdf to manage `jsonnet-tool`. The plugin will be installed when

```console
# Install jsonnet-tool
./scripts/install-asdf-plugins.sh
# Install the correct version of jsonnet-tool from `.tool-versions`
asdf install
```

### Ruby

Ruby is managed through `asdf`. The version of Ruby is configured via the `.tool-versions` file.
Note that previously, contributors on this project needed to configure
[`legacy_version_file = yes`](https://asdf-vm.com/manage/configuration.html#legacy-version-file)
but this setting is no longer required.

## Test jsonnet files

There are 2 approaches to write a test for a jsonnet file:

- Use [`jsonnetunit`](https://github.com/yugui/jsonnetunit). This method is
  simple and straight-forward. This approach is perfect for writing unit tests
  that asserts the output of a particular method. The downside is that it
  doesn't support jsonnet assertion and inspecting complicated result is not
  trivial.
- When a jsonnet file becomes more complicated, consists of multiple
  conditional branches and chains of methods, we should think of writing
  integration tests for it instead. Jsonnet Unit doesn't serve this purpose
  very well. Instead, let's use Rspec. Note that we probably don't want to use
  RSpec for testing small jsonnet functions, the idea would more be for testing
  error cases or complicated scenarios where we need to be more expressive
  about the output we expect

We have two custom matchers for writing integration tests:

```ruby
expect(
  <<~JSONNET
  local grafana = import 'toolinglinks/grafana.libsonnet';

  grafana.grafanaUid("bare-file.jsonnet")
JSONNET
).to reject_jsonnet(/invalid dashboard path/i)
```

```ruby
expect(
  <<~JSONNET
  local grafana = import 'toolinglinks/grafana.libsonnet';

  grafana.grafanaUid("stage-groups/code_review.dashboard.jsonnet")
  JSONNET
).to render_jsonnet('stage-groups-code_review')

# Or a more complicated scenario

expect(
  <<~JSONNET
  local stageGroupDashboards = import 'stage-groups/stage-group-dashboards.libsonnet';

  stageGroupDashboards.dashboard('geo').stageGroupDashboardTrailer()
  JSONNET
).to render_jsonnet { |template|
  expect(template['title']).to eql('Group dashboard: enablement (Geo)')

  expect(template['links']).to match([
    a_hash_including('title' => 'API Detail', 'type' => "dashboards", 'tags' => "type:api"),
    a_hash_including('title' => 'Web Detail', 'type' => "dashboards", 'tags' => "type:web"),
    a_hash_including('title' => 'Git Detail', 'type' => "dashboards", 'tags' => "type:git")
  ])
}

# Or, if you are into matchers

expect(
  <<~JSONNET
  local stageGroupDashboards = import 'stage-groups/stage-group-dashboards.libsonnet';

  stageGroupDashboards.dashboard('geo').stageGroupDashboardTrailer()
  JSONNET
).to render_jsonnet(
  a_hash_including(
    'title' => eql('Group dashboard: enablement (Geo)'),
    'links' => match([
      a_hash_including('title' => 'API Detail', 'type' => "dashboards", 'tags' => "type:api"),
      a_hash_including('title' => 'Web Detail', 'type' => "dashboards", 'tags' => "type:web"),
      a_hash_including('title' => 'Git Detail', 'type' => "dashboards", 'tags' => "type:git")
    ])
  )
)
```

### Location of test files

- JsonnetUnit tests must stay in the same directory and have the same name as the jsonnet file being tested but ending in `_test.jsonnet`. Some examples:
  - `services/stages.libsonnet`  -> `services/stages_test.jsonnet`
  - `libsonnet/toolinglinks/sentry.libsonnet`  -> `libsonnet/toolinglinks/sentry_test.jsonnet`

- RSpec tests replicates the directory structure of the Jsonnet files inside `spec` directory and must end in `_spec.rb` suffixes. Some example:
  - `libsonnet/toolinglinks/grafana.libsonnet` -> `spec/libsonnet/toolinglinks/grafana_spec.rb`
  - `dashboards/stage-groups/stage-group-dashboards.libsonnet` -> `spec/dashboards/stage-groups/stage-group-dashboards_spec.rb`

### How to run tests?

- Run the full Jsonnet test suite in your local environment with `make test-jsonnet && bundle exec rspec`
- Run a particular Jsonnet unit test file with `scripts/jsonnet_test.sh periodic-queries/periodic-query_test.jsonnet`
- Run a particular Jsonnet integration test file with `bundle exec rspec spec/libsonnet/toolinglinks/grafana_spec.rb`

_Note_: Verify that you have all the jsonnet dependencies downloaded  before attempting to run the tests, you can
automatically download the necessary dependencies by running `make jsonnet-bundle`.

## Pre-commit hooks

This project supports a set of [`pre-commit`](https://pre-commit.com/) hooks which can assist catching CI validation errors before early. While they are not required, they are recommended.

After running the `./scripts/prepare-dev-env.sh` script as described in the [Contributor Onboarding](#contributor-onboarding) section, the `pre-commit` hooks will be automatically installed and ready to go.

When running `git commit`, the hooks will check all staged changes, ensuring that they are valid. The `pre-commit` checks may in some cases automatically fix any problems. If they do this, you'll need to stage the changes and try again.

```console
$ git commit
check for case conflicts.................................................Passed
check that executables have shebangs.....................................Passed
check json...........................................(no files to check)Skipped
check for merge conflicts................................................Passed
check that scripts with shebangs are executable..........................Passed
check for broken symlinks............................(no files to check)Skipped
check yaml...........................................(no files to check)Skipped
detect private key.......................................................Passed
fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook

Fixing scripts/prepare-dev-env.sh

fix utf-8 byte order marker..............................................Passed
trim trailing whitespace.................................................Passed
mixed line ending........................................................Passed
don't commit to branch...................................................Passed
jsonnetfmt...........................................(no files to check)Skipped
shellcheck...............................................................Passed
shfmt....................................................................Passed
```

## Debug options

Some debug options can be set via environment variables to influence the Jsonnet building process:

- `GL_JSONNET_CACHE_DEBUG`: We cache jsonnet outputs in the `.cache`, setting this variable to `true` prints cache misses on `$stderr`.
- `GL_JSONNET_CACHE_SKIP`: Setting this to `true` disables the jsonnet cache.
- `GL_JSONNET_GNU_PARALLEL`: Setting this to `true` makes `generate-jsonnet-rules` use GNU parallel instead of xargs, and produces a `joblog.txt` file. This can be useful for profiling build times.

## Contributing

Please see the [contribution guidelines](CONTRIBUTING.md)

# But always remember

![Dont Panic](img/dont_panic_towel.jpg)

<!-- Links -->
[on-call-issues]:                   https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues?scope=all&utf8=%E2%9C%93&state=all&label_name[]=oncall

[incident-io-eoc-schedule]:         https://app.incident.io/gitlab/on-call/schedules/01K5YWAGZ7YCQGAG7ATQ9XQWHW

[prometheus-gprd]:                  https://prometheus.gprd.gitlab.net/alerts
[prometheus-gprd-targets-down]:     https://prometheus.gprd.gitlab.net/consoles/up.html
[prometheus-app-gprd]:              https://prometheus-app.gprd.gitlab.net/alerts
[prometheus-app-gprd-targets-down]: https://prometheus-app.gprd.gitlab.net/consoles/up.html

[runbook-repo]:                     https://gitlab.com/gitlab-com/runbooks

[slack-incident-management]:        https://gitlab.slack.com/channels/incident-management
[slack-production]:                 https://gitlab.slack.com/channels/production
