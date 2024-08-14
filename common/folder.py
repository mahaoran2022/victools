# -*- coding: UTF-8 -*-
import os
import shutil


def create_layer(a):
    b = a + 'layer'
    return clear_and_create_folder(b)


def create_initial_folder(a):
    b = a + '_initial'
    return clear_and_create_folder(b)


def create_project_folder(a):
    b = a + '_project'
    return clear_and_create_folder(b)


def delete_folder(a):
    shutil.rmtree(a)
    print("删除文件夹")


def clear_and_create_folder(b):
    d = os.path.exists(b)
    if not d:
        os.makedirs(b)
        print("成功创建")
    else:
        print("文件夹已存在")
        shutil.rmtree(b)
        os.makedirs(b)
        print("文件夹重新创建！")
    return b


# x=file("D:/ArcGIS/nierjiinput.img")


def not_exist_then_create_folder(b):
    d = os.path.exists(b)
    if not d:
        os.makedirs(b)
        print("文件夹成功创建")
    return b


def folder_is_exist(b):
    return os.path.exists(b)
