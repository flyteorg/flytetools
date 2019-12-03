#!/usr/bin/env python

import time

import six
from flyteidl.core.errors_pb2 import ErrorDocument
from flyteidl.core.literals_pb2 import LiteralMap
from flytekit.clients import helpers as _helpers
from flytekit.clients.friendly import SynchronousFlyteClient
from flytekit.clis.sdk_in_container.pyflyte import update_configuration_file
from flytekit.common.core.identifier import WorkflowExecutionIdentifier as _WorkflowExecutionIdentifier
from flytekit.common.utils import load_proto_from_file
from flytekit.configuration.platform import URL, INSECURE
from flytekit.interfaces.data.s3.s3proxy import AwsS3Proxy
from flytekit.models.literals import LiteralMap as SdkLiteralMap
from flytekit.models.core.execution import WorkflowExecutionPhase as _WorkflowExecutionPhase

PROJECT = 'flytetester'
DOMAIN = 'development'

# These are the names of the launch plans (workflows) kicked off in the run.sh script
# This is what we'll be looking for in Admin.
EXPECTED_EXECUTIONS = [
    'app.workflows.failing_workflows.DivideByZeroWf',
    'app.workflows.work.WorkflowWithIO',
    'app.workflows.failing_workflows.RetrysWf',
]

# This tells Python where admin is, and also to hit Minio instead of the real S3
update_configuration_file('end2end/end2end.config')
client = SynchronousFlyteClient(URL.get(), insecure=INSECURE.get())

# For every workflow that we test on in run.sh, have a function that can validate the execution response
# It will be supplied an execution object, a node execution list, and a task execution list
# Should return
#  - True, if the execution has completed and everything checks out
#  - False, if things have failed for whatever reason, either the execution failed, or the outputs are wrong, whatever
#  - None, if things aren't complete yet
def workflow_with_io_validator(execution, node_execution_list, task_execution_list):
    """
    Validation logic for app.workflows.work.WorkflowWithIO
    :param flytekit.models.execution.Execution execution:
    :param list[flytekit.models.node_execution.NodeExecution] node_execution_list:
    :param list[flytekit.models.admin.task_execution.TaskExecution] task_execution_list:
    :rtype: option[bool]
    """
    phase = execution.closure.phase
    if not phase == _WorkflowExecutionPhase.SUCCEEDED:
        # If not succeeded, either come back later, or see if it failed
        if phase == _WorkflowExecutionPhase.ABORTED or phase == _WorkflowExecutionPhase.FAILED or \
                phase == _WorkflowExecutionPhase.TIMED_OUT:
            return False
        else:
            return None  # come back and check later

    # Only come to this logic if we are in the succeeded state.

    # Verify that the inputs are correct
    # b = execution.spec.inputs.literals.get('b')
    # assert b.scalar.primitive.string_value == 'hello_world'
    #
    # a = execution.spec.inputs.literals.get('a')
    # assert a.scalar.primitive.integer == 10

    # Check node executions
    assert len(node_execution_list) == 3  # one task, plus start/end nodes
    ne = node_execution_list
    task_node = None
    for n in ne:
        if n.id.node_id == 'odd-nums-task':
            task_node = n
    assert task_node is not None

    # Get the output from Minio into the workflow container
    # output_path = task_node.closure.output_uri
    # assert output_path != ''
    # tmp_file_name = '/tmp/output-{}'.format(execution.id.name)
    # proxy = AwsS3Proxy()
    # proxy.download(output_path, tmp_file_name)
    # x = load_proto_from_file(LiteralMap, tmp_file_name)
    # output_map = SdkLiteralMap.from_flyte_idl(x)
    # str_output = output_map.literals['altered_string']
    # assert str_output.scalar.primitive.string_value == 'hello_world_changed'

    assert len(task_execution_list) > 0

    print('Done validating app-workflows-work-workflow-with-i-o!')

    return True


def failing_workflows_divide_by_zero_wf_validator(execution, node_execution_list, task_execution_list):
    """
    Validation logic for app.workflows.failing_workflows.DivideByZeroWf
    This workflow should always fail.

    :param flytekit.models.execution.Execution execution:
    :param list[flytekit.models.node_execution.NodeExecution] node_execution_list:
    :param list[flytekit.models.admin.task_execution.TaskExecution] task_execution_list:
    :rtype: option[bool]
    """
    phase = execution.closure.phase
    if not phase == _WorkflowExecutionPhase.FAILED:
        # If not failed, fail the test if the execution is in an unacceptable state
        if phase == _WorkflowExecutionPhase.ABORTED or phase == _WorkflowExecutionPhase.SUCCEEDED or \
                phase == _WorkflowExecutionPhase.TIMED_OUT:
            return False
        else:
            return None  # come back and check later

    # Check node executions
    assert len(node_execution_list) == 2  # one task, plus start
    ne = node_execution_list
    node_execution = None
    for n in ne:
        if n.id.node_id == 'div-by-zero':
            node_execution = n
    assert node_execution is not None

    assert len(task_execution_list) > 0

    # Download the error document and make sure it contains what we think it should contain
    error_message = node_execution.closure.error.message
    assert 'division by zero' in error_message

    print('Done validating app-workflows-failing-workflows-divide-by-zero-wf!')
    return True


