<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# dev.gitlab.org Service

* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22dev-gitlab-org%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::DevGitlabOrg"

## Logging

* [Rails](https://nonprod-log.gitlab.net/app/r/s/FUSMg)
* [Gitaly](https://nonprod-log.gitlab.net/app/r/s/DUsV1)
* [GitLab Shell](https://nonprod-log.gitlab.net/app/r/s/nDLCx)
* [Sidekiq](https://nonprod-log.gitlab.net/app/r/s/k0z53)

<!-- END_MARKER -->

## Summary

This is an internal GitLab instance running GitLab CE. The omnibus-gitlab package on this server is a GitLab CE package
with required configuration to keep it operational. Regular omnibus-gitlab commands can be used on this node.

Although the environment has dev in its domain name, don't refer to it as dev, since that could be confused with a
local development environment.

The main uses for the `.org` environment:

* Building official artifacts
* Providing build isolation for SOX compliance (located on different instance and infrastructure)
* Certifying SBOM and provenance
* Controlling publishing of releases
* Controlling synchronization with Canonical after publishing
* Ensuring the ability to release GitLab for Self-Managed customers in case of a total outage of GitLab.com

## Architecture

Single VM Omnibus installation of GitLab, running the latest nightly CE package.

### Nightly package version tags

This section explains how to the running package can be correlated with the corresponding component
version for Rails, Gitaly, etc. The nightly package version tag contains information about the
Omnibus GitLab commit SHA and the pipeline in which the package was built.

**Sample version:** `18.7.0+rnightly.2232110042.583f3a9c-0`

```sh
user@dev-1-01-sv-dev-1.c.gitlab-dev-1.internal:~$ apt show gitlab-ce
Package: gitlab-ce
Version: 18.7.0+rnightly.2232110042.583f3a9c-0
...
Installed-Size: 4,019 MB
...
License: MIT
Download-Size: 1,399 MB
APT-Sources: https://packages.gitlab.com/gitlab/nightly-builds/ubuntu jammy/main amd64 Packages
...

```

* `18.7.0`: Current stable GitLab release
* `+rnightly`: Indication that this is a nightly package build
* `2232110042`: Pipeline ID where this package was built. This is a pipeline in the
[gitlab-org/omnibus-gitlab](https://gitlab.com/gitlab-org/omnibus-gitlab)
project in GitLab.com: `https://gitlab.com/gitlab-org/omnibus-gitlab/-/pipelines/2232110042`
* `583f3a9c`: Commit SHA at which this package was built. This refers to a commit in the Omnibus
  GitLab codebase: `https://gitlab.com/gitlab-org/omnibus-gitlab/-/commit/583f3a9c`

To find the Rails version for a given nightly package version (say
`18.7.0+rnightly.2232110042.583f3a9c-0`), go to the
[pipeline](https://gitlab.com/gitlab-org/omnibus-gitlab/-/pipelines/2232110042) using the pipeline
ID in the version tag. Then, open the `Ubuntu-22.04-branch`
[CI job](https://gitlab.com/gitlab-org/omnibus-gitlab/-/jobs/12540224633)[^1] and search for the text
`build-component_shas`[^2] in the job logs. This section
[reports the SHAs](https://gitlab.com/gitlab-org/omnibus-gitlab/-/jobs/12540224633#L4497) of all components
included in the nightly package:

``` shell
#### SHAs of GitLab Components
gitlab-rails : 7d37ca3fba9c62b3b5665630a94214c6c2e71eb6
gitlab-rails-ee : 7d37ca3fba9c62b3b5665630a94214c6c2e71eb6
gitlab-shell : 73d5ec55604c39ea9b4447a860d70fa4486ae599
gitlab-pages : 7f508608cbdb5252f4a15acae0f4fd301234a192
gitaly : 8f4748a573cb961eced7d8f94112a3f572cf5281
gitlab-kas : eb09c31bfeb3f691ca8a3588241abe7d25f3b345
```

<!-- ## Performance -->

<!-- ## Scalability -->

<!-- ## Availability -->

<!-- ## Durability -->

<!-- ## Security/Compliance -->

<!-- ## Monitoring/Alerting -->

## Links to further Documentation

1. [Automated Tasks](./automated-tasks.md)
1. [Maintenance Tasks](./maintenance-tasks.md)

[^1]: We are looking at the job for Ubuntu 22.04 here because the VM running dev.gitlab.org is
running Ubuntu 22.04 right now. If the OS version changse, then look for the appropriate job in the
CE nightly build pipeline.

[^2]: If you can not find it, you can also try searching by clicking on `Show complete raw` to view
the logs as plain text.
