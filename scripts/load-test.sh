#!/usr/bin/env bash
# Sends traffic to the API so Grafana panels fill up and the HPA has CPU to react to.
# Usage: URL=http://lostfound.local ./scripts/load-test.sh [requests] [parallel]
set -euo pipefail

URL="${URL:-http://lostfound.local}"
REQUESTS="${1:-2000}"
PARALLEL="${2:-20}"

hit() {
  case $(( $1 % 10 )) in
    0) curl -s -o /dev/null "$URL/api/items/99999" ;;              # a few 404s for the error panel
    1) curl -s -o /dev/null "$URL/api/items/stats" ;;
    2) curl -s -o /dev/null "$URL/api/items?q=library" ;;
    *) curl -s -o /dev/null "$URL/api/items" ;;
  esac
}
export -f hit
export URL

echo "Sending $REQUESTS requests to $URL ($PARALLEL at a time)..."
seq 1 "$REQUESTS" | xargs -P "$PARALLEL" -I{} bash -c 'hit {}'
echo "Load test finished"