def retrys_wf_validator(execution, node_execution_list, task_execution_list):
    """
    Validation logic for app.workflows.failing_workflows.RetrysWf
    This workflow should always fail, but should run a total of three times, since the task has two retries

    :param flytekit.models.execution.Execution execution:
    :param list[flytekit.models.node_execution.NodeExecution] node_execution_list:
    :param list[flytekit.models.admin.task_execution.TaskExecution] task_execution_list:
    :rtype: option[bool]
    """
    phase = execution.closure.phase
    if not phase == _WorkflowExecutionPhase.FAILED:
        # If not failed, fail the test if the execution is in an unacceptable state
        if phase == _WorkflowExecutionPhase.ABORTED or phase == _WorkflowExecutionPhase.SUCCEEDED or \
                phase == _WorkflowExecutionPhase.TIMED_OUT:
            return False
        else:
            return None  # come back and check later

    assert len(task_execution_list) == 3
    print('Done validating app-workflows-failing-workflows-retrys-wf!')
    return True


validators = {
    'app.workflows.work.WorkflowWithIO': workflow_with_io_validator,
    'app.workflows.failing_workflows.DivideByZeroWf': failing_workflows_divide_by_zero_wf_validator,
    'app.workflows.failing_workflows.RetrysWf': retrys_wf_validator,
}


def process_executions(execution_names):
    """
    This is the main loop of the end to end test.  Basically it's an infinite loop, that only exits if everything
    has finished (either successfully or unsuccessfully), pausing for five seconds at a time.

    For each execution in the list of expected executions given in the input, it will query the Admin service for
    the execution object, all node executions, and all task executions, and hand these objects off to the validator
    function for the respective workflow.

    :param dict[Text, Text] execution_names: map of lp names to execution name
    """
    succeeded = set()
    failed = set()
    while True:
        if len(succeeded) + len(failed) == len(EXPECTED_EXECUTIONS):
            print('All done verifying...')
            break

        for lp_name, execution_name in six.iteritems(execution_names):
            if lp_name in succeeded or lp_name in failed:
                continue

            # Get an updated execution object
            workflow_execution_id = _WorkflowExecutionIdentifier(project=PROJECT, domain=DOMAIN, name=execution_name)
            execution_object = client.get_execution(workflow_execution_id)

            # Get updated list of all the node executions for it
            node_executions = []
            for ne in _helpers.iterate_node_executions(client, workflow_execution_id):
                node_executions.append(ne)

            # Get an updated list of all task executions
            task_executions = []
            for n in node_executions:
                for te in _helpers.iterate_task_executions(client, n.id):
                    task_executions.append(te)

            # Send response to the appropriate handler
            result = validators[lp_name](execution_object, node_executions, task_executions)
            if result is None:
                print('LP {} with execution {} still not ready...'.format(lp_name, execution_name))
            elif result:
                print('Adding {} to succeeded'.format(lp_name))
                succeeded.add(lp_name)
            else:
                print('Adding {} to failed'.format(lp_name))
                failed.add(lp_name)

        # This python script will hang forever for now - relies on the timeout implemented in the bash script to exit
        # in the failure case
        print('Sleeping...')
        time.sleep(5)

    if len(failed) > 0:
        print('Some tests failed :(')
        exit(1)
    print('All tests passed!')
    exit(0)


def get_executions():
    """
    Retrieve all relevant executions from Admin
    :rtype: list[flytekit.models.execution.Execution]
    """
    resp = client.list_executions_paginated(PROJECT, DOMAIN, filters=[])
    # The executions returned should correspond to the workflows launched in run.sh
    assert len(resp[0]) == len(EXPECTED_EXECUTIONS)
    # pagination token should be an empty string, since we're running from an empty database, and we don't kick
    # off that many executions in an end-to-end test.
    assert resp[1] == ''
    return resp[0]


def pair_lp_names_with_execution_ids(lp_names, executions):
    """
    :param list[Text] lp_names:
    :param list[flytekit.models.execution.Execution] executions:
    :rtype: dict[Text, Text]
    """
    r = {}
    for lp in lp_names:
        for e in executions:
            if e.spec.launch_plan.name == lp:
                r[lp] = e.id.name  # the name of the execution identifier, like ff8b30386aafa4daba79
        assert lp in r
        assert r[lp] != ''

    return r


def validate_endtoend_test():
    # The test should have been kicked off an an execution

    # Get execution objects from Admin
    executions = get_executions()

    # For each execution, find the execution id associated with that launch plan/workflow name
    execution_names = pair_lp_names_with_execution_ids(EXPECTED_EXECUTIONS, executions)

    process_executions(execution_names)


if __name__ == '__main__':
    validate_endtoend_test()
