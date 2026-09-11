# Optional addons (not installed by default)

Helm values for addons that were commented out in the former `40_install_others` role.
Copy to a new install role when enabling:

| File | Chart | Suggested role name |
|------|-------|---------------------|
| `templates/graylog.yaml.j2` | kong-z/graylog | `install_graylog` |
| `templates/trivy.yaml.j2` | aquasecurity/trivy-operator | `install_trivy` |
| `kubevious.yaml` | kubevious/kubevious | `install_kubevious` |
| `cost-analyzer.yaml` | kubecost/cost-analyzer | `install_kubecost` |
| `kafka-ui.yaml` | kafka-ui/kafka-ui | `install_kafka_ui` |
| `metrics-server.yaml` | metrics-server | `install_metrics_server` |
