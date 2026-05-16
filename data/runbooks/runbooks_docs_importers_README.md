# Importers Runbooks

## Summary

This section contains runbooks for GitLab's import functionality, which allows users to migrate projects and data from external sources into GitLab. Importers are a critical feature for the Create stage, enabling seamless onboarding of projects from various platforms. The Import team is responsible for maintaining and supporting all importer functionality. For urgent issues or escalations, [contact the Import team](https://handbook.gitlab.com/handbook/engineering/devops/create/import/#how-to-reach-us).

## Architecture

GitLab supports [multiple import methods](https://docs.gitlab.com/user/import/), each with different data sources and migration strategies.

### Dependencies

#### GitLab services

- **Database**: PostgreSQL for storing imported data
- **Sidekiq**: Background job processing for long-running imports
- **Redis**: Job queue management

#### Other

- **External APIs**: Connectivity to source platforms (GitHub, Bitbucket, etc.)
- **Network**: Outbound connectivity to external services

## Performance

Import performance depends on several factors:

- **Project size**: Larger projects with more data take longer to import
- **Sidekiq workers**: More workers on the destination instance improve throughput
- **Network latency**: Distance and connectivity between source and destination instances
- **External API rate limits**: Third-party platforms may throttle requests
- **Database performance**: Query optimization and available resources on destination

Typical import times:

- Small projects (< 100 MB): 5-15 minutes
- Medium projects (100 MB - 1 GB): 15-60 minutes
- Large projects (> 1 GB): 1-4+ hours

## Scalability

Import scalability considerations:

- **Concurrent imports**: Destination instance can handle 6 migrations per user. Each migration can have a collection of entities (projects or groups). A single migration usually runs up to 5 concurrent entities at a time.
- **Sidekiq capacity**: Scale Sidekiq workers based on import workload
- **Database connections**: Ensure sufficient database connection pool
- **Network bandwidth**: Monitor outbound bandwidth during bulk imports
- **Storage**: Ensure destination instance has sufficient disk space for imported data

## Availability

Import availability depends on:

- **Source instance availability**: Source must be accessible during import
- **Destination instance availability**: Destination must be operational
- **Network connectivity**: Stable connection between instances required
- **External service availability**: Third-party APIs must be accessible

Failed imports can typically be retried without data loss or duplication.

## Durability

Data durability during imports:

- **Transactional consistency**: Imports use database transactions where possible
- **Partial imports**: Failed imports may leave partial data; cleanup may be required
- **Backup strategy**: Ensure destination instance has backups before large imports
- **Audit trail**: Import operations are logged for compliance and troubleshooting

## Security/Compliance

Security considerations for importers:

- **Authentication**: Source credentials must be securely stored and transmitted
- **Authorization**: Verify user has permission to import from source
- **Data privacy**: Sensitive data (tokens, passwords) should not be logged
- **Network security**: Use HTTPS/TLS for all external connections
- **Access control**: Imported data inherits destination instance permissions

## Monitoring/Alerting

All importers share common monitoring patterns:

- Import job status tracking in Sidekiq
- Database performance during bulk data insertion
- API rate limiting from external sources
- Network connectivity to external services
- Import success/failure rates and duration metrics

### Common Issues

- **Rate limiting**: External APIs may throttle requests
- **Network timeouts**: Long-running imports may timeout. Timeouts can be cause by connection resets, DNS failures, TLS/SSL issues, proxy or firewall interference. Transferring large repositories, especially with many LFS objects or attachments, is inherently slow and also susceptible to connection issues.
- **Data validation**: Invalid or incompatible data from source
- **Permission issues**: Insufficient access to source repositories
- **Database constraints**: Duplicate keys or constraint violations

## Importer Runbooks

- [Direct Transfer](./direct-transfer.md)
- [Import/Export](./import-export.md)
- [GitHub Import](./github-importer.md)
- [Bitbucket Cloud](./bitbucket-cloud.md)
- [Bitbucket Server](./bitbucket-server.md)
- [Gitea](./gitea.md)
- [Repository by URL](./repository-by-url.md)
- [FogBugz](./fogbugz.md)
- [Manifest File](./manifest-file.md)

## Links to Further Documentation

- [GitLab Import Documentation](https://docs.gitlab.com/ee/user/project/import/)
- [Import API Documentation](https://docs.gitlab.com/ee/api/projects.html#import-a-project)
- [Import Group Documentation](https://docs.gitlab.com/ee/user/group/import/)
