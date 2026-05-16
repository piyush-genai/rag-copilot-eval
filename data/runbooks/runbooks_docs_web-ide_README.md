# Web IDE runbook

## Basic information

### Contact

- **Group**: AI:Editor Extensions: VS Code
- **Handbook**: [Editor Extensions: VS Code](https://handbook.gitlab.com/handbook/engineering/ai/editor-extensions-vscode/)
- **Group Slack channel**: [#g_editor-extensions](https://gitlab.enterprise.slack.com/archives/C058YCHP17C)
- **Feature Slack channel**: [#f_vscode_web_ide](https://gitlab.enterprise.slack.com/archives/C03CEHDPQGH)

### Availability

- gitlab.com, dedicated, and self-managed instances.
- Available on free-tier with the exception of AI-related capabilities.

### Core Functionality

- Source control: Modify one or more files in a local repository, commit, and push them to the remote repository.
- Extensions Marketplace: Install 3rd-party extensions to extend the core functionality of the editor.
- Integration with Duo Code Suggestions and Duo Chat.
- Markdown preview.

### Documentation

- [User documentation](https://docs.gitlab.com/user/project/web_ide/)
- [Troubleshooting instructions](https://docs.gitlab.com/user/project/web_ide/#troubleshooting)
- [Extension host domain configuration](https://docs.gitlab.com/administration/settings/web_ide/)
- [Extension marketplace configuration](https://docs.gitlab.com/administration/settings/vscode_extension_marketplace/)
- [Development documentation](https://gitlab.com/gitlab-org/gitlab-web-ide/-/tree/main/docs?ref_type=heads)

## Dashboards

- [Web IDE HTTP requests logs](https://log.gprd.gitlab.net/app/r/s/ttfDQ)
- [.cdn.web-ide.gitlab-static.net health dashboard](https://dashboards.gitlab.net/d/gitlab-static-main/gitlab-static3a-overview?orgId=1&var-PROMETHEUS_DS=mimir-gitlab-ops&var-environment=gprd)
- [Editor Extensions error budget dashboard](https://dashboards.gitlab.net/d/stage-groups-editor_extensions/stage-groups3a-editor-extensions3a-group-dashboard?orgId=1&from=now-6h%2Fm&to=now%2Fm&timezone=utc&var-PROMETHEUS_DS=mimir-gitlab-gprd&var-environment=gprd&var-stage=main&var-controller=$__all&var-action=$__all)
- [Web IDE sentry errors dashboard](https://new-sentry.gitlab.net/organizations/gitlab/issues/searches/28/?query=is%3Aunresolved+feature_category%3Aweb_ide&referrer=issue-list&sort=trends&statsPeriod=14d)
- [Tableau usage dashboard](https://10az.online.tableau.com/#/site/gitlab/views/EditorMetrics/WebIDEDashboardbyDeliveryType?:iid=1).
- Use the [Open VSX status page](https://status.open-vsx.org/) to check the status of the Open VSX service that provides 3rd-party extensions to the Web IDE.

## Troubleshooting and incident mitigation

### If the Web IDE doesn't load

1. Check the health of the `.cdn.web-ide.gitlab-static.net` service and the error budget Web IDE rails controllers. You can find links
to all dashboards in the [dashboards](#dashboards) section.
1. Check client-side errors in the Sentry dashboard.

Reach out to the [infrastructure platforms team assistance](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/getting-assistance/)
to recover `.cdn.web-ide.gitlab-static.net`.

### Customers experience CORS issues

You can find information about common CORS issues for the
Web IDE in the [user documentation](https://docs.gitlab.com/user/project/web_ide/#cors-issues).

### Rollback procedure

To revert the Web IDE editor version, Submit an MR reverting the `@gitlab/web-ide` npm package update in the GitLab Application [package.json](https://gitlab.com/gitlab-org/gitlab/-/blob/master/package.json?ref_type=heads)
file.

### Extensions Marketplace

Check the status of the Open VSX extensions registry in the Open VSX status page.

If necessary, we can disable the Extensions Marketplace or change the registry default URL in the gitlab.com admin portal. You can read the instructions in the [administration docs](https://docs.gitlab.com/administration/settings/vscode_extension_marketplace/).
