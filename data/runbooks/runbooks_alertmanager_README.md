# Alertmanager configuration

We manage our Alertmanager configuration here using jsonnet. The resultant
Kubernetes secret object is uploaded, and is consumed by
[the Prometheus operator deployment](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles/-/tree/master/releases/30-gitlab-monitoring).

The CI jobs for this are run on `ops.gitlab.net` where the variables are configured.
See: https://ops.gitlab.net/gitlab-com/runbooks/-/settings/ci_cd

## Variables

### `ALERTMANAGER_SECRETS_FILE`

Type: File

Value: A jsonnet file, based on the dummy-secrets.jsonnet template.

## CI Jobs

These jobs run in a CI pipeline, view the [.gitlab-ci.yml](../.gitlab-ci.yml) to
determine how this is configured.

To run a manual deploy, you will need a local secrets file with the filename
exported in the `ALERTMANAGER_SECRETS_FILE` variable.

For the production alertmanger, this content is stored in vault at [`
ops-gitlab-net/gitlab-com/runbooks/ops/alertmanager`](https://vault.gitlab.net/ui/vault/secrets/ci/kv/ops-gitlab-net%2Fgitlab-com%2Frunbooks%2Fops%2Falertmanager/details?version=2).

Then run:

```shell
kubectl apply --namespace monitoring --filename k8s_alertmanager_secret.yaml
```

* Generate the `alertmanager.yml` file.
  ```shell
  ./generate.sh
  ```
* Validate the `alertmanager.yml` looks reasonable.
* The contents of this file are visible as a base64 encoded secret, in the
  manifest k8s_alertmanager_secret.yaml.
* When this secret is uploaded to a namespace containing a prometheus operator
  and an Alertmanager CRD (which these days is only the ops GKE cluster's
  monitoring namespace), Alertmanager's config will automatically be updated.
