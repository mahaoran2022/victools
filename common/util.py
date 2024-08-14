# -*- coding: UTF-8 -*-

# 格式化数字
def num_to_str(num, size):
    num_str = bytes(num)
    while len(num_str) < size:
        num_str = '0' + num_str
    return num_str


# 数组转字符串
def array_to_str(_array, _break):
    _str = ''
    num = 0
    for _el in _array:
        _str += bytes(_el)
        if num < len(_array) - 1:
            _str += _break
        num += 1
    return _str
