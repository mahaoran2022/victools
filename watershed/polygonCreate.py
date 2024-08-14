# -*- coding: UTF-8 -*-
# 创建面要素
import arcpy
import common.sp as s


# 参数为输出地址
# List of coordinates (ID, X, Y)
# coords_list = [[1, -61845879.0968, 45047635.4861],
#                [1, -3976119.96791, 46073695.0451],
#                [1, 1154177.8272, -25134838.3511],
#                [1, -62051091.0086, -26160897.9101],
#                [2, 17365918.8598, 44431999.7507],
#                [2, 39939229.1582, 45252847.3979],
#                [2, 41170500.6291, 27194199.1591],
#                [2, 17981554.5952, 27809834.8945],
#                [3, 15519011.6535, 11598093.8619],
#                [3, 52046731.9547, 13034577.2446],
#                [3, 52867579.6019, -16105514.2317],
#                [3, 17160706.948, -16515938.0553]]
def polygon(_out_path, coords_list=None):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _out_file = s.split(_out_path)

    result_path = _path
    result_file = _out_file
    # 定义坐标系以及各种字段
    sr = arcpy.SpatialReference("WGS 1984")
    # Create a feature class with a spatial reference of GCS WGS 1984
    create_file = arcpy.CreateFeatureclass_management(result_path, result_file, "POLYGON", "", "", "", sr)
    if coords_list is not None:
        cur = arcpy.da.InsertCursor(create_file, ["SHAPE@"])
        array = arcpy.Array()
        # Initialize a variable for keeping track of a feature's ID.
        _ID = -1
        for coords in coords_list:
            if _ID == -1:
                _ID = coords[0]
            # Add the point to the feature's array of points
            #   If the ID has changed, create a new feature
            if _ID != coords[0]:
                cur.insertRow([arcpy.Polyline(array)])
                array.removeAll()
            array.add(arcpy.Point(coords[1], coords[2], ID=coords[0]))
            _ID = coords[0]
        # Add the last feature
        _polygon = arcpy.Polygon(array)
        cur.insertRow([_polygon])
        array.removeAll()
    print("面要素生成成功！")


# if __name__ == '__main__':
#     point('D:/Workspace/arcgis-workspace/arcpy_workspace/dem/point/point.shp', 'kehou,125.720555,49.360833,11204600')


