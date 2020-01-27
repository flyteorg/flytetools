from __future__ import absolute_import
from __future__ import print_function

from app.workflows.failing_workflows import retryer
from flytekit.sdk.tasks import (
    dynamic_task,
)
from flytekit.sdk.workflow import workflow_class


@dynamic_task(cpu_request="200m", cpu_limit="200m", memory_request="500Mi", memory_limit="500Mi", retries=3)
def sample_batch_task_cachable(wf_params):
    yield retryer()
    yield retryer()


@workflow_class
class RetryableDynamicWorkflow(object):
    dynamic_task = sample_batch_task_cachable()
