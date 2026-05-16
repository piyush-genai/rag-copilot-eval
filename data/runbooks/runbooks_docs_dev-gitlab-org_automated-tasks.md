# dev.gitlab.org - Automated tasks

1. Nightly builds: Every day at 1:30 UTC, a nightly build gets triggered on
   gitlab.com. The cron trigger times are currently defined at
   [the scheduled pipeline page in the `omnibus-gitlab` repository](https://gitlab.com/gitlab-org/omnibus-gitlab/-/pipeline_schedules).

1. Deployments: Every weekday at 3:20 UTC, the nightly CE packages gets
   automatically deployed on dev.gitlab.org. Any errors in the install process
   will be logged in [Sentry](https://sentry.gitlab.net/gitlab/devgitlaborg/).
   Slack notifications will appear in [`#dev-gitlab`]. The cron task is currently
   defined in
   [role file](https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/ab7fb71c3ec1b4ff1de92158c0d4e94f5bd48023/roles/dev-gitlab-org.json#L360-370).

[`#dev-gitlab`]: https://gitlab.slack.com/archives/C6WQ87MU3
