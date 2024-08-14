# -*- coding: UTF-8 -*-
# 空间分析
import common.sp as s
import arcpy
from arcpy import env
from arcpy.sa import *


# 按掩膜提取
def extract_by_mask(_input_path, _mask_path, _output_path):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(_input_path)
    # Set environment settings
    env.workspace = _path

    # Set local variables
    in_raster = _input

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute ExtractByMask
    out_extract_by_mask = ExtractByMask(in_raster, _mask_path)

    # Save the output
    out_extract_by_mask.save(_output_path)
    print("掩膜提取成功！")


# 值提取至点
def extract_values_to_points(in_point_features, in_raster, out_point_features=None, interpolate_values=None,
                             add_attributes=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _features = s.split(in_point_features)
    # Set environment settings
    env.workspace = _path

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    if out_point_features is None:
        out_point_features = in_point_features.replace('.shp', '_copy.shp')
        ExtractValuesToPoints(in_point_features, in_raster, out_point_features,
                              interpolate_values, add_attributes)
        arcpy.Copy_management(out_point_features, in_point_features)
        arcpy.Delete_management(out_point_features)
    else:
        # Execute ExtractValuesToPoints
        ExtractValuesToPoints(in_point_features, in_raster, out_point_features,
                              interpolate_values, add_attributes)
    print("值提取至点成功！")


# 空值可用""
def con_function(in_conditional_raster, in_true_raster_or_constant, in_false_raster_or_constant=None, where_clause=None,
                 out_raster=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(in_conditional_raster)
    # Set environment settings
    env.workspace = _path

    # Execute Con
    out_con = Con(in_conditional_raster, in_true_raster_or_constant, in_false_raster_or_constant, where_clause)
    # Save the outputs
    if out_raster is None:
        out_raster_path = in_conditional_raster + '_con'
        out_con.save(out_raster_path)
        # Copy to cloud raster format
        arcpy.Copy_management(out_raster_path, in_conditional_raster)
        arcpy.Delete_management(out_raster_path)
    else:
        out_con.save(out_raster)
    print("条件应用成功！")


# 以表格显示分区统计
# ignore_nodata DATA | NODATA
# statistics_type ALL | MEAN | MAJORITY | MAXIMUM | MEDIAN | MINIMUM | MINORITY | RANGE | STD | SUM | VARIETY | MIN_MAX | MEAN_STD | MIN_MAX_MEAN
def zonal_statistics_as_table(in_zone_data_path, zone_field, in_value_raster_path, out_table_path, ignore_nodata=None,
                              statistics_type=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(in_zone_data_path)
    # Set environment settings
    env.workspace = _path

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute ZonalStatisticsAsTable
    ZonalStatisticsAsTable(in_zone_data_path, zone_field, in_value_raster_path,
                           out_table_path, ignore_nodata, statistics_type)
    print("以表格显示分区统计成功！")


# 坡度
# method PLANAR —将使用 2D 笛卡尔坐标系对投影平面执行计算。这是默认方法 | GEODESIC —通过将地球形状视为椭球体，在 3D 笛卡尔坐标系中执行计算
# output_measurement DEGREE —坡度倾角将以度为单位进行计算 | PERCENT_RISE —坡度倾角将以增量百分比进行计算，也称为百分比坡度
# z_unit INCH —英寸（美制） | FOOT —英尺 | YARD —码（美制） | MILE_US —英里（美制） | NAUTICAL_MILE —海里 | MILLIMETER —毫米 | CENTIMETER —厘米 | METER —米 | KILOMETER —千米 | DECIMETER —分米
def slope_function(in_raster_path, out_slope_path, method=None, output_measurement=None, z_factor=None, z_unit=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(in_raster_path)
    # Set environment settings
    env.workspace = _path

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    out_slope = Slope(in_raster_path, output_measurement, z_factor, method, z_unit)

    # Save the outputs
    out_slope.save(out_slope_path)
    print("坡度计算成功！")


def watershed(in_flow_direction_raster, in_pour_point_data, out_shape_path, pour_point_field=None, extent=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_flow_direction_raster)
    # Set environment settings
    env.workspace = _path
    if extent:
        env.extent = extent
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute Watershed
    outWatershed = Watershed(_file, in_pour_point_data, pour_point_field)
    # Save the output
    outWatershed.save(out_shape_path)
    if extent:
        # 恢复环境
        arcpy.ResetEnvironments()
        # 允许覆盖
        env.overwriteOutput = True
        # 破解版不允许并行
        env.parallelProcessingFactor = 0


def ZonalStatisticsAsTable(in_zone_data_path, zone_field, in_value_raster, out_table, ignore_nodata=None,
                           statistics_type=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_zone_data_path)
    # Set environment settings
    env.workspace = _path
    arcpy.gp.ZonalStatisticsAsTable_sa(_file, zone_field, in_value_raster,
                                       out_table, ignore_nodata, statistics_type)
