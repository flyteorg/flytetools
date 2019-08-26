from __future__ import absolute_import
from __future__ import print_function

from app.workflows.sample_tasks import identity_sub_task, simple_batch_task, add_one_and_print


def test_identity_sub_task():
    outputs = identity_sub_task.unit_test(num=5)
    assert outputs['outs'] == 5


def test_simple_batch_task():
    outputs = simple_batch_task.unit_test(iterations=10)
    assert outputs['out'] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_add_one_and_print():
    outs = add_one_and_print.unit_test(value_to_print=15)
    assert outs['out'] == 16
