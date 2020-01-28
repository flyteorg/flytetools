from __future__ import absolute_import
from __future__ import print_function

from app.workflows.failing_workflows import retryer
from flytekit.sdk.tasks import (
    dynamic_task,
)
from flytekit.sdk.workflow import workflow_class


@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi", retries=2)
def sample_dynamic_task(wf_params):
    yield retryer()
    yield retryer()


@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi", retries=2)
def sample_dynamic_task_recursive(wf_params):
    yield sample_dynamic_task()


@workflow_class
class RetryableDynamicWorkflow(object):
    dynamic_task = sample_dynamic_task()
