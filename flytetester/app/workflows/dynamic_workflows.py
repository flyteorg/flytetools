from __future__ import absolute_import
from __future__ import print_function

import time
import os

from flytekit.sdk.tasks import sidecar_task
from flytekit.sdk.workflow import workflow_class
from k8s.io.api.core.v1 import generated_pb2
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class, Input, Output
from flytekit.sdk.tasks import (
    python_task,
    inputs,
    outputs,
)


# Uncachable
@inputs(wf_input=Types.Float, cache_disabled=Types.Boolean)
@outputs(generated=Types.Float)
@python_task
def generate_input(wf_params, wf_input, cache_disabled, generated);
    if cache_disabled:
        generated.set(time.time())
    else:
        generated.set(wf_input)


@outputs(out_ints=[Types.Integer])
@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sample_batch_task_sq(wf_params, caching_input, out_ints):
    res2 = []
    for i in _six_moves.range(0, 3):
        task = sq_sub_task(in1=i)
        yield task
        res2.append(task.outputs.out1)
    out_ints.set(res2)


@inputs(caching_input=Types.Float)
@outputs(out_str=[Types.String], out_ints=[[Types.Integer]])
@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sample_batch_task_cachable(wf_params, caching_input, out_str, out_ints):
    res = ["I'm the first result"]
    for i in _six_moves.range(0, 3):
        task = sub_task(in1=i)
        yield task
        res.append(task.outputs.out1)
        res.append("I'm after each sub-task result")
    res.append("I'm the last result")

    res2 = []
    for i in _six_moves.range(0, 3):
        task = int_sub_task(in1=i)
        yield task
        res2.append(task.outputs.out1)

    # Nested batch tasks
    task = sample_batch_task_sq()
    yield task
    res2.append(task.outputs.out_ints)

    task = sample_batch_task_sq()
    yield task
    res2.append(task.outputs.out_ints)

    out_str.set(res)
    out_ints.set(res2)


@inputs(caching_input=Types.Float, in1=Types.Integer)
@outputs(out1=Types.String)
@python_task(discoverable=True, discovery_version='1.0', cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sub_task(wf_params, caching_input, in1, out1):
    out1.set("hello {}".format(in1))


@inputs(caching_input=Types.Float, in1=Types.Integer)
@outputs(out1=[Types.Integer])
@python_task(discoverable=True, discovery_version='1.0',cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def int_sub_task(wf_params, caching_input, in1, out1):
    out1.set([in1, in1 * 2, in1 * 3])


@inputs(caching_input=Types.Float, in1=Types.Integer)
@outputs(out1=Types.Integer)
@python_task(discoverable=True, discovery_version='1.0',cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sq_sub_task(wf_params, caching_input, in1, out1):
    out1.set(in1 * in1)


@workflow_class
class OptionallyCachableWorkflow(object):
    input_if_cached_enabled = Input(Types.Float, default=10, help="Test float input with default")
    cache_disabled = Input(Types.Boolean, default=False, help="Whether to disable cache.")
    input_generator = generate_input(wf_input=input_if_cached_enabled, cache_disabled=cache_disabled)
    dynamic_task = sample_batch_task_cachable(caching_input=input_generator.out.generated)
