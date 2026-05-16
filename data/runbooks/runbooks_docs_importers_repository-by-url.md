# Repository by URL Importer Runbook

## Summary

The Repository by URL Importer allows customers to import any Git repository by providing its URL. This method is useful for importing from any Git hosting platform or self-hosted Git servers that aren't directly supported by other importers. Note that this method imports only the repository; issues and merge requests are not imported. This runbook provides support engineers with troubleshooting guidance for common repository import failures.

## Troubleshooting

For comprehensive troubleshooting information, see the [Repository by URL Importer Documentation](https://docs.gitlab.com/ee/user/project/import/repo_by_url.html).

Common issues include:

- **Import fails with repository not found**: Verify the repository URL is correct and accessible
- **Import fails with authentication error**: Provide credentials for private repositories (in URL, SSH keys, or deploy keys)
- **Import hangs or times out**: Check repository size and network connectivity, increase timeouts if needed
- **Import succeeds but repository is empty**: Verify source repository is not empty

## Links to Further Documentation

- [Repository by URL Importer Documentation](https://docs.gitlab.com/ee/user/project/import/repo_by_url.html)
