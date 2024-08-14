# -*- coding: UTF-8 -*-
# 对象操作
import arcpy
from arcpy import env
import common.sp as s


def get_property(in_raster_path):
    return arcpy.Describe(in_raster_path)


def get_feature_property(in_feature_path):
    a, b = s.split(in_feature_path)
    env.workspace = a
    return arcpy.Describe(in_feature_path)


def get_raster_cell_size(in_raster_path):
    return [float(arcpy.GetRasterProperties_management(in_raster_path, 'CELLSIZEX').getOutput(0)),
            float(arcpy.GetRasterProperties_management(in_raster_path, 'CELLSIZEY').getOutput(0))]
