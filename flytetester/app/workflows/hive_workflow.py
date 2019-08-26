from __future__ import absolute_import
from __future__ import print_function

import six as _six
from flytekit.common.types.impl.schema import Schema
from flytekit.sdk.tasks import python_task, inputs, outputs, dynamic_task
from flytekit.sdk.tasks import qubole_hive_task
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class


@outputs(hive_results=[Types.Schema()])
@qubole_hive_task(tags=[_six.text_type('these'), _six.text_type('are'), _six.text_type('tags')])
def generate_queries(wf_params, hive_results):
    q1 = "SELECT 1"
    q2 = "SELECT 'two'"
    schema_1, formatted_query_1 = Schema.create_from_hive_query(select_query=q1)
    schema_2, formatted_query_2 = Schema.create_from_hive_query(select_query=q2)

    hive_results.set([schema_1, schema_2])
    return [formatted_query_1, formatted_query_2]


@inputs(ss=[Types.Schema()])
@python_task
def print_schemas(wf_params, ss):
    for s in ss:
        with s as r:
            for c in r.iter_chunks():
                print(c)
                print(type(c))


@workflow_class
class ExampleQueryWorkflow(object):
    a = generate_queries()
    b = print_schemas(ss=a.outputs.hive_results)


@outputs(hive_results=[Types.Schema()])
@qubole_hive_task(cache=True, cache_version='1', tags=['flyteexamples', 'will_be_cached'])
def get_queries_cached(wf_params, hive_results):
    q1 = "SELECT 1 + 15 AS col_a"
    q2 = "SELECT CONCAT_WS(' ', 'hello', 'world') as col_b"
    schema_1, formatted_query_1 = Schema.create_from_hive_query(select_query=q1)
    schema_2, formatted_query_2 = Schema.create_from_hive_query(select_query=q2)

    hive_results.set([schema_1, schema_2])
    return [formatted_query_1, formatted_query_2]


@workflow_class
class ExampleCachedQueriesWorkflow(object):
    generate_and_run = get_queries_cached()
    output_printer = print_schemas(ss=generate_and_run.outputs.hive_results)


@inputs(query_num=Types.Integer)
@outputs(hive_result=Types.Schema())
@qubole_hive_task(tags=['flyteexamples', 'will_not_be_cached'])
def get_uncached_query_for_dynamic(wf_params, query_num, hive_result):
    q1 = "SELECT 1 + 15 AS col_a"
    q2 = "SELECT CONCAT_WS(' ', 'hello', 'world') as col_b"

    if query_num == 1:
        schema, formatted_query = Schema.create_from_hive_query(select_query=q1)
    else:
        schema, formatted_query = Schema.create_from_hive_query(select_query=q2)

    hive_result.set(schema)
    return formatted_query


@outputs(out_str=[Types.Schema()])
@dynamic_task(cache=True, cache_version='1')
def dynamic_hive_task_producer(wf_params, out_str):
    combined_results = []
    for i in (1, 2):
        task = get_uncached_query_for_dynamic(query_num=i)
        yield task
        combined_results.append(task.outputs.hive_result)
    out_str.set(combined_results)


@workflow_class
class ExampleDynamicCachedQueriesWorkflow(object):
    generate_and_run = dynamic_hive_task_producer()
