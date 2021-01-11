#!/bin/bash

set -ex

# Create the project name since this is not one of the defaults
flytekit_venv flyte-cli -h flyteadmin:81 --insecure register-project -n flytetester --identifier flytetester -d "test_project" || true

### Need to get Flyte Admin to cluster sync this so that k8s resources are actually created ###
# Currently, kill the admin pod, so that the init container sync picks up the change.

# First register everything, but make sure to use local Dockernetes admin
flytekit_venv pyflyte -c end2end/end2end.config register -p flytetester -d development workflows

# Kick off workflows
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.work.WorkflowWithIO --b hello_world
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.DivideByZeroWf
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.RetrysWf
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.FailingDynamicNodeWF
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.RunToCompletionWF

# Make sure workflow does everything correctly
flytekit_venv python end2end/validator.py
