# Import/Export Importer Runbook

## Summary

Import/Export allows customers to export projects from GitLab as a file and import them into another GitLab instance, or into a different namespace in the same GitLab instance. This method is useful for offline migrations or transferring projects between disconnected instances. This runbook provides support engineers with troubleshooting guidance for common import/export failures. Note: Project export files should not be used for backups, as not all items are exported and backups may not work reliably.

**Important Limitations:**

- Maximum import file size: 5 GiB (default)
- Maximum export size: 40 GiB
- Only the latest diff is preserved for merge requests
- Deploy keys are not imported
- Project members with Owner role are imported as Maintainer role
- Rate limits: 6 exports/imports per minute per user

## Troubleshooting

For comprehensive troubleshooting information, see the [Import/Export Troubleshooting Guide](https://gitlab.com/help/user/project/settings/import_export_troubleshooting).

Common issues include:

- **Export file generation fails**: Check available disk space and project size
- **Import fails with file validation error**: Verify export file integrity and format
- **Import completes but data is missing**: Check GitLab version compatibility and known limitations
- **PG::QueryCanceled error during import**: Increase database statement timeout or use Rake task for large projects

## Links to Further Documentation

- [Import/Export Documentation](https://docs.gitlab.com/ee/user/project/settings/import_export.html)
