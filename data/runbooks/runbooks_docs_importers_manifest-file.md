# Manifest File Importer Runbook

## Summary

The Manifest File Importer allows customers to import multiple projects in bulk using a manifest configuration file. This method is useful for migrating entire groups or organizations from other platforms into GitLab. The manifest must be an XML file up to 1 MB in size. GitLab requires PostgreSQL for manifest imports to work, as subgroups are needed for the import process. This runbook provides support engineers with troubleshooting guidance for common manifest import failures.

## Troubleshooting

For comprehensive information about manifest file format and configuration, see the [Manifest File Importer Documentation](https://docs.gitlab.com/ee/user/project/import/manifest.html).

Common issues include:

- **Import fails with manifest file validation error**: Verify manifest file format is valid YAML/JSON and all required fields are present
- **Some projects import successfully, others fail**: Check project configuration, URLs, and repository access
- **Import hangs or times out**: Monitor Sidekiq progress, increase timeouts, or consider importing in batches for large manifests
- **Projects imported but data is incomplete**: Verify manifest configuration includes data import settings

## Links to Further Documentation

- [Manifest File Importer Documentation](https://docs.gitlab.com/ee/user/project/import/manifest.html)
