# -*- coding: UTF-8 -*-
# 分离目录和文件名
# 无法识别中文,修改

import re


def split(y):
    a = y.count("/")
    print(a)
    if a != 0:
        x = y.rsplit('/', 1)
    else:
        x = y.rsplit('\\', 1)
    d = x[0]
    e = x[1]
    return d, e


def getName(x):
    y = re.split('/|\\\\', x)
    name = y[len(y) - 1]
    return name.split('.')[0]
