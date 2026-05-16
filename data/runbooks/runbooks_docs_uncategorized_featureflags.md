# Feature Flags

We use [feature flags](https://docs.gitlab.com/ee/operations/feature_flags.html) extensively during GitLab development to allow us to do more controlled testing of new features, as well as revert quickly in the case of an incident. We control feature flags via GitLab chatops in Slack. We have an [issue template](https://gitlab.com/gitlab-org/gitlab/-/blob/master/.gitlab/issue_templates/Feature%20Flag%20Roll%20Out.md) prepared in the gitlab-or/gitlab project with regards to rolling out a new feature flag.

## Reverting Feature Flags

Should you need to disable a feature flag during an incident, the preferred method is to use chatops and set the flag to false.

```
/chatops gitlab run feature set <feature-flag-name> false
```

### Incase the ChatOps Command Fails

The ChatOps command above is usually sufficient for disabling a feature flag. However, if the command fails because the GitLab API is unavailable, an SRE (or anyone with SSH access to the `console-01-sv-gprd.c.gitlab-production.internal` host) can disable a feature flag directly from the gprd Rails Console by following these steps:

**Step 1: Connect to the Rails Console**

 Follow the instructions [here](../bastions/gprd-bastions.md#console-access) to gain Read/Write access to the Rails Console in `gprd`.

**Step 2: Verify the Feature Flag Status**

Once connected to the Rails Console, verify that the feature flag is enabled and that you are using the correct name. Run the command below, which should return true:

```ruby
Feature.enabled?(:<feature-flag-name>)
```

**Step 3: Disable the Feature Flag**

Run the following command to disable the feature flag:

```ruby
Feature.disable(:<feature-flag-name>)
```

Take note of the time you have run this command. You will be using the time in a subsequent step.

**Step 4: Post in the #production Slack Channel**

Inform the team in the #production Slack channel that you have disabled the feature flag from the `gprd` Rails Console. You can use a message similar to the following:

"I have disabled the `<feature-flag-name>` feature flag from the `gprd` Rails Console. I disabled the fature flag this way because the `gprd` API is currently unavailable or intermittent."

**Step 5: Create an Issue in [gitlab-com/gl-infra/feature-flag-log](https://gitlab.com/gitlab-com/gl-infra/feature-flag-log)**

When you are able to create issues in gitlab.com, create an issue in the [gitlab-com/gl-infra/feature-flag-log](https://gitlab.com/gitlab-com/gl-infra/feature-flag-log) project for posterity using the following format:

Title: `Feature flag <feature-flag-name> has been set to false on gprd`

Description:

```md
This feature flag was disabled from the `gprd` Rails Console due to an unavailable or intermittent API.

- Changed by @<your-gitlab-username> at <time feature flag was disabled in ISO 8604 format e.g. 2025-08-29T11:40:02+00:00>
- Host: https://gitlab.com
- Rollout issue: <Rollout Issue Link>
- Incident: <Incident Issue Link>

/label ~"host::gitlab.com" ~"change"
/close
```

Link the rollout issue for the feature flag into the issue you have created. The rollout issue can be found by searching for `Rollout of <feature flag>` in [gitlab-org/gitlab](https://gitlab.com/gitlab-org/gitlab/-/issues).

Make sure to link the issue you have created in feature-flag-log to the incident issue.
