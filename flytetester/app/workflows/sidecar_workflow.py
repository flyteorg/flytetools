from __future__ import absolute_import
from __future__ import print_function

import time
import os

from flytekit.sdk.tasks import sidecar_task
from flytekit.sdk.workflow import workflow_class
from k8s.io.api.core.v1 import generated_pb2


# A simple pod spec in which a shared volume is mounted in both the primary and secondary containers. The secondary
# writes a file that the primary waits on before completing.
def generate_pod_spec_for_task():
    pod_spec = generated_pb2.PodSpec()

    primary_container = generated_pb2.Container(name="primary")

    secondary_container = generated_pb2.Container(
        name="secondary",
        image="alpine",
    )
    secondary_container.command.extend(["/bin/sh"])
    secondary_container.args.extend(["-c", "echo hi sidecar world > /data/message.txt"])
    shared_volume_mount = generated_pb2.VolumeMount(
        name="shared-data",
        mountPath="/data",
    )
    secondary_container.volumeMounts.extend([shared_volume_mount])
    primary_container.volumeMounts.extend([shared_volume_mount])

    pod_spec.volumes.extend([generated_pb2.Volume(
        name="shared-data",
        volumeSource=generated_pb2.VolumeSource(
            emptyDir=generated_pb2.EmptyDirVolumeSource(
                medium="Memory",
            )
        )
    )])
    pod_spec.containers.extend([primary_container, secondary_container])
    return pod_spec


@sidecar_task(
    pod_spec=generate_pod_spec_for_task(),
    primary_container_name="primary",
)
def primary_sidecar_task(wfparams):
    # The code defined in this task will get injected into the primary container.
    while not os.path.isfile('/data/message.txt'):
        time.sleep(5)


@workflow_class
class SidecarWorkflow(object):
    s = primary_sidecar_task()
