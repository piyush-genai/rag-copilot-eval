# Getting help with GCP support and Rackspace

**Engineer(s) oncall - you now go to Google first in the GCP console for support tickets**

1. File support cases for GCP issues with the [Google Support case system](https://console.cloud.google.com/support/cases?organizationId=769164969568&supportedpurview=project). See the [readme in the vendor tracker](https://gitlab.com/gitlab-com/gl-infra/google-gitlab-tracker) for more details and additional escalation paths.
1. We use Rackspace for billing of GCP.  Questions for billing can be opened in the Rackspace portal.

## Support Portal and numbers

Google:

* There is also a dedicated slack channel to inquire about any issues which GCP may be seeing and for seeking assistance: [#ext-google-cloud](https://gitlab.slack.com/archives/C01KPV0V3SM)

Rackspace:

* Link to Portal <https://mycloud.rackspace.com>
* SRE managers and Infra Analysts have acces to the rackspace portal

## GitLab issues Trackers

**Google Vendor Tracker**:<https://gitlab.com/gitlab-com/gl-infra/google-gitlab-tracker>

**Rackspace Vendor Tracker**: <https://gitlab.com/gitlab-com/gl-infra/rackspace/issues>

## Contacts

Google:

* See the [readme in the vendor tracker](https://gitlab.com/gitlab-com/gl-infra/google-gitlab-tracker). The project is private due to confidential interactions with the vendor.

### Making a support ticket in Rackspace (For billing questions only)

Pick the Rackspace Ticketing System, Project ID: mgcp-1173105-ticket-escalation.  This will allow you to pick a severity.

Short history, due to automation needs from Rackspace, service accounts would need to be made in gitlab-production and we were not okay with that from a security point of view.  This temporary project is a workaround to let us pick severity on tickets and will be watched by our support there.

GitLab-production project is our GitLab.com SaaS application project and cases there will have the highest Priority.

Rackspace SLA for tickets is 4 hours for ticket response.
