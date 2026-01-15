#!/usr/bin/env bash
# Stop and remove containers, networks, and volumes for a clean reset.
set -euo pipefail

docker compose down -v
