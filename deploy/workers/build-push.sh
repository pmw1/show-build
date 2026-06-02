#!/usr/bin/env bash
# build-push.sh — build all worker flavors, tag with git SHA + 'latest', push to
# the Gitea container registry. Run from the repo root on any dev box with docker.
# DRAFT (worker-multi-image). Requires: `docker login 192.168.51.206:3000` once.
#
# Usage:
#   deploy/workers/build-push.sh [flavor ...]      # default: all flavors
#   FLAVORS="media-gpu" deploy/workers/build-push.sh
set -euo pipefail

REGISTRY="${REGISTRY:-192.168.51.206:3000/showbuild}"
SHA="$(git rev-parse --short HEAD)"
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"

declare -A DOCKERFILE=(
  [base]="$DIR/worker.base.Dockerfile"
  [media-cpu]="$DIR/worker.media-cpu.Dockerfile"
  [media-gpu]="$DIR/worker.media-gpu.Dockerfile"
)
declare -A IMAGE=(
  [base]="worker-base"
  [media-cpu]="worker-media-cpu"
  [media-gpu]="worker-media-gpu"
)

FLAVORS_TO_BUILD=("${@:-}")
[ -z "${FLAVORS_TO_BUILD[*]}" ] && FLAVORS_TO_BUILD=(${FLAVORS:-base media-cpu media-gpu})

cd "$ROOT"
for f in "${FLAVORS_TO_BUILD[@]}"; do
  df="${DOCKERFILE[$f]:-}"; img="${IMAGE[$f]:-}"
  [ -z "$df" ] && { echo "unknown flavor: $f" >&2; exit 2; }
  ref_sha="$REGISTRY/$img:$SHA"
  ref_latest="$REGISTRY/$img:latest"
  echo ">>> building $f -> $ref_sha"
  docker build -f "$df" -t "$ref_sha" -t "$ref_latest" .
  echo ">>> pushing $ref_sha + :latest"
  docker push "$ref_sha"
  docker push "$ref_latest"
done

echo "done. SHA=$SHA flavors=${FLAVORS_TO_BUILD[*]}"
echo "hosts auto-pull :latest (Watchtower/cron) -> fleet self-upgrades."
