from __future__ import absolute_import

from flytekit.common.notifications import PagerDuty
from flytekit.common.schedules import CronSchedule
from flytekit.common.types.primitives import String, Integer, Boolean
from flytekit.models.core.execution import WorkflowExecutionPhase
from flytekit.sdk.tasks import (
    python_task,
    inputs,
    outputs,
)
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class, Input, Output

PAGE_ON_FAILURE_IN_PRODUCTION = PagerDuty(
    phases=[WorkflowExecutionPhase.FAILED, WorkflowExecutionPhase.TIMED_OUT],
    recipients_email=["testservice-low-urgency@lyft.pagerduty.com"],
)

TEST_CRON_SCHEDULE = CronSchedule("0/15 * * * ? *")


@inputs(list_of_nums=[Types.Integer])
@outputs(are_num_odd=[Types.Boolean])
@python_task(cache_version='1')
def find_odd_numbers(wf_params, list_of_nums, are_num_odd):
    if wf_params and wf_params.logging:
        wf_params.logging.info("Running find_odd_nums python task")
    output_list = []
    for num in list_of_nums:
        b = num % 2 == 1
        output_list.append(b)
        if wf_params and wf_params.logging:
            wf_params.logging.info("Number {} is odd? {}".format(num, b))
    are_num_odd.set(output_list)


@workflow_class()
class OnePythonTaskWF(object):
    odd_nums_task = find_odd_numbers(list_of_nums=[2, 3, 4, 7])
    task_output = odd_nums_task.outputs.are_num_odd


onePythonTaskLP = OnePythonTaskWF.create_launch_plan(schedule=TEST_CRON_SCHEDULE,
                                                     notifications=[PAGE_ON_FAILURE_IN_PRODUCTION])


@inputs(list_of_nums=[Types.Integer], demo_string=Types.String)
@outputs(are_num_odd=[Types.Boolean], altered_string=Types.String)
@python_task(cache_version='1')
def find_odd_numbers_with_string(wf_params, list_of_nums, demo_string, are_num_odd, altered_string):
    if wf_params and wf_params.logging:
        wf_params.logging.info("Running find_odd_nums python task")
    output_list = []
    for num in list_of_nums:
        b = num % 2 == 1
        output_list.append(b)
        if wf_params and wf_params.logging:
            wf_params.logging.info("Number {} is odd? {}".format(num, b))
    are_num_odd.set(output_list)
    altered_string.set(demo_string + '_changed')


@workflow_class()
class WorkflowWithIO(object):
    a = Input(Types.Integer, default=10, help="Test integer input with default")
    b = Input(Types.String, required=True, help="Test string with no default")
    odd_nums_task = find_odd_numbers_with_string(list_of_nums=[2, 3, 4, 7], demo_string=b)
    task_output = Output(odd_nums_task.outputs.are_num_odd, sdk_type=[Boolean])
    output_a = Output(a, sdk_type=Integer)  # pass through output
    output_b = Output(odd_nums_task.outputs.altered_string, sdk_type=String)
