# -*- coding: UTF-8 -*-
import arcpy
from arcpy import env
import common.sp as s


def get_table_list(_shape_path, fields=None):
    a, b = s.split(_shape_path)
    env.workspace = a
    _list = []
    if fields is not None and len(fields) > 0:
        rows = arcpy.da.SearchCursor(_shape_path, fields)
    else:
        # 提取field
        desc = arcpy.Describe(_shape_path)
        fields = []
        for field in desc.fields:
            fields.append(field.Name)
        rows = arcpy.da.SearchCursor(_shape_path, fields)
    for row in rows:
        _map = {}
        for i in range(len(fields)):
            _map.update({fields[i]: row[i]})
        _list.append(_map)
    print("获得表格！")
    return _list


if __name__ == '__main__':
    # get_table_list("D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer/point/point_100.shp", None)
    get_table_list(
        "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer/watershed/watershed_kehou.shp", None)
#     get_table_list("D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer/point/point_100.shp", ['NEAR_FID', 'name', 'code'])
