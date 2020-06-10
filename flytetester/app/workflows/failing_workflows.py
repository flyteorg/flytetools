from __future__ import absolute_import
from __future__ import print_function

import time
from datetime import timedelta

from flytekit.sdk.tasks import (
    python_task,
    dynamic_task,
    outputs,
)
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class
from flytekit.common.exceptions.base import FlyteRecoverableException
from flytekit.models.core.workflow import WorkflowMetadata

@outputs(answer=Types.Integer)
@python_task(cpu_request="40m")
def divider(wf_params, answer):
    answer.set(1 / 0)


@workflow_class
class DivideByZeroWf(object):
    div_by_zero = divider()


@outputs(answer=Types.Integer)
@python_task(timeout=timedelta(1), cpu_request="10m")
def oversleeper(wf_params, answer):
    time.sleep(10)
    answer.set(1)


@workflow_class
class SleeperWf(object):
    zzz = oversleeper()


@python_task(retries=2, cpu_request="20m")
def retryer(wf_params):
    raise FlyteRecoverableException('This task is supposed to fail')


@workflow_class
class RetrysWf(object):
    retried_task = retryer()


@dynamic_task(retries=2, cpu_request="40m")
def retryable_dynamic_node(wf_params):
    yield divider()


@inputs(in_str=Types.String)
@python_task()
def echo(wf_params, in_str):
    wf_params.logging.warn(in_str)


@workflow_class
class FailingDynamicNodeWF(object):
    should_fail_and_retry = retryable_dynamic_node()


@workflow_class(on_failure=WorkflowMetadata.OnFailurePolicy.FAIL_AFTER_EXECUTABLE_NODES_COMPLETE)
class RunToCompletionWF(object):
    div_by_zero = divider()
    echo_n = echo(in_str="should never run")

    echo_n_2 = echo(in_str="should run first")
    echo_n_2_2 = echo(in_str="should run next")
    div_by_zero_2 = divider()

    echo_n_2 >> echo_n_2_2 >> div_by_zero_2
    div_by_zero >> echo_n
