#!/usr/bin/env bash
# sends lots of requests to the api so the grafana panels fill up and the hpa sees cpu use
# how to use it
# set the url variable and run the script
# you can give the number of requests and how many to send at the same time
# stop right away if any command fails
set -euo pipefail

# default values if you do not give your own
URL="${URL:-http://lostfound.local}"
REQUESTS="${1:-2000}"
PARALLEL="${2:-20}"

# send one request and pick the route based on the request number
hit() {
  case $(( $1 % 10 )) in
    # one in ten asks for a missing item to make a few 404 errors for the error panel
    0) curl -s -o /dev/null "$URL/api/items/99999" ;;
    1) curl -s -o /dev/null "$URL/api/items/stats" ;;
    2) curl -s -o /dev/null "$URL/api/items?q=library" ;;
    *) curl -s -o /dev/null "$URL/api/items" ;;
  esac
}
# share the function and the url with the parallel workers
export -f hit
export URL

echo "Sending $REQUESTS requests to $URL ($PARALLEL at a time)..."
# run many requests at the same time
seq 1 "$REQUESTS" | xargs -P "$PARALLEL" -I{} bash -c 'hit {}'
echo "Load test finished"
