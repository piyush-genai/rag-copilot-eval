# Identity Verification

## Contact Information

- **Group**: SSCS:Authorization
- **Handbook**: [Identity Verification Engineering documentation](https://internal.gitlab.com/handbook/engineering/identity-verification/)
- **Slack**: [#g_sscs_authorization](https://gitlab.enterprise.slack.com/archives/C0610LVCSAY)

## Overview

Identity Verification is a feature integrated into gitlab.com's registration
flow and CI/CD Pipelines to protect the platform from abuse. It leverages
[Arkose](https://www.arkoselabs.com/) to assign new users a risk level (High,
Medium, or Low) during sign-up and based on this risk assessment, users are
required to complete verification steps before they can start using GitLab.

### Functionality

During sign-up new users are required to complete one of the following:

- Only [email verification](https://docs.gitlab.com/security/email_verification/) (Low-risk users)
- Email, and phone number verification (Medium-risk users)
- Email, phone number, and credit card verification (High-risk users)

Low-risk users are required to complete one of the following verification steps
before they can start running CI/CD pipelines:

- Phone number verification
- Phone number, and credit card verification (users with High-risk phone number)

Additionally, Arkose is also used to present users with a CAPTCHA before they
can perform phone number and credit card verification. This protects the
underlying API endpoints from automated attacks.

### Failures

#### Arkose Integration issues

Problems with Arkose should be escalated to Arkose team in [#ext-gitlab-arkose](https://gitlab.enterprise.slack.com/archives/C02SGF6RLPQ).

##### Impact

Arkose issues can lead to new users not able to complete sign-up or run CI/CD
pipelines. For example, in the past
[Increased Arkose Verification Failures on GitLab.com (a sev2 incident)](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/20420)
prevented users from completing Identity Verification.

##### Fail-Open Behavior

Identity Verification is designed to fail-open when specific problems with
Arkose are detected (e.g. service is down, spike in token verification
failures). See [Arkose integration](https://internal.gitlab.com/handbook/engineering/identity-verification/#arkose-integration).

##### Symptoms

Spike in Arkose token verification failures (# of failures is normally < 10% of
success + failures). This can be observed by looking at [logs for successful and failed Arkose token verifications](https://log.gprd.gitlab.net/app/r/s/v1VnK).

##### Mitigation

Arkose-related issues can be mitigated by disabling `arkose_labs_enabled` application setting. Doing this will

1. Disable user risk assessment during sign-up - all new users will only be required to complete email verification
2. Disable usage of Arkose CAPTCHA before users can perform phone number and credit card verification

This reduces our protection from abuse but will allow new users to continue
signing up to gitlab.com and use CI/CD pipelines.

## Documentation

- [Identity Verification feature documentation](https://docs.gitlab.com/security/identity_verification/)
- [Identity Verification Engineering documentation](https://internal.gitlab.com/handbook/engineering/identity-verification/)
