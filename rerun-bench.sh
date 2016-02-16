#!/bin/bash

export _JAVA_OPTIONS="-Xms4g -Xmx4g"
export CRATE_HEAP_SIZE=10g
export CRATE_TESTS_SQL_REQUEST_TIMEOUT="600" # 10 minutes
ulimit -a

BUILDS=$(curl -s https://cdn.crate.io/downloads/releases/nightly/ | grep "crate-*" | awk  -F '[<>]' '/<a / { print $3 } ')
for BUILD in $BUILDS; do
  CRATE_URL="https://cdn.crate.io/downloads/releases/nightly/$BUILD"
  rm -rf parts
  echo "start stresstest with: $CRATE_URL"
  ./gradlew -s --console=plain --daemon bench \
    -Dcrate.testing.from_url=$CRATE_URL \
    -Djub.consumers=CONSOLE,CRATE \
    -Djub.crate.host=crate1,crate2,crate3 \
    -Djub.crate.http=4200 \
    -Djub.crate.transport=4300
done
