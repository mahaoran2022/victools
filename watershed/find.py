# -*- coding: UTF-8 -*-
# 寻找倾斜点
from __future__ import print_function
import arcpy
from arcpy import env
import common.sp as s
import common.checkFile as checkFile
import dao.mongo as mongo
import time


# 参数为输入输出地址
def find(_points, _reference_stream_points, _basin, _workspace_path, project_out):
    env.overwriteOutput = True  # 允许覆盖
    _points_path, _points_file = s.split(_points)
    env.workspace = _points_path

    # 近邻分析寻找near-FID
    in_features = _points
    near_features = _reference_stream_points
    # 判断是否有方案锁 有方案锁则等待 200 ms
    near_features_path, near_features_file = s.split(near_features)
    while checkFile.check_lock(near_features_path, near_features_file):
        time.sleep(0.2)
    arcpy.Near_analysis(in_features, near_features, "10000 Meters")
    arcpy.GetMessages()

    # 提取shp文件中的'NEAR_FID'字段
    _fields = ['NEAR_FID', 'name', 'code']
    _list = []
    rows = arcpy.da.SearchCursor(in_features, _fields)
    for row in rows:
        _map = {}
        _map.update({'NEAR_FID': row[0]})
        _map.update({'name': row[1]})
        _map.update({'code': row[2]})
        _list.append(_map)

    # 寻点
    for _map in _list:
        # out_feature_class = a + r"\pour_point_" + bytes(i) + ".shp"
        out_feature_class = _points_path + "/pour_point_" + _map['name'] + _map['code'] + ".shp"
        # 判断是否已存在对应输出
        if not checkFile.file_is_exist(out_feature_class):
            if _map['NEAR_FID'] == -1:
                in_features = _points
                where_clause = '"code" = ' + "'" + bytes(_map['code']) + "'"
                print(where_clause)
                print(in_features)
                arcpy.Select_analysis(in_features, out_feature_class, where_clause)
            else:
                in_features = _reference_stream_points
                where_clause = '"FID" = ' + bytes(_map['NEAR_FID'])
                arcpy.Select_analysis(in_features, out_feature_class, where_clause)
        # 更新数组
        for _basin_one in _basin:
            if bytes(_map['code']) == bytes(_basin_one['code']):
                _basin_one.update({'pour_point_path': out_feature_class.replace(_workspace_path, '')})
                _basin_one.update({'project_out': project_out})
                break
    print("寻点成功！")
    return _basin


# m=r"D:\ArcGIS\data\yalujiang.tiftuceng\str"
# n="dhfpoint.shp"
# print(find(m,n))
# 成功！


# if __name__ == '__main__':
#     find('D:/Workspace/arcgis-workspace/arcpy_workspace/dem/point/point.shp',
#          'D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imgtuceng/streamorder.shp')
