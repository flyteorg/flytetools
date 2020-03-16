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
from flytekit.common.tasks.presto_task import SdkPrestoTask

schema = Types.Schema([("a", Types.String), ("b", Types.Integer)])

presto_task = SdkPrestoTask(
    query="SELECT * FROM hive.city.fact_airport_sessions WHERE ds = '2019-07-21' LIMIT 10",
    typed_schema=schema,
    routing_group="etl",
    catalog="hive",
    schema="city",
    discoverable=False,
    discovery_version=None,
    retries=1,
    timeout=None,
)


@workflow_class()
class PrestoWorkflow(object):
    # a = Input(Types.Integer, default=10, help="Test integer input with default")
    # b = Input(Types.String, required=True, help="Test string with no default")
    # odd_nums_task = find_odd_numbers_with_string(list_of_nums=[2, 3, 4, 7], demo_string=b)
    # task_output = Output(odd_nums_task.outputs.are_num_odd, sdk_type=[Boolean])

    p_task = presto_task()
    output_a = Output(p_task.outputs.schema, sdk_type=Types.Schema)
    # output_b = Output(odd_nums_task.outputs.altered_string, sdk_type=String)
