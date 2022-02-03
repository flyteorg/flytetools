#!/bin/bash

set -ex

LATEST_VERSION=$(curl --silent "https://api.github.com/repos/flyteorg/flytesnacks/releases/latest" | jq -r .tag_name)

# TODO: Leave this here while we don't have a new flytesnacks release, let's use a release that is not affected by the conditional bug.
LATEST_VERSION=v0.3.27

# We register the workflows here to avoid a race condition between registering the latest version of flytesnacks and the execution of the functional tests.
# flytectl register examples -p flytesnacks -d development --version $LATEST_VERSION

flytekit_venv python functional-tests/run-tests.py $LATEST_VERSION P0,P1 functional-tests/functional-test.config core
