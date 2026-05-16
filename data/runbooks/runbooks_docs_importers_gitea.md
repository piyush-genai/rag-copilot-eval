# Gitea Importer Runbook

## Summary

The Gitea Importer allows customers to import projects directly from Gitea instances into GitLab. It uses the Gitea API to fetch repository data and metadata, providing a migration path for Gitea users. This runbook provides support engineers with troubleshooting guidance for common Gitea import failures.

**Key Features:**

- Supports post-migration user contribution mapping (GitLab 17.8+)
- Preserves repository public/private access
- Imports issues, pull requests, milestones, and labels
- Requires Gitea version 1.0.0 or later
- Imported items have an "Imported" badge

**Important Limitation:**

- Because Gitea is not an OAuth provider, authors/assignees cannot be automatically mapped to GitLab users. The project creator is set as the author initially, but post-migration mapping can reassign contributions.

## Troubleshooting

For comprehensive troubleshooting information, see the [Gitea Importer Documentation](https://docs.gitlab.com/ee/user/import/gitea.html) and [Post-migration User Mapping](https://docs.gitlab.com/ee/user/import/mapping.html).

Common issues include:

- **Import fails with connection error**: Verify the Gitea URL is correct and accessible, check SSL/TLS certificates
- **Import fails with authentication error**: Verify credentials are valid and have necessary permissions
- **User contributions assigned to project creator**: Use post-migration user mapping (GitLab 17.8+) to reassign contributions to correct users
- **Repository data not fully imported**: Check Gitea API capabilities and version compatibility
- **Import hangs or times out**: Monitor Sidekiq progress, increase timeouts, or consider importing in phases for large repositories

## Links to Further Documentation

- [Gitea Importer Documentation](https://docs.gitlab.com/ee/user/import/gitea.html)
