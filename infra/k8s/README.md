# Kubernetes starter

Build and publish the project image, replace `ghcr.io/REPLACE_OWNER/fleetguard-api:REPLACE_TAG`, then create namespace and secret values out of band:

```sh
kubectl apply -f infra/k8s/namespace.yaml
kubectl -n fleetguard create secret generic fleetguard-secrets \
  --from-literal=POSTGRES_DSN='...' --from-literal=JWT_SECRET='...' \
  --from-literal=DEMO_PASSWORD='...'
kubectl apply -f infra/k8s/config.yaml -f infra/k8s/web.yaml
```

Provide PostgreSQL, Redpanda/Kafka, ClickHouse and Redis endpoints, network policies, TLS ingress, external secrets, persistence, PodDisruptionBudgets, broker partition settings and metrics adapter before using this in a production cluster. The manifests are a starter, not a complete managed data-plane installation.
