# Direct Transfer Importer Runbook

## Summary

Direct Transfer is GitLab's native project migration method that transfers groups and projects from one GitLab instance to another using the GitLab API. It provides the most complete data migration, including project settings, issues, merge requests, pipelines, and more.

## Troubleshooting

For comprehensive troubleshooting information, see the [Direct Transfer Known Issues](https://gitlab.com/help/user/group/import/#known-issues).

Common issues include:

- **Files with long filenames not migrated**: Files longer than 255 characters are not migrated ([issue 406685](https://gitlab.com/gitlab-org/gitlab/-/issues/406685))
- **DiffNote::NoteDiffFileCreationError**: In GitLab 16.9 and earlier, diffs on merge request notes may be missing ([issue 438422](https://gitlab.com/gitlab-org/gitlab/-/issues/438422))
- **Batch export failed from source instance**: Check disk space, memory, and database performance on source instance
- **Import takes too long**: Add more Sidekiq workers to destination instance or redistribute large projects
- **Shared members mapped as direct members**: Expected behavior when importing top-level groups
- **Scheduled scan execution policies not migrated**: Upgrade to GitLab 16.2 or later
- **Command exited with error code 15**: Transient error that GitLab automatically retries

For performance optimization, see [Reducing migration duration](https://gitlab.com/help/user/group/import/#reducing-migration-duration).
