# PostgreSQL subtransactions

In August 2021 [we've learned that PostgreSQL subtransactions can contribute to
production incidents](https://gitlab.com/gitlab-org/gitlab/-/issues/338346)
causing database contention and saturating PostgreSQL replicas..

A subtransaction in PostgreSQL is created when we create a `SAVEPOINT` within
an active transaction. We decided to remove usage of all subtransactions from
our codebase.

As of the beginning of September 2021 subtransactions are not expected to be
used in our codebase. We check every database transaction originating GitLab
Rails and log detected subtransactions using application structured logger.
[Additional instrumentation has been introduced](https://gitlab.com/gitlab-org/gitlab/-/merge_requests/67918)
to achieve this.

## Elastic Watcher

At the beginning of September 2021 we also shipped [a new Elastic
Watcher](https://gitlab.com/gitlab-com/runbooks/-/merge_requests/3875) that is
supposed to notify engineers when a new transaction using subtransactions gets
detected in logs.

## What to do when you see this watcher firing notifications?

You might see a Slack notification about new subtransactions being detected.
It is important to create an issue with the information from the log in
`gitlab-org/gitlab` project:

- Add "Subtransaction:" to the issue title and describe when this happened.
- Copy & paste backtrace from the log entry into the issue body.
- Ping people that had been involved in removing subtransactions (@stanhu,
  @grzesiek) in the issue.
