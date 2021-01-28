from app.workflows.sample_tasks import add_one_and_print
from app.workflows.work import find_odd_numbers_with_string
from app.workflows.dynamic_workflows import sample_batch_task_cachable


def test_add_one_and_print():
    outs = add_one_and_print.unit_test(value_to_print=15)
    assert outs['out'] == 16


def test_find_odd_numbers_with_string():
    outs = find_odd_numbers_with_string.unit_test(list_of_nums=[3, 4], demo_string='hello world')
    assert outs['altered_string'] == 'hello world_changed'
    assert outs['are_num_odd'] == [True, False]


def test_fds():
    res = sample_batch_task_cachable.unit_test(caching_input=10.0)
    assert res == {'out_str': ["I'm the first result", 'hello 0', "I'm after each sub-task result", 'hello 1',
                               "I'm after each sub-task result", 'hello 2', "I'm after each sub-task result",
                               "I'm the last result"],
                   'out_ints': [[0, 0, 0], [1, 2, 3], [2, 4, 6], [0, 1, 4], [0, 1, 4]]}
