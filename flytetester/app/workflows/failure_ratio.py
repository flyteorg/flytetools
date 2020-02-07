from __future__ import absolute_import
from __future__ import print_function

from flytekit.common.exceptions.base import FlyteRecoverableException
from flytekit.common.types.containers import List
from flytekit.sdk.tasks import (
    dynamic_task,
    python_task, inputs, outputs)
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class, Output


@outputs(out_int=Types.Integer)
@inputs(idx=Types.Integer)
@python_task
def fail_if_4_5(wf_params, idx, out_int):
    if idx == 4 or idx == 5:
        wf_params.logging.info("This task will fail")
        raise FlyteRecoverableException('This task is supposed to fail')

    wf_params.logging.info("This task should succeed")
    out_int.set(idx)


@outputs(out_ints=[Types.Integer])
@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi", retries=2,
              allowed_failure_ratio=0.3)
def failure_ratio_task_gen(wf_params, out_ints):
    res = []
    for i in range(0, 10):
        t = fail_if_4_5(idx=i)
        yield t
        res.append(t.outputs.out_int)

    out_ints.set(res)


@workflow_class
class FailureRatioWorkflow(object):
    dynamic_task = failure_ratio_task_gen()

    out_ints = Output(dynamic_task.outputs.out_ints, List(Types.Integer), help="The output ints.")
