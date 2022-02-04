#!/bin/bash

set -ex

LATEST_VERSION=$(curl --silent "https://api.github.com/repos/flyteorg/flytesnacks/releases/latest" | jq -r .tag_name)

flytekit_venv python functional-tests/run-tests.py $LATEST_VERSION P0,P1 functional-tests/functional-test.config core
