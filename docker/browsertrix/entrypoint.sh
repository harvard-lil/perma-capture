#!/bin/sh
# see https://docs.docker.com/engine/reference/builder/#entrypoint
set -e

# Initialize the data directory
mkdir -p $DATA_DIR

# Exec the original command
exec su -c "$*"
