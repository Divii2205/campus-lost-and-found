#!/usr/bin/env bash
# the gitops version of deploy-local.sh
# it builds images tagged with the commit sha and loads them into the kind cluster
# then it writes the sha into values-gitops.yaml
# argocd deploys it after you commit and push that file
# the images are built on the laptop because the ci images are for amd64
# and kind on an apple silicon mac runs arm64
# stop right away if any command fails
set -euo pipefail

# use the current commit id as the image tag
SHA="$(git rev-parse HEAD)"
CLUSTER="${CLUSTER:-session21}"
BACKEND="ghcr.io/divii2205/lostfound-backend:${SHA}"
FRONTEND="ghcr.io/divii2205/lostfound-frontend:${SHA}"
VALUES="helm/lostfound/values-gitops.yaml"

# build both images and copy them into the kind cluster
docker build -t "$BACKEND" backend
docker build -t "$FRONTEND" frontend
kind load docker-image "$BACKEND" "$FRONTEND" --name "$CLUSTER"

# put the new sha into the gitops values file
sed -i.bak -E "s/tag: \"[0-9a-f]*\"/tag: \"${SHA}\"/" "$VALUES"
rm -f "${VALUES}.bak"

# show what changed and what to do next
git diff -- "$VALUES"
echo "Next: git commit -am \"Deploy ${SHA:0:7} with ArgoCD\" && git push"
