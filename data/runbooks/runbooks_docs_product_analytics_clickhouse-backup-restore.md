# Product Analytics ClickHouse Failure Remediation, Backup & Restore Process

Follow this runbook when a Product Analytics ClickHouse Cloud database is broken beyond repair and requires remediation.

## Check metrics

1. Check the metrics of the failed instance. Can the issue be mitigated in the first instance by increasing the available memory?
    * The [Clickhouse metrics dashboard](https://clickhouse.cloud/service/6ecb3dfd-fbc6-4889-b8b9-c667a2f5082a) shows available metrics.
    * Speak to a ClickHouse Cloud administrator to attempt this. (@mwoolf, @dennis should cover most working hours - alternatively try in #f_clickhouse)

## Speak to ClickHouse Cloud support

1. In the first instance, open a P1 support ticket in [ClickHouse Cloud](https://clickhouse.cloud).
2. Ping the team in #g_monitor_product_analytics and #analytics-section to make them aware of the failure.
2. Consider pinging ClickHouse team members in `clickhouse-gitlab-external431` to expedite the request.

## Restoring from Backup

> Only ClickHouse Cloud administrators are permitted to do this.

1. Create a new [Admin API key](https://clickhouse.cloud/organizations/8a0d56e3-d8f0-4e70-80bf-a8bf6ee950bd/keys)
    * Set an expiration of 1 hour.
2. Use `cURL` to list all clusters - `curl "https://api.clickhouse.cloud/v1/organizations/8a0d56e3-d8f0-4e70-80bf-a8bf6ee950bd/services" \
   -u '{API KEY}:{API SECRET}'`
3. Find the cluster in question and list its backups - `curl "https://api.clickhouse.cloud/v1/organizations/8a0d56e3-d8f0-4e70-80bf-a8bf6ee950bd/services/bf5e7003-585d-4767-84ed-13fe3b934c8d/backups" \
   -u '{API_KEY}:{API SECRET}'`
4. Create a new service _from the backup_ - make sure to note the password in the response, it will only be available once. This should take around 5-10 minutes but relies on GCP:

```shell
curl -X "POST" "https://api.clickhouse.cloud/v1/organizations/8a0d56e3-d8f0-4e70-80bf-a8bf6ee950bd/services" \
     -H 'Content-Type: application/json' \
     -u '{API KEY}:{API SECRET}' \
     -d $'{
  "tier": "production",
  "provider": "gcp",
  "region": "us-central1",
  "name": "restored-product-analytics-TEST", # This should be the same name as the existing service, prefixed with 'restored'.
  "idleScaling": false,
  "backupId": "REPLACE ME" # This is the backup ID from step 3.
}'
```

5. Enable a private connection to the instance using the [self-serve information](https://clickhouse.com/docs/en/manage/security/gcp-private-service-connect#add-endpoint-id-to-services-allow-list).
6. Update the secrets and connection strings in [Vault](https://vault.gitlab.net/) to connect to the new instance. `gitlab-com/gitlab-org/analytics-section/product-analytics/analytics-stack/prd-278964/analytics-stack`
7. Redeploy the latest version of the analytics-stack.
8. Check the following on the [main team dashboard](https://dashboards.gitlab.net/d/da6cf9ea-d593-41ed-91c5-8536fd15c2fa/fe5b2275-5e92-58a0-a397-d2bdf8cd2e18?orgId=1&refresh=5m):
   * Vector is still ingesting data.
   * ClickHouse is still writing new data.
   * No unexpected errors in the configurator logs.
