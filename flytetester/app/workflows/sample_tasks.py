from __future__ import absolute_import
from __future__ import print_function

from flytekit.sdk.tasks import inputs, outputs, python_task, dynamic_task, spark_task
from flytekit.sdk.types import Types
from six.moves import range


@inputs(num=Types.Integer)
@outputs(out=Types.Integer)
@python_task(cache_version='1')
def identity_sub_task(wf_params, num, out):
    out.set(num)


@inputs(iterations=Types.Integer)
@outputs(out=[Types.Integer])
@dynamic_task(cache_version='1', cache=False)
def simple_batch_task(wf_params, iterations, out):
    list_of_outputs = []
    for i in range(iterations):
        sub_task = identity_sub_task(num=i)
        list_of_outputs.append(sub_task.outputs.out)
        yield sub_task
    out.set(list_of_outputs)


@inputs(value_to_print=Types.Integer)
@outputs(out=Types.Integer)
@python_task(cache_version='1')
def add_one_and_print(workflow_parameters, value_to_print, out):
    added = value_to_print + 1
    workflow_parameters.logging.info("My printed value: {}".format(added))
    out.set(added)


@inputs(values_to_print=[Types.Integer])
@outputs(out=Types.Integer)
@python_task(cache_version='1')
def sum_non_none(workflow_parameters, values_to_print, out):
    added = 0
    for value in values_to_print:
        workflow_parameters.logging.info("Adding values: {}".format(value))
        if value is not None:
            added += value
    added += 1
    workflow_parameters.logging.info("My printed value: {}".format(added))
    out.set(added)


@inputs(values_to_add=[Types.Integer])
@outputs(out=Types.Integer)
@python_task(cache_version='1')
def sum_and_print(workflow_parameters, values_to_add, out):
    summed = sum(values_to_add)
    workflow_parameters.logging.info("Summed up to: {}".format(summed))
    out.set(summed)


@inputs(value_to_print=Types.Integer, date_triggered=Types.Datetime)
@python_task(cache_version='1', cache=False)
def print_every_time(workflow_parameters, value_to_print, date_triggered):
    workflow_parameters.logging.info(
        "My printed value: {} triggered on: {}".format(value_to_print, date_triggered))


@inputs(value_to_print=Types.Integer)
@python_task(cache_version='1', cache=False)
def print_int(wf_params, value_to_print):
    wf_params.logging.info("Value: {}".format(value_to_print))
