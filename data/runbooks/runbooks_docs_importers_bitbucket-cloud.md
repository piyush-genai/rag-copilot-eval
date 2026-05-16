# Bitbucket Cloud Importer Runbook

## Summary

The Bitbucket Cloud Importer allows customers to import projects directly from Bitbucket Cloud into GitLab. It uses the Bitbucket Cloud API to fetch repository data, issues, pull requests, and other metadata. This runbook provides support engineers with troubleshooting guidance for common Bitbucket Cloud import failures.

## Troubleshooting

For comprehensive troubleshooting information, see the [Bitbucket Cloud Importer Troubleshooting Guide](https://gitlab.com/help/user/import/bitbucket_cloud#troubleshooting).

Common issues include:

- **Import process used wrong account**: Revoke GitLab access, sign out completely, and sign in with the correct Bitbucket account
- **User mapping fails despite matching names**: Verify that the username in Bitbucket account settings matches the public name in Atlassian account settings
- **Pull requests imported as empty merge requests**: Pull requests from forks or different projects are imported as empty merge requests (known limitation)
- **Import hangs or times out**: Monitor Sidekiq progress, increase timeouts, or consider importing in phases for large repositories
