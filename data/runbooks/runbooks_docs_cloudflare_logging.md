# Cloudflare Logs

Each Cloudflare zone pushes logs to a Google Cloud Storage (GCS) bucket with the name of `gitlab-<environment>-cloudflare-logpush`. This operation happens every 5 minutes so the logs don't give an immediate overview of what's currently happening.

Starting 2022-04-14 we enabled Logpush v2. These logs will be shipped to a distinct `v2` subdirectory in that GCS bucket.

They are partitioned by day with the format `v2/{http,spectrum}/dt=YYYYMMDD/` to enable the use of partitions in BigQuery to speed up queries.

Logpush v2 allows us to also access logs for Firewall events, DNS and NELs. These are not configured at the moment, but can be enabled if the need arises.

At least READ access to GCS in the `Production` project in GCP is required to be able to view these logs.

NELs are also already available as metrics [here](https://dashboards.gitlab.net/d/sPqgMv9Zk/cloudflare-traffic-overview?orgId=1&refresh=5m)

## BigQuery

The logs can be queried from the external tables `http` and `spectrum` in the BigQuery dataset `cloudflare_logs_$env` via [the BigQuery Studio](https://console.cloud.google.com/bigquery?project=gitlab-production&ws=!1m4!1m3!3m2!1sgitlab-production!2scloudflare_logs_gprd). Those tables are configured with partitioning enabled on the `dt` field to speed up queries by only loading data for the particular day(s) requested:

```sql
# Query HTTP logs for 5xx errors between 2024-11-01 and 2024-11-08
SELECT * FROM `cloudflare_logs_gprd.http` WHERE dt >= 20241101 AND dt < 20241108 AND EdgeResponseStatus >= 500;
# Query HTTP logs for a specific Ray ID
SELECT * FROM `cloudflare_logs_gprd.http` WHERE dt >= 20241101 AND dt < 20241108 AND RayID = '97f3d760a559d434';
# Query Spectrum logs for connections from embargoed countries on 2024-11-12
SELECT * FROM `cloudflare_logs_gprd.spectrum` WHERE dt = 20241112 AND upper(ClientCountry) in ("SY","KP","CU","IR") AND Event = 'disconnect';
```

## BigQuery (load)

Querying the external tables can result in timeouts. In this case you can resort to loading the data into a native BigQuery table `cloudflare_logs_${env}_native.{http,spectrum}` instead.

```bash
glsh cloudflare-bq-load --dry-run http 20250915

glsh cloudflare-bq-load http 20250915
glsh cloudflare-bq-load spectrum 20250915
```

This load job will take on the order of 5 minutes. But once the load is complete, queries will be fast.

Thes native tables are time-partitioned (hourly) by `EdgeStartTimestamp` for http, `Timestamp` for spectrum. Use those columns in your queries insteaed of `dt`.

Default retention is 7 days. Note that BigQuery does not deduplicate records. Importing the same day multiple times will result in duplicates. For incremental loads, you can perform a more targeted load of only new files.

Sample queries:

```sql
SELECT * FROM `cloudflare_logs_gprd_native.http` WHERE EdgeStartTimestamp BETWEEN '2025-09-14' AND '2025-09-15' AND EdgeResponseStatus >= 500;
SELECT * FROM `cloudflare_logs_gprd_native.http` WHERE EdgeStartTimestamp BETWEEN '2025-09-14' AND '2025-09-15' AND RayID = '97f3d760a559d434';
SELECT * FROM `cloudflare_logs_gprd_native.spectrum` WHERE TIMESTAMP_TRUNC(Timestamp, DAY) = '2024-11-12' AND upper(ClientCountry) in ("SY","KP","CU","IR") AND Event = 'disconnect';
```

## Processing the raw data

If you want to run more ad-hoc analysis, there is also a script, which allows us
to access a NDJSON stream of logs. This script can be found in
`scripts/cloudflare_logs.sh`. The script is adapted to make use of Logpush v2 data.

The usage of the script should be limited to a console host because of traffic
cost. It will need to read the whole logs for the provided timeframe.

Example:

To get the last 30 minutes of logs up until 2020-04-14T00:00 UTC as a stream,
use

```bash
./cloudflare_logs.sh -e gprd -d 2020-04-14T00:00 -t http -b 30
```

You can then `grep` on that to narrow it down. The use of `jq` on an unfiltered
stream is not recommended, as that significantly increases processing time.

Beware, that this process will take long for large timespans.

Full example to search for logs of a given project which have a 429 response
code:

```bash
./cloudflare_logs.sh -e gprd -d 2020-04-14T00:00 -t http -b 2880 \
  | grep 'api/v4/projects/<PROJECT_ID>' \
  | jq 'select(.EdgeResponseStatus == 429)'
```

Note: Due to the way logs are shipped into GCS, there might be a delay of up
to 10 minutes for logs to be available.

## Cloudflare Audit Logs

Different than traffic logging, Cloudflare audit information provides logs
on changes to the Cloudflare configuration. What account turned off a page
rule, or modified a DNS entry, etc.

* Log into cloudflare.com
* When you see a list of zones to manage, near the top of the page
  select `Audit Logs`

[Cloudflare Article](https://support.cloudflare.com/hc/en-us/articles/115002833612-Understanding-Cloudflare-Audit-Logs)

## Retention

Cloudflare logs will be retained for 91 days via GCS object lifecycle management.
