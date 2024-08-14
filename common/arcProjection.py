# -*- coding: UTF-8 -*-
# 投影转换
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def project(in_feature_path, out_feature_path, sr):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    # Set the workspace
    env.workspace = _path
    in_feature = _file
    if out_feature_path is None:
        out_feature_path = in_feature_path.replace('.shp', '') + '_proj.shp'
        arcpy.Project_management(in_feature, out_feature_path, sr)
        arcpy.Copy_management(out_feature_path, in_feature_path)
        arcpy.Delete_management(out_feature_path)
    else:
        arcpy.Project_management(in_feature, out_feature_path, sr)


def project_by_prj(in_feature_path, out_feature_path, projection_path):
    sr = arcpy.SpatialReference(projection_path)
    project(in_feature_path, out_feature_path, sr)


# WGS 1984 |
def project_by_reference_name(in_feature_path, out_feature_path, reference_name):
    sr = arcpy.SpatialReference(reference_name)
    project(in_feature_path, out_feature_path, sr)


# 4326 |
def project_by_factory_code(in_feature_path, out_feature_path, factory_code):
    sr = arcpy.SpatialReference(factory_code)
    project(in_feature_path, out_feature_path, sr)


#  GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
#                PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];\
#                -400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;\
#                0.001;0.001;IsHighPrecision
def project_by_wkt(in_feature_path, out_feature_path, wkt):
    sr = arcpy.SpatialReference()
    sr.loadFromString(wkt)
    project(in_feature_path, out_feature_path, sr)


def project_raster(in_raster_path, sr, out_raster_path=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_raster_path)
    # Set the workspace
    env.workspace = _path
    in_raster = _file
    if out_raster_path is None:
        out_raster_path = in_raster_path + '_proj.img'
        arcpy.ProjectRaster_management(in_raster_path, out_raster_path, sr)
        out_raster = Raster(out_raster_path)
        out_raster.save(in_raster_path)
        arcpy.Delete_management(out_raster_path)
    else:
        arcpy.ProjectRaster_management(in_raster_path, out_raster_path, sr)


# 4326 |
def project_raster_by_factory_code(in_raster_path, factory_code, out_raster_path=None):
    sr = arcpy.SpatialReference(factory_code)
    project_raster(in_raster_path, sr, out_raster_path)


# 定义投影
def define_projection(in_dataset_path, factory_code):
    # 允许覆盖
    env.overwriteOutput = True
    # 参数为输入输出地址
    _path, in_dataset = s.split(in_dataset_path)
    # 设置程序输入文件的目录
    env.workspace = _path
    sr = arcpy.SpatialReference(factory_code)
    arcpy.DefineProjection_management(in_dataset, sr)
    print("定义投影成功！")
