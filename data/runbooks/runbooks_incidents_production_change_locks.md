## How to enact a Production Change Lock (PCL)

The PCL mechanism is described in the handbook in the [change management section](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/#production-change-lock-pcl).

This is a runbook for the steps to take to put a PCL in place.

### Who to consult

1. Check with the @release-managers in the #releases Slack channel to confirm the state of the monthly release or any security releases.
2. Check with security in the #security Slack channel if there are any imminent security patches that release managers may not be notified of yet.
3. Check with @incident-managers and @sre-oncall in the Slack #production channel to see if there are any concerns.

### Steps to put the PCL in place

1. Create an MR to add the PCL to the table on the [handbook page](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/#production-change-lock-pcl).
2. Create an MR to add the PCL to the [changelock.yml](https://gitlab.com/gitlab-com/gl-infra/change-lock/-/blob/master/config/changelock.yml?ref_type=heads). An example MR is [here](https://gitlab.com/gitlab-com/gl-infra/change-lock/-/merge_requests/49).
3. Add a CR ([see example](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/18551)) that will block deployments and feature flags.
   1. On the CR, notify the release managers who will be on duty during this period.
   2. If needed, get advance written confirmation on the CR issue in a comment as to who has permission to approve exempt changes during the PCL.
   3. Make sure someone marks the CR issue as ~"change::in-progress" at the start of the PCL.

In case of the need to deploy or execute Post Deployment Migrations during a PCL, Release Managers will open a CR (examples: [deployment CR](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/17150), [PDM CR](https://gitlab.com/gitlab-com/gl-infra/production/-/issues/17152)) to track the deployment. SRE On Call approval, Sr. Director+ of Infrastructure (or designated) is needed for each deployment CR. More details in [Release Docs](https://gitlab.com/gitlab-org/release/docs/-/blob/master/release_manager/pcl-guide.md)
When these are merged:

1. Put a message in the `#cto` Slack channel that the PCL is in place and cross post this to the other relevant Slack channels.
