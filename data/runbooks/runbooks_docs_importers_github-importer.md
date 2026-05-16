# GitHub Importer Runbook

## Summary

The GitHub Importer allows customers to import projects directly from GitHub or GitHub Enterprise Server into GitLab. It uses the GitHub API to fetch repository data, issues, pull requests, and other metadata. This runbook provides support engineers with troubleshooting guidance for common GitHub import failures and performance issues.

## Troubleshooting

For comprehensive troubleshooting information, see the [GitHub Importer Troubleshooting Guide](https://gitlab.com/help/user/project/import/troubleshooting_github_import).

Common issues include:

- **Import fails due to missing prefix**: In GitLab 16.5 and later, add the `api/v3` prefix when importing from GitHub Enterprise URLs
- **Missing comments in large projects**: The GitHub API has a limit of approximately 30,000 notes. Use the **Use alternative comments import method** option to import beyond this limit
- **GitLab instance cannot connect to GitHub**: For Self-Managed instances behind proxies running GitLab 15.10 or earlier, add `github.com` and `api.github.com` to the allowlist for local requests
- **Pull request comments in wrong threads**: Comments created before 2017 may appear in separate threads due to GitHub API limitations
