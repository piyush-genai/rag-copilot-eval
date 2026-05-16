# Bitbucket Server Importer Runbook

## Summary

The Bitbucket Server Importer allows customers to import projects directly from Bitbucket Server (or Data Center) into GitLab. It uses the Bitbucket Server API to fetch repository data, pull requests, and other metadata. This runbook provides support engineers with troubleshooting guidance for common Bitbucket Server import failures.

## Troubleshooting

For comprehensive troubleshooting information, see the [Bitbucket Server Importer Troubleshooting Guide](https://gitlab.com/help/user/import/bitbucket_server#troubleshooting).

Common issues include:

- **Import fails with connection error**: Verify the Bitbucket Server URL is correct and accessible, check SSL/TLS certificates
- **Import fails with authentication error**: Verify credentials are valid and have necessary permissions
- **Import fails with "Import URL is blocked"**: Ensure Bitbucket Server is aware of proxy servers and proxy configuration is correct
- **LFS objects not imported**: If credentials contain special characters, URL-encode them (e.g., `@` becomes `%40`)
- **Import hangs or times out**: Monitor Sidekiq progress, increase timeouts, or consider importing in phases for large repositories
