#!/usr/bin/env bash
# List unique container image registries referenced by Pods in the cluster.
set -euo pipefail

# Collect image references from all Pods
kubectl get pods --all-namespaces -o jsonpath="{.items[*].spec.containers[*].image}" \
  | tr -s '[[:space:]]' '\n' \
  | sort -u \
  > /tmp/k8s-images.txt

# Extract unique registry hosts (before first '/')
awk -F/ '{print $1}' /tmp/k8s-images.txt | sort -u

echo "Wrote image list to /tmp/k8s-images.txt"
