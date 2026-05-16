These helper scripts facilitate running ad-hoc observations locally on a GKE node.

The goal is to support using some general-purpose Linux observability tools
in the context of a kubernetes node in the GKE platform, letting those tools
operate on the scope of a specific target process, container, pod, or the whole host.

Supporting documentation:
[Ad hoc observability tools on Kubernetes nodes](../../docs/kube/k8s-adhoc-observability.md)

The above docs include:
* CPU profiling, packet captures, `pidstat` usage, and other general-purpose Linux observability tools/techniques
* Tips and demos for using these observability tools in GKE
* Special considerations for interpreting results in the context of container isolation and resource usage limits
