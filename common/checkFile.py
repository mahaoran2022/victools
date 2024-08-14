# -*- coding: UTF-8 -*-
# 检查方案锁
import os
import common.sp as sp
import time


def check_lock_batch(_given_path, _given_files):
    for (dir_path, dirs, files) in os.walk(_given_path):
        # Iterate over every file name
        for _file in files:
            for _given_file in _given_files:
                # Check .lock files
                if _given_file in _file and _file.endswith('.lock'):
                    return True
    return False


def check_lock_and_wait_second(_file, _second):
    _path_name, _file_name = sp.split(_file)
    while check_lock(_path_name, _file_name):
        print("等待" + bytes(_second) + "秒")
        time.sleep(_second)


def check_lock_batch_and_wait_second(_files, _second):
    _path = ''
    _files_without_path = []
    for _file in _files:
        _path_name, _file_name = sp.split(_file)
        _path = _path_name
        _files_without_path.append(_file_name)
    while check_lock_batch(_path, _files_without_path):
        time.sleep(_second)


def check_lock(_given_path, _given_file):
    for (dir_path, dirs, files) in os.walk(_given_path):
        # Iterate over every file name
        for _file in files:
            # Check .lock files
            if _given_file in _file and _file.endswith('.lock'):
                return True
    return False


def check_shapefile(_given_path, _given_file):
    num = 0
    for (dir_path, dirs, files) in os.walk(_given_path):
        # Iterate over every file name
        for _file in files:
            if (_given_file in _file and _file.endswith('.shp')) or (
                    _given_file in _file and _file.endswith('.shx')) or (
                    _given_file in _file and _file.endswith('.dbf')) or (
                    _given_file in _file and _file.endswith('.prj')):
                num = num + 1
    if num == 4:
        return True
    return False


def file_is_exist(b):
    return os.path.isfile(b)


def get_file_size(b):
    return os.path.getsize(b)


def get_dir_size(b):
    size = 0
    for root, dirs, files in os.walk(b):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    return size


if __name__ == "__main__":
    # given_path = "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer"
    # given_files = ['fac', 'stream_order.shp']
    # if check_lock_batch(given_path, given_files):
    #     print("存在方案锁！")
    given_path = "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/anhui/anhui.imglayer/fill"
    print(get_dir_size(given_path) / (1024 * 1024))
