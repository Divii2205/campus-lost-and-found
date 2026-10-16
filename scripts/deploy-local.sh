#!/usr/bin/env bash
# the local version of the ci deploy job
# it builds images tagged with the commit sha and loads them into the kind cluster
# then it rolls them out with helm
# stop right away if any command fails
set -euo pipefail

# use the current commit id as the image tag
SHA="$(git rev-parse HEAD)"
CLUSTER="${CLUSTER:-session21}"
BACKEND="ghcr.io/divii2205/lostfound-backend:${SHA}"
FRONTEND="ghcr.io/divii2205/lostfound-frontend:${SHA}"

# build both images and copy them into the kind cluster
docker build -t "$BACKEND" backend
docker build -t "$FRONTEND" frontend
kind load docker-image "$BACKEND" "$FRONTEND" --name "$CLUSTER"

# make the namespace and then install or upgrade the app with helm
kubectl apply -f k8s/namespace.yaml
helm upgrade --install lostfound ./helm/lostfound -n lostfound \
  -f helm/lostfound/values-dev.yaml \
  --set backend.tag="$SHA" --set frontend.tag="$SHA" \
  --wait --timeout 5m

# show the running pods
kubectl get pods -n lostfound
