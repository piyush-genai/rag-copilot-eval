## Infrastructure events

Infrastructure events are log messages that helpful for [incident management](https://about.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/) to help answer the question **what changes happened leading up to the event?**

* **[View events for Production](https://nonprod-log.gitlab.net/goto/2f2872632ccd39c3895e11290c77c346)**
* **[View events for Staging](https://nonprod-log.gitlab.net/goto/ff048cb673e91c294b66589ff3c61efb)**

We log events for the following actions:

* All infrastructure and deployment pipelines for the staging (`gstg`) and production (`gprd`) environments.
  * <https://ops.gitlab.net/gitlab-cookbooks/chef-repo/>
  * <https://ops.gitlab.net/gitlab-com/gitlab-com-infrastructure/>
  * <https://gitlab.com/gitlab-com/gl-infra/k8s-workloads>
* Chatops commands for Feature Flags and Canary
* PagerDuty events via a webhook listener <https://gitlab.com/gitlab-com/gl-infra/pd-event-logger>

Note that we do not currently differentiate between successful and failed deployments, tracked in <https://gitlab.com/gitlab-com/gl-infra/reliability/-/issues/12685>.
Other environments like `pre`, `release`, etc. are not included because they are not part of incident management.

There are two ElasticSearch indexes that are used for events, `events-gstg` and `events-gprd`.
These indexes are both configured in the non-prod ElasticSearch cluster nonprod-log.gitlab.net so that we are not tied to the availability of the production for event records.

### CI Variables

There is a dedicated user `events` in the nonprod cluster for sending events in the 1Password production vault named "User for sending infra events to ElasticSearch".

In CI, use the variable named `$ES_NONPROD_EVENTS_URL` for sending events with `curl`.

### Fields for events

The following fields are recommended for events:

| name       | type   |
| ---------- | ------ |
| `time`     | string |
| `type`     | string |
| `message`  | string |
| `env`      | string |
| `stage`    | string |
| `username` | string |
| `source`   | string |
| `diff_url` | string |

* `message`: Free-form text describing the event
* `env`: Either `gprd` or `gstg`.
* `stage`: Either `main` or `cny`
* `username`: GitLab username if available, if unknown use `unknown` as the value.
* `type`: The type of event, for example: `deployment`, `configuration`, `alert`, etc.
* `diff_url`: optional HTTP link, if a list of changes are available.
* `source`: optional source, may be a URL to a pipeline or job or free-form text

### Sending events from CI

The following snippet can be used to create shell function that will send events from CI

```yaml
.sendEvent:
  - &sendEvent
    |
      sendEvent() {
        command -v curl >/dev/null 2>&1 || \
          { echo >&2 "sending events requires curl but it's not installed."; exit 1; }
        MSG="$1"
        TYPE="${2:-configuration}"
        ENV="${3:-gprd}"
        TS=$(date -u +%s000)
        USERNAME="${GITLAB_USER_LOGIN:-unknown}"
        SOURCE="${CI_JOB_URL:-unknown}"
        DATA="
          {
            \"time\": \"$TS\",
            \"type\": \"$TYPE\",
            \"message\": \"$MSG\",
            \"env\": \"$ENV\",
            \"username\": \"$USERNAME\",
            \"source\": \"$SOURCE\"
          }
        "
        echo "Sending event: \"$MSG\""
        curl -s -X POST "$ES_NONPROD_EVENTS_URL/events-$ENV/_doc" -H 'Content-Type: application/json' -d "$DATA" > /dev/null
      }
```

Then in a new or existing `before_script` section:

```yaml
before_script:
  - *sendEvent
```

And call the shell function from the `script:` section:

```yaml
script:
  - ...
  - sendEvent "Starting an event"
  - ...
  - sendEvent "Finishing an event"
```
