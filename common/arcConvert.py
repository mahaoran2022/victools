# -*- coding: UTF-8 -*-
# 转换工具
from __future__ import print_function
import arcpy
from arcpy import env
import common.sp as s
import common.jsonConvert as jsonConvert
import common.checkFile as checkFile
import json


def raster_to_polygon(filepath, check_exist, out_polygons_path=None):
    # 参数为输入输出地址
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(filepath)
    # Set environment settings
    env.workspace = _path

    # Set local variables
    in_raster = _file
    # out_polygons = _file.rsplit('.')[0] + ".shp"
    if out_polygons_path is None:
        out_polygons = _file.replace('.tif', '') + '.shp'
        out_polygons_path = _path + "/" + out_polygons
    if check_exist and checkFile.file_is_exist(out_polygons_path):
        return out_polygons_path
    field = "VALUE"
    # Execute RasterToPolygon
    arcpy.RasterToPolygon_conversion(in_raster, out_polygons_path, "NO_SIMPLIFY", field)
    print("栅格转面成功！")
    return out_polygons_path


def raster_to_polygon_3d(filepath):
    # 参数为输入输出地址
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(filepath)
    # Set environment settings
    env.workspace = _path

    # Set local variables
    in_raster = _file
    # out_polygons = _file.rsplit('.')[0] + ".shp"
    out_polygons = _file.replace('.tif', '') + '_ori.shp'

    # Execute RasterToPolygon
    arcpy.RasterDomain_3d(in_raster, out_polygons, "POLYGON")
    print("栅格转面成功！")

    return _path + "/" + out_polygons


# m=r"D:\ArcGIS\data\yalujiang.tiftuceng\liuyu0"
# shil(m)
#     # Set environment settings
#     env.workspace = a
#     # Set local variables
#     inStreamRaster = b
#     inFlowDir = y
#     outStreamFeats = w
#     # Check out the ArcGIS Spatial Analyst extension license
#     arcpy.CheckOutExtension("Spatial")
#     # Execute
#     StreamToFeature(inStreamRaster, inFlowDir, outStreamFeats,"NO_SIMPLIFY")


def raster_to_point(filepath, river_corr_point=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(filepath)
    # 栅格转点要素
    env.workspace = _path
    in_raster = _file
    if river_corr_point is None:
        out_point = filepath + ".shp"
    else:
        out_point = river_corr_point
    field = "VALUE"
    arcpy.RasterToPoint_conversion(in_raster, out_point, field)
    print("栅格转点成功！")


def point_to_raster(in_features_path, value_field, out_rasterdataset, cell_assignment=None, priority_field=None,
                    cellsize=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_features_path)
    # 栅格转点要素
    env.workspace = _path
    in_features = _file
    arcpy.PointToRaster_conversion(in_features, value_field, out_rasterdataset, cell_assignment, priority_field,
                                   cellsize)
    print("点转栅格成功！")


def feature_to_json(filepath):  # 参数为输入输出地址
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(filepath)
    # Set the workspace
    env.workspace = _path
    json_in = _file
    # json_out
    in_raster = _file
    # json_out = _file.rsplit('.')[0] + ".json"
    json_out = _file.replace('.shp', '') + '.json'
    json_out_path = _path + "/" + json_out
    if not checkFile.file_is_exist(json_out_path):
        # Convert the selected features to JSON
        arcpy.FeaturesToJSON_conversion(json_in, json_out, "", "", "", "GEOJSON")
    else:
        checkFile.check_lock_and_wait_second(filepath, 0.2)
        arcpy.FeaturesToJSON_conversion(json_in, json_out, "", "", "", "GEOJSON")
    print("json转化成功！")

    return json_out_path


def json_to_feature(_geo_json, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    # polygon = arcpy.AsShape(json)
    # polygon.save(out_feature_path)
    _esri_json = jsonConvert.geo_to_esri(_geo_json, None)
    out_json_path = out_feature_path.replace('.shp', '.json')
    _json_str = json.dumps(_esri_json)
    with open(out_json_path, 'w') as json_file:
        json_file.write(_json_str)
    checkFile.check_lock_and_wait_second(out_feature_path, 0.2)
    arcpy.JSONToFeatures_conversion(out_json_path, out_feature_path)
    # sr = arcpy.SpatialReference("WGS 1984")
    # arcpy.DefineProjection_management(out_feature_path, sr)
    print("json转矢量成功！")


# 本方法不能输出属性表
def feature_to_features(in_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    # Set the workspace
    env.workspace = _path
    with arcpy.da.SearchCursor(_file, ["SHAPE@", 'FID']) as cursor:
        # SHAPE@指代单个要素，ID是一个字段，该字段也是我们想要作为每个polygon命名的值，也可以改为其他的字段
        for row in cursor:
            out_name = str(row[1]) + '.shp'  # 输出文件名 确保均为字符串类型，注意命名是唯一的，这样就能将该shp数据中的所有要素都导出
            arcpy.FeatureClassToFeatureClass_conversion(row[0], _path, out_name)

# if __name__ == '__main__':
#     raster_to_point('D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imgtuceng/streamorder')
#     feature_to_features(u"D:/Workspace/arcgis-workspace/arcpy_workspace/uploadedWatershed/一级/一级.shp")
