# -*- coding: UTF-8 -*-
import sys
import time
import os.path
import shutil
import numpy as np
import math
import configparser
import arcpy
from arcpy import env
import common.sp as s
import common.constant as constant
import common.arcUtils as arcUtils
import common.arcConvert as arcConvert
import common.arcAnalysis as arcAnalysis
import common.arcProjection as arcProjection
import common.arcDataManagement as arcDataManagement


def generate_point(_in_value_path, _out_shp_path, _precision):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(_out_shp_path)
    # Set the workspace
    env.workspace = _path
    CENTROID_X = 'CENTROID_X'
    CENTROID_Y = 'CENTROID_Y'
    sr = arcpy.Describe(_in_value_path).spatialReference
    create_file = arcpy.CreateFeatureclass_management(_path, _file, "POINT", "", "", "", sr)
    arcpy.AddField_management(create_file, "pointid", "LONG")
    arcpy.AddField_management(create_file, "grid_code", "LONG")
    cursor = arcpy.da.InsertCursor(create_file, ['SHAPE@XY', 'pointid', 'grid_code'])
    rows = arcpy.SearchCursor(_in_value_path)  # 查询游标
    index = 1
    grid_code_num = 1
    for row in rows:
        _point = arcpy.Point()
        _x = row.getValue(CENTROID_X)
        _x = float(int(_x * 10 ** _precision)) / 10 ** _precision
        # print(_x)
        _point.X = _x
        _y = row.getValue(CENTROID_Y)
        _y = float(int(_y * 10 ** _precision)) / 10 ** _precision
        _point.Y = _y
        # print(_y)
        point_geometry = arcpy.PointGeometry(_point)
        cursor.insertRow((point_geometry, index, grid_code_num))
        index = index + 1
    del cursor


def main():
    '''
    直接从basin文件生成点文件
    '''
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini')
    _basin_name = config.get('general', 'basin_name')  # dem
    gridSize = config.get('general', 'gridsize')
    gridSize = float(gridSize)

    # 工作空间路径
    _workspace_path = os.path.dirname(os.path.abspath(__file__))
    _calculate_path = os.path.join(_workspace_path, 'data', 'watershed', _basin_name, 'calculate')
    dic_out = _calculate_path

    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0
    # ################# 字符串常量 #################
    # ################# 路径常量 #################
    basin_path = dic_out + "/basin.shp"
    basin_bak_path = basin_path.replace('.shp', '_bak.shp')
    all_area_path = dic_out + "/all_area.shp"
    intersect_area_path = dic_out + "/is_area.shp"
    basin_point_path = dic_out + '/basin_clip.shp'
    # ################# start logic ##############
    # Define pixel_size and NoData value of new raster
    NoData_value = 0
    Data_value = 1
    # 备份，虽然文档写这个是只读属性，但是实操的时候属性读过就消失
    arcpy.CopyFeatures_management(basin_path, basin_bak_path)
    desc = arcpy.Describe(basin_bak_path)
    x_min = desc.extent.XMin
    x_max = desc.extent.XMax
    y_min = desc.extent.YMin
    y_max = desc.extent.YMax
    # adjust the output domain to grid size floating point
    _precision = len(str(gridSize).split(".")[1])
    _precision = _precision + 1
    xOff = x_min % gridSize
    x_min = x_min - xOff
    x_min = float(int(x_min * 10 ** _precision)) / 10 ** _precision
    xOff = x_max % gridSize
    x_max = x_max + (gridSize - xOff)
    x_max = float(int(x_max * 10 ** _precision)) / 10 ** _precision
    yOff = y_max % gridSize
    y_max = y_max + (gridSize - yOff)
    y_max = float(int(y_max * 10 ** _precision)) / 10 ** _precision
    yOff = y_min % gridSize
    y_min = y_min - yOff
    y_min = float(int(y_min * 10 ** _precision)) / 10 ** _precision
    # Create the destination data source
    x_res = int(np.ceil((x_max - x_min) / gridSize))
    y_res = int(np.ceil((y_max - y_min) / gridSize))
    # Loop over array to find the elements the high res raster falls in
    point_data_all = []
    for i in range(y_res):
        for j in range(x_res):
            _y = y_min + i * gridSize
            _x = x_min + j * gridSize
            item = {}
            item["_x"] = _x
            item["_y"] = _y
            point_data_all.append(item)
    arcUtils.create_area_shp(point_data_all, gridSize, all_area_path)
    # 定义投影
    arcProjection.define_projection(all_area_path, 4326)
    _area_id = 'area_id'
    arcDataManagement.add_field(all_area_path, _area_id, 'LONG')
    arcUtils.update_field_by_order(all_area_path, _area_id)
    hiResRatio = 50.
    highResGrid = gridSize / hiResRatio
    arcAnalysis.intersect([all_area_path, basin_path], intersect_area_path, cluster_tolerance=highResGrid)
    generate_point(intersect_area_path, basin_point_path, _precision)


def break_point_flg():
    pass


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
