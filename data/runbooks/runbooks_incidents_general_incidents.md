# Incidents

First: don't panic

If you are feeling overwhelmed, escalate to the [IMOC or CMOC](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#roles).
Whoever is in that role can help you get other people to help with whatever is needed.  Our goal is to resolve the incident in a timely manner, but sometimes that means slowing down and making sure we get the right people involved.  Accuracy is as important or more than speed.

Roles for an incident can be found in the [incident management section of the handbook](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/)

If you need to [report an incident](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#report-an-incident-via-slack), type `/incident` or `/inc` in Slack and follow the prompts - a bot will make and issue/google doc and zoom link for you.

## Communication Tools

If you do end up needing to post and update about an incident, we use [Status.io](https://status.io)

On status.io, you can [Make an incident](https://app.status.io/dashboard/5b36dc6502d06804c08349f7/incident/create) and Tweet, post to Slack, IRC, Webhooks, and email via checkboxes on creating or updating the incident.

The incident will also have an affected infrastructure section where you can pick components of the GitLab.com application and the underlying services/containers should we have an incident due to a provider.

You can update incidents with the Update Status button on an existing incident, again you can tweet, etc from that update point.

Remember to close out the incident when the issue is resolved.  Also, when possible, put the issue and/or google doc in the post mortem link.

## IMOC Checklist

As we start to open up the role of IMOC, we realized we should add an IMOC checklist for things done in the role when joining an incident.

### Assess the overall status

Take a minute to assess the overall situation:

1. Are we down, degraded, how concerned should we be?
2. Are we in S1 / all hands on deck?
3. Do I need to be ready to yell for help?

Look at [Apdex and Error Ratio Graphs](https://dashboards.gitlab.net/d/general-service/general-service-platform-metrics?orgId=1).

1. Are there spikes or dips passing the outage SLO dashed lines?
1. Be concerned if:
   1. the graph has been past the SLO for outage for more than 5 min.
   1. the slope of the graph is continuing down for the last 5 min.
1. Is GitLab.com up/degraded? Start with [general: GitLab Dashboards](https://dashboards.gitlab.net/d/general-public-splashscreen/general-gitlab-dashboards?orgId=1) and then drill further
    * [Web](https://dashboards.gitlab.net/d/web-main/web-overview?orgId=1). This is what users see.
    * [API](https://dashboards.gitlab.net/d/api-main/api-overview?orgId=1). This is what automation (including gitaly/registry/kas) sees.
2. Are runners doing okay?
    * [ci-runners: Overview](https://dashboards.gitlab.net/d/ci-runners-main/ci-runners-overview?orgId=1)
3. Other services overview:
    * [general: Service Platform Metrics](https://dashboards.gitlab.net/d/general-service/general-service-platform-metrics?orgId=1). You can pick services here in the “type” dropdown. Make sure environment is `gprd` (not `gstg`) and stage is `main` (all servers) or `cny` (canary) depending on what you are looking at.

### Lower stress of the EOC

During a high-profile and high-impact incident (e.g severity 1), one of your primary responsibilities as Incident Manager is to help lower the stress levels of the Engineer On-Call.

See the guidance from the IMOC onboarding:

* [How does an Incident Manager effectively engage with the Engineer On-Call?](https://gitlab.com/gitlab-com/gl-infra/reliability/-/blob/master/.gitlab/issue_templates/onboarding-im.md#how-does-an-incident-manager-effectively-engage-with-the-engineer-on-call).

### Estimate the Severity of the issue

Estimate the severity of the issue as soon as EOC or you have an idea on what the problem is. Evaluate based on [Availability](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/engineering-productivity/issue-triage/#availability). Sometimes it is tough to say to the upset customer that their issue is not S1 for us, but we need to think about the whole situation and other users.

If the incident directly affects availability for customers and you have access to a sample of namespace IDs or names you can use the [ChatOps](https://handbook.gitlab.com/handbook/support/workflows/chatops/#namespace) tool to quickly establish the tier and number of members. The `find` command takes up to 5 namespaces at a time.

We prefer to avoid [hotpatches](https://gitlab.com/gitlab-org/release/docs/-/blob/master/general/deploy/post-deployment-patches.md#overview). If a hotpatch is being considered, the issue severity will drive the decision:

1. Hotpatches are usually for S1 issues.
1. Security issues may receive a hotpatch regardless of severity.
1. Lower severity bugs that are still a major blocker may receive a hotpatch, but pull in the dev team, support, and PM to reassess and confirm severity.
    * In situations where reputational risk is high, even a non S1 issue can receive a hotpatch. If that is the case, the incident can’t be lower than S2. This is not strictly documented for a reason, because it gives the IMOC, EOC, Release Managers the power to decide based on the situation. It is critical that there is some flexibility and common sense in the process.
    * Will the situation degrade, or is it ‘stable’ and next deploy will fix?

Reasons that we are careful about hot patches:

1. There is a cognitive/disruptive workload introduced (multiple people co-ordinating/reviewing/wrangling) that is out-of-band from our otherwise structured and generally automated release procedures.
2. They occasionally hit edge cases and have to be re-done
3. Generally riskier (may not get any automated CI tests, we're trusting the diff that is applied to be accurate and not introduce any new problems).

### Timers/Mental checks

As an IMOC, on roughly these times, you can ask yourself these questions:

1. Do we have the right people in the incident room? (every 5 min early on)
2. Do we need [DB team help](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/database/)? (if postgres related, have we engaged DBRE or the Database team?)
3. Do we understand what is going on? (first 10 min frequently - every 2-3 min)
    * If not sev1/down, a little more relaxed - say every 15 min
4. Do we understand what to do to resolve or mitigate the problem? (first 10 min frequently after we have identified the issue- every 2-3 min)
    * If not sev1/down, again a little more relaxed, every 15 min
5. Do we need a [CMOC](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/#how-to-engage-the-cmoc)?  Is this customer facing?  Default to yes, but if deploy blocker - probably no.
6. Regularly check on the EOC. EOC is in a highly stressful situation, pager is going off every few minutes and they are asked to try and deduct what is happening. As IMOC, you need to support the EOC.
7. 10-15 minutes in.  Make sure there is an executive summary somewhere.  Most times at the top of the prod issue description.  If hard down, make sure gdoc exists with this summary.  Make sure the gdoc is shared in slack so people see it.
8. Help the EOC keep the Timeline tab in the incident issue up to date.  If you are collecting things, use issue comments, then edit the Timeline later.

### Handling S3/S4

If not on full alert, now in the realm of judgement related to next steps

1. Is this internal?
    * Deploy blocker?
    * Data team (replication delay)?
    * Are the right people involved to fix the problem? Ask for help if not.
2. You can click the runbooks links from the alerts in #production
    * Are we doing / have we done the things listed there?
3. If the alert is not actionable, review the [alert deletion guide](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/monitoring/deleting-alerts.md#an-impatient-sres-guide-to-deleting-alerts).
