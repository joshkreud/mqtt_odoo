#!/usr/bin/env bash
# Prepare things for the workspace

set -e

if [ ! -f .devcontainer/.env ]; then
    echo "==> Copying .devcontainer/.env.sample --> Please ensure correct config"
    cp .devcontainer/.env.sample .devcontainer/.env
fi

source .devcontainer/.env

TRAEFIK_NET=$(docker network ls --format="{{lower .Name}}" | grep traefik )
if [ -z "$TRAEFIK_NET" ]; then
  echo "=x Missing Traefik docker network."
  echo "=x Make sure traefik container is running and attached to network named 'traefik'"
  exit 1
fi
