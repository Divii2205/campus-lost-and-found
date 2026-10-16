#!/usr/bin/env bash
# Local version of the CI deploy job: build images tagged with the commit SHA,
# load them into the kind cluster and roll them out with Helm.
set -euo pipefail

SHA="$(git rev-parse HEAD)"
CLUSTER="${CLUSTER:-session21}"
BACKEND="ghcr.io/divii2205/lostfound-backend:${SHA}"
FRONTEND="ghcr.io/divii2205/lostfound-frontend:${SHA}"

docker build -t "$BACKEND" backend
docker build -t "$FRONTEND" frontend
kind load docker-image "$BACKEND" "$FRONTEND" --name "$CLUSTER"

kubectl apply -f k8s/namespace.yaml
helm upgrade --install lostfound ./helm/lostfound -n lostfound \
  -f helm/lostfound/values-dev.yaml \
  --set backend.tag="$SHA" --set frontend.tag="$SHA" \
  --wait --timeout 5m

kubectl get pods -n lostfound
