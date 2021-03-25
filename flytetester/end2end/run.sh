#!/bin/bash

set -ex

# Create the project name since this is not one of the defaults
flytekit_venv flyte-cli -h flyteadmin:81 --insecure register-project -n flytetester --identifier flytetester -d "test_project" || true

### Need to get Flyte Admin to cluster sync this so that k8s resources are actually created ###
# Currently, kill the admin pod, so that the init container sync picks up the change.

# First register everything, but make sure to use local Dockernetes admin
flytekit_venv pyflyte -c end2end/end2end.config register -p flytetester -d development workflows

# Kick off workflows
# This one needs an input, which is easier to do programmatically using flytekit
flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.work.WorkflowWithIO --b hello_world

# Quick shortcut to get at the version
arrIN=(${FLYTE_INTERNAL_IMAGE//:/ })
VERSION=${arrIN[1]}

#flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.DivideByZeroWf
flytectl --config /opt/go/config.yaml get launchplan -p flytetester -d development app.workflows.failing_workflows.RetrysWf --version ${VERSION} --execFile DivideByZeroWf.yaml
flytectl --config /opt/go/config.yaml create execution --execFile DivideByZeroWf.yaml -p flytetester -d development

#flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.RetrysWf
flytectl --config /opt/go/config.yaml get launchplan -p flytetester -d development app.workflows.failing_workflows.RetrysWf --version ${VERSION} --execFile Retrys.yaml
flytectl --config /opt/go/config.yaml create execution --execFile Retrys.yaml -p flytetester -d development

#flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.FailingDynamicNodeWF
flytectl --config /opt/go/config.yaml get launchplan -p flytetester -d development app.workflows.failing_workflows.RetrysWf --version ${VERSION} --execFile FailingDynamicNodeWF.yaml
flytectl --config /opt/go/config.yaml create execution --execFile FailingDynamicNodeWF.yaml -p flytetester -d development

#flytekit_venv pyflyte -c end2end/end2end.config lp -p flytetester -d development execute app.workflows.failing_workflows.RunToCompletionWF
flytectl --config /opt/go/config.yaml get launchplan -p flytetester -d development app.workflows.failing_workflows.RetrysWf --version ${VERSION} --execFile RunToCompletionWF.yaml
flytectl --config /opt/go/config.yaml create execution --execFile RunToCompletionWF.yaml -p flytetester -d development

# Make sure workflow does everything correctly
flytekit_venv python end2end/validator.py
