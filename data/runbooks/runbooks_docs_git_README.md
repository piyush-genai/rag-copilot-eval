<!-- MARKER: do not edit this section directly. Edit services/service-catalog.yml then run scripts/generate-docs -->

# Git Access Service

* [Service Overview](https://dashboards.gitlab.net/d/git-main/git-overview)
* **Alerts**: <https://alerts.gitlab.net/#/alerts?filter=%7Btype%3D%22git%22%2C%20tier%3D%22sv%22%7D>
* **Label**: gitlab-com/gl-infra/production~"Service::Git"

## Logging

* [Rails](https://log.gprd.gitlab.net/goto/b368513b02f183a06d28c2a958b00602)
* [Workhorse](https://log.gprd.gitlab.net/goto/3ddd4ee7141ba2ec1a8b3bb0cb1476fe)
* [Puma](https://log.gprd.gitlab.net/goto/a2601cff0b6f000339e05cdb9deab58b)
* [nginx](https://log.gprd.gitlab.net/goto/8a5fb5820ec7c8daebf719c51fa00ce0)
* [Unstructured Rails](https://console.cloud.google.com/logs/viewer?project=gitlab-production&interval=PT1H&resource=gce_instance&advancedFilter=jsonPayload.hostname%3A%22git%22%0Alabels.tag%3D%22unstructured.production%22&customFacets=labels.%22compute.googleapis.com%2Fresource_name%22)
* [system](https://log.gprd.gitlab.net/goto/bd680ccb3c21567e47a821bbf52a7c09)

<!-- END_MARKER -->

<!-- ## Summary -->

<!-- ## Architecture -->

<!-- ## Performance -->

<!-- ## Scalability -->

<!-- ## Availability -->

<!-- ## Durability -->

<!-- ## Security/Compliance -->

<!-- ## Monitoring/Alerting -->

<!-- ## Links to further Documentation -->
