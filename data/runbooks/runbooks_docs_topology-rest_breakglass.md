# Breakglass

We follow the [Principle of Least Privilege](https://csrc.nist.gov/glossary/term/least_privilege) whereby SREs don't have default read/write access to Cells infrastructure in GCP.  This helps limit blast radius in case of security
incidents or misconfigurations of running scripts locally to production.  We use [Privileged Access Manager (PAM)][PAM] to provide short lived access to GCP via
the console or `gcloud`.

## Topology Service Access

- Read Only: Get read only access like reading logs.

  ```sh
  gcloud beta pam grants create \
      --entitlement="readonly-entitlement-gitlab-runway-topo-svc-stg" \
      --requested-duration="1800s" \
      --justification="$ENTER_YOUR_JUSTIFICATION" \
      --location=global \
      --project="gitlab-runway-topo-svc-stg"
    ```

  NOTE: For production use `--entitlement="readonly-entitlement-gitlab-runway-topo-svc-prod"`
    and `--project="gitlab-runway-topo-svc-prod"`

  For example, after running this command will be given the requested access to the Topology Service project in the UI.

  - [staging project GCP page](https://console.cloud.google.com/welcome?authuser=0&project=gitlab-runway-topo-svc-stg&supportedpurview=project).
  - [production project GCP page](https://console.cloud.google.com/welcome?authuser=0&project=gitlab-runway-topo-svc-prod&inv=1&invt=AbinMw&supportedpurview=project).

- Read/Write: Get read/write access requiring approval

  ```sh
  gcloud beta pam grants create \
      --entitlement="readwrite-entitlement-gitlab-runway-topo-svc-stg" \
      --requested-duration="1800s" \
      --justification="$ENTER_YOUR_JUSTIFICATION" \
      --location=global \
      --project="gitlab-runway-topo-svc-stg"
  ```

  NOTE: For production use `--entitlement="readwrite-entitlement-gitlab-runway-topo-svc-prod"`
    and `--project="gitlab-runway-topo-svc-prod"`

- Breakglass: Only used by the On-Call Engineer when they need write access with
    no approval to fix a high severity incident

  ```sh
  gcloud beta pam grants create \
      --entitlement="breakglass-entitlement-gitlab-runway-topo-svc-stg" \
      --requested-duration="1800s" \
      --justification="$ENTER_YOUR_JUSTIFICATION" \
      --location=global \
      --project="gitlab-runway-topo-svc-stg"
  ```

  NOTE: For production use `--entitlement="breakglass-entitlement-gitlab-runway-topo-svc-prod"`
    and `--project="gitlab-runway-topo-svc-prod"`

[PAM]: https://cloud.google.com/iam/docs/pam-overview
