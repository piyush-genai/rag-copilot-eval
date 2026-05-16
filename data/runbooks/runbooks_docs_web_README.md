<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# GitLab.com Web Service

* [Service Overview](https://dashboards.gitlab.net/d/web-main/web-overview)
* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22web%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::Web"

## Logging

* [Rails](https://log.gprd.gitlab.net/goto/15b83f5a97e93af2496072d4aa53105f)
* [Workhorse](https://log.gprd.gitlab.net/goto/464bddf849abfd4ca28494a04bad3ead)
* [Kubernetes](https://log.gprd.gitlab.net/goto/88eab835042a07b213b8c7f24213d5bf)

<!-- END_MARKER -->

## Debugging UI errors

When parts of the page fail to load or an error banner indicating something failed to load is visible, you can check the requests made by the browser to see the exact error.

Many of the asynchronous requests are GraphQL requests to `/api/graphql`. These requests will have a `x-gitlab-feature-category` header that can help identify the team responsible.

GraphQL requests can return a 200 response code but have errors in the response body. These can be found in the top-level `errors` key in the response JSON.

<!-- ## Summary -->

<!-- ## Architecture -->

<!-- ## Performance -->

<!-- ## Scalability -->

<!-- ## Availability -->

<!-- ## Durability -->

<!-- ## Security/Compliance -->

<!-- ## Monitoring/Alerting -->

<!-- ## Links to further Documentation -->
