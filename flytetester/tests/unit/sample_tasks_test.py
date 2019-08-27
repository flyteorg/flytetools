from __future__ import absolute_import
from __future__ import print_function

from app.workflows.sample_tasks import add_one_and_print
from app.workflows.work import find_odd_numbers_with_string


def test_add_one_and_print():
    outs = add_one_and_print.unit_test(value_to_print=15)
    assert outs['out'] == 16


def test_find_odd_numbers_with_string():
    outs = find_odd_numbers_with_string.unit_test(list_of_nums=[3,4], demo_string='hello world')
    assert outs['altered_string'] == 'hello world_changed'
    assert outs['are_num_odd'] == [True, False]
