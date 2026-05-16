# Product Analytics Kubernetes Architecture

This document outlines how the product analytics stack is deployed and managed internally for GitLab's customers.

## Analytics Deployment Locations

Product Analytics is hosted in the following GKE clusters:

- **pre-gitlab-gke** (Development)
- **gstg-gitlab-gke** (Staging) - *Note: Not yet deployed*
- **gprd-gitlab-gke** (Production) - *Note: Not yet deployed*

All clusters are accessible via the [GCP Console](https://console.cloud.google.com).

For direct Kubernetes API access to the clusters, follow this [guide on setting up direct access](https://gitlab.com/gitlab-com/runbooks/-/blob/master/docs/kube/k8s-oncall-setup.md#kubernetes-api-access).

## How to Update the Analytics-Stack Deployment Chart

### Modifying the Chart Values

The product analytics chart is deployed to GKE via the `gitlab-helmfiles` repository, which can be found [here](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles).

The analytics-stack chart values file is located in the same repository [here](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles/-/tree/master/releases/analytics?ref_type=heads).

### Upgrading the Chart Version

To update the Helm chart version used by the `gitlab-helmfiles` repository, modify the chart version [here](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles/-/blob/master/bases/environments/pre.yaml?ref_type=heads#L12).

Before merging or updating the chart, ensure that the release has been published in the public analytics-stack repository, which can be found [here](https://gitlab.com/gitlab-org/analytics-section/product-analytics/helm-charts/-/releases).

### Update Analytics Vault Secrets

The product analytics chart uses GitLab's Vault External Secrets provider to ensure that no confidential values are publicly available.

All analytics values can be modified using the Vault UI or programmatically with Vault credentials. An example of the `pre-gitlab-gke` Vault values can be found [here](https://vault.gitlab.net/ui/vault/secrets/k8s/kv/list/pre-gitlab-gke/analytics/). Once the values have been added to your Vault, you can add/edit the `values.yaml.gotmpl` [file](https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles/-/blob/master/releases/analytics/values-secrets/values.yaml.gotmpl?ref_type=heads). Once deployed, the external-secrets operator will ensure that the secret exists in the desired namespace for your deployment.
