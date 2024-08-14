# -*- coding: UTF-8 -*-
# 经纬度坐标点转点要素
from __future__ import print_function
import arcpy
import common.sp as s


# 参数为输出地址
def point(_points_out_path, _basin_points):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _points_out_file = s.split(_points_out_path)
    # _file = os.listdir(a)  # 删除可能存在的point
    # for fi in _file:
    #     if "point" in fi:
    #         f = a+"/"+fi
    #         os.remove(f)
    # 按照”;“和”,“将数据处理成二维数组写入
    # p = []
    # if ";" in y:
    #     q = y.split(";")
    #     for i in q:
    #         p.append(i.split(","))
    # else:
    #     q = y.split(",")
    #     p.append(q)
    # 定义坐标系以及各种字段
    sr = arcpy.SpatialReference("WGS 1984")
    result_path = _path
    result_file = _points_out_file
    create_file = arcpy.CreateFeatureclass_management(result_path, result_file, "POINT", "", "", "", sr)
    # createFC = arcpy.CreateFeatureclass_management(resultpath, resultshp, "POINT")
    arcpy.AddField_management(create_file, "num", "SHORT")
    arcpy.AddField_management(create_file, "name", "TEXT")
    arcpy.AddField_management(create_file, "LGTD", "DOUBLE")
    arcpy.AddField_management(create_file, "LTTD", "DOUBLE")
    arcpy.AddField_management(create_file, "code", "TEXT")
    _fields = []
    _fields.append('shape')
    _fields.append('name')
    _fields.append('LGTD')
    _fields.append('LTTD')
    _fields.append('code')
    cur = arcpy.da.InsertCursor(create_file, _fields)
    for _basin_point in _basin_points:
        if 'watershed_path' not in _basin_point:
            # row = cur.newRow()
            _point = arcpy.Point()
            name = _basin_point['name']
            lon = float(_basin_point['longitude'])
            lat = float(_basin_point['latitude'])
            code = _basin_point['code']
            _point.X = lon
            _point.Y = lat
            point_geometry = arcpy.PointGeometry(_point)
            # row.shape = point_geometry
            # row.name = name
            # row.LGTD = lon
            # row.LTTD = lat
            # row.code = code
            # cur.insertRow(row)
            cur.insertRow((point_geometry, name, lon, lat, code))
    print(u"点要素生成成功！")
# point(r"D:\ArcGIS\data\yalujiang.tiftuceng\point.shp",[["科后",125.720555,49.360833],["尼尔基",124.528583,48.492617]])
# 成功！


# if __name__ == '__main__':
#     point('D:/Workspace/arcgis-workspace/arcpy_workspace/dem/point/point.shp', 'kehou,125.720555,49.360833,11204600')


