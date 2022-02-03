#!/bin/bash

set -ex


# TODO: Leave this here while we don't have a new flytesnacks release, let's use a release that is not affected by the conditional bug.
# LATEST_VERSION=$(curl --silent "https://api.github.com/repos/flyteorg/flytesnacks/releases/latest" | jq -r .tag_name)
LATEST_VERSION=v0.1.1

flytekit_venv python functional-tests/run-tests.py $LATEST_VERSION P0,P1 functional-tests/functional-test.config core
