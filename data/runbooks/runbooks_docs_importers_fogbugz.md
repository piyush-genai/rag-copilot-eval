# FogBugz Importer Runbook

## Summary

The FogBugz Importer allows customers to import issues and project data from FogBugz into GitLab. It uses the FogBugz API to fetch issue data and metadata, providing a migration path for FogBugz users. This runbook provides support engineers with troubleshooting guidance for common FogBugz import failures.

**Key Features:**

- Imports all cases and comments with original case numbers and timestamps
- Supports user mapping from FogBugz to GitLab
- Can re-import projects to create new copies
- Preserves case status and metadata

**Important Notes:**

- Only issues are imported (not repositories)
- User mapping must be configured during import
- Users can be mapped to GitLab users or left unmapped (adds full name to description)

## Troubleshooting

For comprehensive information about FogBugz importer configuration and user mapping, see the [FogBugz Importer Documentation](https://docs.gitlab.com/ee/user/project/import/fogbugz.html).

Common issues include:

- **Import fails with connection error**: Verify the FogBugz URL is correct and accessible, check SSL/TLS certificates
- **Import fails with authentication error**: Verify credentials are valid and have necessary permissions
- **User mapping not working**: Configure user mapping correctly during import - map each FogBugz user to a GitLab user or leave empty to add full name to description
- **Issues not imported or incomplete**: Check FogBugz API capabilities and user permissions
- **Import hangs or times out**: Monitor Sidekiq progress, increase timeouts, or consider importing in phases for large projects

## Links to Further Documentation

- [FogBugz Importer Documentation](https://docs.gitlab.com/ee/user/project/import/fogbugz.html)
