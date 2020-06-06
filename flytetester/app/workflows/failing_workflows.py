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

@outputs(answer=Types.Integer)
@python_task
def divider(wf_params, answer):
    answer.set(1 / 0)


@workflow_class
class DivideByZeroWf(object):
    div_by_zero = divider()


@outputs(answer=Types.Integer)
@python_task(timeout=timedelta(1))
def oversleeper(wf_params, answer):
    time.sleep(10)
    answer.set(1)


@workflow_class
class SleeperWf(object):
    zzz = oversleeper()


@python_task(retries=2)
def retryer(wf_params):
    raise FlyteRecoverableException('This task is supposed to fail')


@workflow_class
class RetrysWf(object):
    retried_task = retryer()


@dynamic_task(retries=2)
def retryable_dynamic_node(wf_params):
    yield divider()


@workflow_class
class FailingDynamicNodeWF(object):
    should_fail_and_retry = retryable_dynamic_node()
