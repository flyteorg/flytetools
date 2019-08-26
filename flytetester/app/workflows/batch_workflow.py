from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flytekit.sdk.tasks import python_task, inputs, outputs, dynamic_task
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class, Output
from six import moves as _six_moves

from app.workflows.sample_tasks import simple_batch_task


@outputs(out_ints=[Types.Integer])
@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sample_batch_task_sq(wf_params, out_ints):
    res2 = []
    for i in _six_moves.range(0, 3):
        task = sq_sub_task(in1=i)
        yield task
        res2.append(task.outputs.out1)
    out_ints.set(res2)


@outputs(out_str=[Types.String], out_ints=[[Types.Integer]])
@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sample_batch_task_no_inputs(wf_params, out_str, out_ints):
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


@inputs(in1=Types.Integer)
@outputs(out1=Types.String)
@python_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sub_task(wf_params, in1, out1):
    out1.set("hello {}".format(in1))


@inputs(in1=Types.Integer)
@outputs(out1=[Types.Integer])
@python_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def int_sub_task(wf_params, in1, out1):
    out1.set([in1, in1 * 2, in1 * 3])


@inputs(in1=Types.Integer)
@outputs(out1=Types.Integer)
@python_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def sq_sub_task(wf_params, in1, out1):
    out1.set(in1 * in1)


@inputs(ints_to_print=[[Types.Integer]], strings_to_print=[Types.String])
@python_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi")
def print_every_time(workflow_parameters, ints_to_print, strings_to_print):
    print("Int values: {}".format(ints_to_print))
    print("String values: {}".format(strings_to_print))


@workflow_class
class BatchTasksWorkflow(object):
    batch_task = sample_batch_task_no_inputs()
    py_task = print_every_time(ints_to_print=batch_task.outputs.out_ints, strings_to_print=batch_task.outputs.out_str)
    ints = Output(batch_task.outputs.out_ints, sdk_type=[[Types.Integer]])
    strs = Output(batch_task.outputs.out_str, sdk_type=[Types.String])


@workflow_class
class SimpleBatchWorkflow(object):
    simple = simple_batch_task(iterations=5)
