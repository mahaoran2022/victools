# -*- coding: UTF-8 -*-
# 经纬度坐标点转点要素
from __future__ import print_function
import arcpy
import common.sp as s
import json
import common.jsonConvert as jsonConvert
import os


# 参数为输出地址
def point(_points_out_path, _basin_points):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _points_out_file = s.split(_points_out_path)
    # 定义坐标系以及各种字段
    sr = arcpy.SpatialReference("WGS 1984")
    result_path = _path
    result_file = _points_out_file
    create_file = arcpy.CreateFeatureclass_management(result_path, result_file, "POINT", "", "", "", sr)
    # createFC = arcpy.CreateFeatureclass_management(resultpath, resultshp, "POINT")
    arcpy.AddField_management(create_file, "num", "SHORT")
    arcpy.AddField_management(create_file, "code", "TEXT")
    arcpy.AddField_management(create_file, "name", "TEXT")
    arcpy.AddField_management(create_file, "longitude", "DOUBLE")
    arcpy.AddField_management(create_file, "latitude", "DOUBLE")
    arcpy.AddField_management(create_file, "rainfall", "DOUBLE")
    _fields = []
    _fields.append('shape')
    _fields.append('code')
    _fields.append('name')
    _fields.append('longitude')
    _fields.append('latitude')
    _fields.append('rainfall')
    cur = arcpy.da.InsertCursor(create_file, _fields)
    for _rainfall_station in _basin_points:
        if 'watershed_path' not in _rainfall_station:
            # row = cur.newRow()
            _point = arcpy.Point()
            code = _rainfall_station['stcd']
            name = _rainfall_station['stnm']
            lon = float(_rainfall_station['lgtd'])
            lat = float(_rainfall_station['lttd'])
            rainfall = _rainfall_station['rainfall']
            _point.X = lon
            _point.Y = lat
            point_geometry = arcpy.PointGeometry(_point)
            # row.shape = point_geometry
            # row.name = name
            # row.LGTD = lon
            # row.LTTD = lat
            # row.code = code
            cur.insertRow((point_geometry, code, name, lon, lat, rainfall))
    print("点要素生成成功！")
# point(r"D:\ArcGIS\data\yalujiang.tiftuceng\point.shp",[["科后",125.720555,49.360833],["尼尔基",124.528583,48.492617]])
# 成功！


if __name__ == '__main__':
    # json解析
    # json_read = "D:/Workspace/arcgis-workspace/arcpy_workspace/rainfall.json"
    # _json_str = jsonConvert.jsonfile_to_json_str(json_read)
    # _json = json.loads(_json_str, encoding='gb18030')
    # point('D:/Workspace/arcgis-workspace/arcpy_workspace/rainfall.shp',_json)

    _given_path = u"D:/Workspace/arcgis-workspace/shuju/GIS检验"
    for (dir_path, dirs, files) in os.walk(_given_path):
        # Iterate over every file name
        for _file in files:
            if _file.endswith('.txt'):
                json_read = dir_path + "/" + _file
                _json_str = jsonConvert.jsonfile_to_json_str(json_read)
                _json = json.loads(_json_str, encoding='gb18030')
                point(dir_path + "/point_" + _file.replace('-', '_').replace('.', '') + ".shp", _json)


