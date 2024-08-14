# -*- coding: UTF-8 -*-
import sys
import time
import os.path
import shutil
import numpy as np
import math
import configparser
import pickle
import dao.mongo as _mongo
import arcpy
from arcpy import env
from arcpy.sa import *
import common.constant as constant
import common.sp as s
import common.folder as _folder
import common.arcSpatialAnalyst as arcSpatialAnalyst
import common.arcProjection as arcProjection
import common.arcConvert as arcConvert
import common.arcDataManagement as arcDataManagement
import common.arcUtils as arcUtils
import common.data as _data
import common.arcAnalysis as arcAnalysis


def check_properties(_src_path, fields):
    # ['pointid', SoilID, 'T_SAND', 'T_CLAY', 'T_OC', 'S_SAND', 'S_CLAY', 'S_OC']
    item = {}
    # 循环保存上一条 ，记录SoilID对应的数据 ...
    with arcpy.da.UpdateCursor(_src_path, fields) as cursor:
        for row in cursor:
            if row[fields.index('T_SAND')] == 0:
                row[fields.index('T_SAND')] = item['T_SAND']
                row[fields.index('T_CLAY')] = item['T_CLAY']
                row[fields.index('T_OC')] = item['T_OC']
                row[fields.index('S_SAND')] = item['S_SAND']
                row[fields.index('S_CLAY')] = item['S_CLAY']
                row[fields.index('S_OC')] = item['S_OC']
                cursor.updateRow(row)
            else:
                item['T_SAND'] = row[fields.index('T_SAND')]
                item['T_CLAY'] = row[fields.index('T_CLAY')]
                item['T_OC'] = row[fields.index('T_OC')]
                item['S_SAND'] = row[fields.index('S_SAND')]
                item['S_CLAY'] = row[fields.index('S_CLAY')]
                item['S_OC'] = row[fields.index('S_OC')]


def statistics_soil_type(soil_type_map, soil_type_data_to_hydraulic_parameter, soil_type_data):
    soil_type_data_to_hydraulic_parameter_map = arcUtils.list_to_map(soil_type_data_to_hydraulic_parameter,
                                                                     'soil_type_code')

    for _key in soil_type_map:
        item = soil_type_map[_key]
        # T layer
        _sand_mean_value_T = item['T_SAND']
        _clay_mean_value_T = item['T_CLAY']
        _err_T = 999999999
        _soil_type_code_T = -1
        # S layer
        _sand_mean_value_S = item['S_SAND']
        _clay_mean_value_S = item['S_CLAY']
        _err_S = 999999999
        _soil_type_code_S = -1
        for _soil_type_one in soil_type_data:
            _sand_tar = _soil_type_one['sand_percent']
            _clay_tar = _soil_type_one['clay_percent']
            if abs(_sand_tar - _sand_mean_value_T) + abs(_clay_tar - _clay_mean_value_T) < _err_T:
                _err_T = abs(_sand_tar - _sand_mean_value_T) + abs(_clay_tar - _clay_mean_value_T)
                _soil_type_code_T = _soil_type_one['soil_type_code']
            if abs(_sand_tar - _sand_mean_value_S) + abs(_clay_tar - _clay_mean_value_S) < _err_S:
                _err_S = abs(_sand_tar - _sand_mean_value_S) + abs(_clay_tar - _clay_mean_value_S)
                _soil_type_code_S = _soil_type_one['soil_type_code']
        if _soil_type_code_T > 0:
            item['soil_type_code_T'] = _soil_type_code_T
        if _soil_type_code_S > 0:
            item['soil_type_code_S'] = _soil_type_code_S
    # print("soil_type_map")
    # print(soil_type_map)
    for _key in soil_type_map:
        item = soil_type_map[_key]
        _key_T = item['soil_type_code_T']
        item['hydraulic_T'] = soil_type_data_to_hydraulic_parameter_map[_key_T]
        _key_S = item['soil_type_code_S']
        item['hydraulic_S'] = soil_type_data_to_hydraulic_parameter_map[_key_S]
    # print("soil_type_map")
    # print(soil_type_map)


def get_soil_params(soil_data):
    exec(open("./SWCharEst.py").read())
    soil_data_np = np.array(soil_data)
    soil_results = {}
    for i in range(len(soil_data_np)):
        soilTexture = [soil_data_np[i, 2] / 100, soil_data_np[i, 3] / 100, soil_data_np[i, 4] / 0.58]
        swc = SWCharEst()
        results = swc.Get(soilTexture[0], soilTexture[1], soilTexture[2])
        _new_item = {}
        for _key in results:
            _new_item[_key + '1'] = results[_key]
        soil_results[soil_data[i][0]] = _new_item
    for i in range(len(soil_data_np)):
        soilTexture = [soil_data_np[i, 5] / 100, soil_data_np[i, 6] / 100, soil_data_np[i, 7] / 0.58]
        swc = SWCharEst()
        results = swc.Get(soilTexture[0], soilTexture[1], soilTexture[2])
        _new_item = {}
        for _key in results:
            _new_item[_key + '2'] = results[_key]
        soil_results[soil_data[i][0]].update(_new_item)
    return soil_results


def create_soil_table(_list, soil_type_map, soil_params, _avg_rain):
    result = []
    index = 1
    for row in _list:
        solidId = row["SoilID"]
        soil_type = soil_type_map.get(solidId)
        pointid = row["pointid"]
        soil_param = soil_params.get(pointid)
        item = {}
        item["RUN"] = 1
        item["GRID"] = index
        index = index + 1
        item["LAT"] = row["LAT"]
        item["LNG"] = row["LNG"]
        item["lNFlLT"] = 0.35
        item["Ds"] = 0.3
        item["Ds_MAX"] = 25
        item["Ws"] = 0.6
        item["C"] = 2
        item["EXPT_1"] = soil_type['hydraulic_T']['saturated_hydraulic_conductivity']
        item["EXPT_2"] = soil_type['hydraulic_S']['saturated_hydraulic_conductivity']
        item["EXPT_3"] = soil_type['hydraulic_S']['saturated_hydraulic_conductivity']
        item["Ksat_1"] = soil_param['Ks1'] * 10 * 3600 * 24
        item["Ksat_2"] = soil_param['Ks2'] * 10 * 3600 * 24
        item["Ksat_3"] = soil_param['Ks2'] * 10 * 3600 * 24
        item["PHI_1"] = -99
        item["PHI_2"] = -99
        item["PHI_3"] = -99
        item["MOIST_1"] = 20
        item["MOIST_2"] = 30
        item["MOIST_3"] = 50
        item["ELEV"] = row["ELEV"]
        item["DEPTH_1"] = 0.1
        item["DEPTH_2"] = 0.3
        item["DEPTH_3"] = 0.85
        item["AVG_T"] = -99
        item["DP"] = 4
        item["BUBLE1"] = soil_type['hydraulic_T']['bubble_pressure']
        item["BUBLE2"] = soil_type['hydraulic_S']['bubble_pressure']
        item["BUBLE3"] = soil_type['hydraulic_S']['bubble_pressure']
        item["QUARZ1"] = -99
        item["QUARZ2"] = -99
        item["QUARZ3"] = -99
        item["BULKDN1"] = soil_type['hydraulic_T']['overall_density']
        item["BULKDN2"] = soil_type['hydraulic_S']['overall_density']
        item["BULKDN3"] = soil_type['hydraulic_S']['overall_density']
        item["PARTDN1"] = 2685
        item["PARTDN2"] = 2685
        item["PARTDN3"] = 2685
        item["OFF_GMT"] = 8
        item["WcrFT1"] = soil_param['FC1']
        item["WcrFT2"] = soil_param['FC2']
        item["WcrFT3"] = soil_param['FC2']
        item["WpFT1"] = soil_param['WP1']
        item["WpFT2"] = soil_param['WP2']
        item["WpFT3"] = soil_param['WP2']
        item["Z0_SOIL"] = 0.001
        item["Z0_SNOW"] = 0.0005
        item["PRCP"] = _avg_rain
        item["RESM1"] = 0.027
        item["RESM2"] = 0.027
        item["RESM3"] = 0.027
        item["FS_ACTV"] = 0
        result.append(item)
    return result


def save_soil_txt(soil_table_data, fields_order, soil_txt_path):
    print("开始生成土壤文件")
    start = time.time()
    text = ''
    for data in soil_table_data:
        for field in fields_order:
            text = text + str(data[field]) + '\t'
        text = text[:-1]
        text = text + '\n'
    text = text[:-1]
    file = open(soil_txt_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()
    end = time.time()
    print("土壤文件生成成功！耗时: %s S" % (end - start))


def get_raster_with_vegetation(vegetation_raster_path, vegetation_in, vegetation_out):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(vegetation_raster_path)
    env.workspace = _path
    # Execute Con
    raster_1 = Raster(vegetation_raster_path)
    raster_2 = Raster(vegetation_in)
    v_out = Con(raster_1 >= 0, raster_1 * 100 + raster_2)
    # Save the outputs
    v_out.save(vegetation_out)


def calculate_vagetation_params(data, out_file_path):
    '''
    from R resource
    '''
    root_pm = ['0.10 0.05 1.00 0.45 5.00 0.50',
               '0.10 0.05 1.00 0.45 5.00 0.50',
               '0.10 0.05 1.00 0.45 5.00 0.50',
               '0.10 0.05 1.00 0.45 5.00 0.50',
               '0.10 0.05 1.00 0.45 5.00 0.50',
               '0.10 0.10 1.00 0.65 1.00 0.25',
               '0.10 0.10 1.00 0.65 1.00 0.25',
               '0.10 0.10 1.00 0.65 0.50 0.25',
               '0.10 0.10 1.00 0.65 0.50 0.25',
               '0.10 0.10 1.00 0.70 0.50 0.20',
               '0.10 0.10 0.75 0.60 0.50 0.30']
    veg_stat = []
    for vegetation_point in data:
        _id = round(vegetation_point['grid_code'] / 100)
        veg_type = vegetation_point['grid_code'] - _id * 100
        item = {}
        item["pointid"] = _id
        item["veg_type"] = veg_type
        veg_stat.append(item)
    veg_stat = sorted(veg_stat, key=lambda veg_stat: veg_stat["pointid"])
    # print(veg_stat)
    vn = 0
    tl = len(veg_stat)
    type_stat = [0] * 11
    out_text = []
    type_list = range(1, 12)
    aban = 0.02  # 面积比例少于百分之二的植被类型不登记
    index = 1
    for i, vegetation_point in enumerate(veg_stat):
        current_id = int(vegetation_point['pointid'])
        tp = int(vegetation_point['veg_type'])
        vn = vn + 1
        if type_list.count(tp) == 1:
            type_stat[tp - 1] = type_stat[tp - 1] + 1
        # don't know why using if
        # if i==tl or
        # print(type_stat)
        type_stat = map(lambda x: x / vn, type_stat)
        type_sum = sum(item > aban for item in type_stat)
        out_line = [str(index), str(type_sum)]
        index = index + 1
        out_text.append('\t'.join(out_line))
        out_text.append('\n')
        for t in range(len(type_list)):
            if type_stat[t] > aban:
                out_line = [str(t + 1), str(round(type_stat[t], 5)), str(root_pm[t])]
                out_text.append('\t'.join(out_line))
                out_text.append('\n')
        type_stat = [0] * 11
        vn = 0

    # print(out_text)
    with open(out_file_path, 'w') as f:
        f.writelines(out_text)


def update_watershed(watershed_path, watershed_centroid_map):
    _area_id = 'area_id'
    CENTROID_X = 'CENTROID_X'
    CENTROID_Y = 'CENTROID_Y'
    Elev = 'Elev'
    ElevMin = 'ElevMin'
    ElevMax = 'ElevMax'
    hru_elev = 'hru_elev'
    X_Centroid = 'X_Centroid'
    Y_Centroid = 'Y_Centroid'
    Lon_Centro = 'Lon_Centro'
    Lat_Centro = 'Lat_Centro'
    Elev_Avg = 'Elev_Avg'
    Basin_Area = 'Basin_Area'
    hruid = 'hruid'
    hru_id = 'hru_id'
    seg_hru_id = 'seg_hru_id'
    Subbasin = 'Subbasin'
    Elev = 'Elev'
    RASTERVALU = "RASTERVALU"
    Area = 'Area'
    area_geo = 'AREA_GEO'
    # 添加字段
    arcDataManagement.add_field(watershed_path, hruid, 'LONG')  # area_id
    arcDataManagement.add_field(watershed_path, hru_id, 'LONG')  # area_id
    arcDataManagement.add_field(watershed_path, seg_hru_id, 'LONG')  # Subbasin
    arcDataManagement.add_field(watershed_path, Elev_Avg, 'DOUBLE')  # Elev
    arcDataManagement.add_field(watershed_path, X_Centroid, 'DOUBLE')  # CENTROID_X
    arcDataManagement.add_field(watershed_path, Y_Centroid, 'DOUBLE')  # CENTROID_Y
    arcDataManagement.add_field(watershed_path, Lon_Centro, 'DOUBLE')  # CENTROID_X
    arcDataManagement.add_field(watershed_path, Lat_Centro, 'DOUBLE')  # CENTROID_Y
    arcDataManagement.add_field(watershed_path, Basin_Area, 'DOUBLE')  # Area
    arcDataManagement.add_field(watershed_path, hru_elev, 'DOUBLE')  # RASTERVALU
    fields = [_area_id, hruid, hru_id, seg_hru_id, Elev_Avg, X_Centroid, Y_Centroid, Lon_Centro, Lat_Centro, Basin_Area,
              hru_elev, Subbasin, Elev, CENTROID_X, CENTROID_Y, Area]
    with arcpy.da.UpdateCursor(watershed_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[0]
            if watershed_centroid_map.has_key(_temp_key):
                item = watershed_centroid_map.get(_temp_key)
                row[fields.index(hru_elev)] = item[RASTERVALU]
            row[fields.index(hruid)] = _temp_key
            row[fields.index(hru_id)] = _temp_key
            row[fields.index(seg_hru_id)] = row[fields.index(Subbasin)]
            row[fields.index(Elev_Avg)] = row[fields.index(Elev)]
            row[fields.index(X_Centroid)] = row[fields.index(CENTROID_X)]
            row[fields.index(Y_Centroid)] = row[fields.index(CENTROID_Y)]
            row[fields.index(Lon_Centro)] = row[fields.index(CENTROID_X)]
            row[fields.index(Lat_Centro)] = row[fields.index(CENTROID_Y)]
            row[fields.index(Basin_Area)] = row[fields.index(Area)]
            cursor.updateRow(row)
    fieldArrays = arcpy.ListFields(watershed_path)
    _to_remove_fields = [_area_id, 'Subbasin', 'Area', 'Lat', 'Long', 'Elev', 'ElevMin', 'ElevMax', area_geo,
                         CENTROID_Y, CENTROID_X]
    for field in _to_remove_fields:
        arcDataManagement.delete_field(watershed_path, field)


def update_river(river_path):
    start_x = 'start_x'
    start_y = 'start_y'
    end_x = 'end_x'
    end_y = 'end_y'
    start_lon = 'start_lon'
    start_lat = 'start_lat'
    end_lat = 'end_lat'
    end_lon = 'end_lon'
    TopElev = 'TopElev'
    BotElev = 'BotElev'
    Length = 'Length'
    seg_id = 'seg_id'
    tosegment = 'tosegment'
    #
    from_area = 'from_area'
    to_area = 'to_area'
    Subbasin = 'Subbasin'
    SubbasinR = 'SubbasinR'
    MinEl = 'MinEl'
    MaxEl = 'MaxEl'
    LENGTH_GEO = 'LENGTH_GEO'
    START_X = 'START_X'
    START_Y = 'START_Y'
    END_X = 'END_X'
    END_Y = 'END_Y'
    MID_X = 'MID_X'
    MID_Y = 'MID_Y'
    START_X_T = 'START_X_T'
    START_Y_T = 'START_Y_T'
    END_X_T = 'END_X_T'
    END_Y_T = 'END_Y_T'

    arcUtils.update_column(river_path, START_X, START_X_T, 'DOUBLE')
    arcUtils.update_column(river_path, START_Y, START_Y_T, 'DOUBLE')
    arcUtils.update_column(river_path, END_X, END_X_T, 'DOUBLE')
    arcUtils.update_column(river_path, END_Y, END_Y_T, 'DOUBLE')
    # 添加字段
    arcDataManagement.add_field(river_path, seg_id, 'LONG')  # Subbasin
    arcDataManagement.add_field(river_path, tosegment, 'LONG')  # SubbasinR
    arcDataManagement.add_field(river_path, BotElev, 'DOUBLE')  # MinEl
    arcDataManagement.add_field(river_path, TopElev, 'DOUBLE')  # MaxEl
    arcDataManagement.add_field(river_path, Length, 'LONG')  # LENGTH_GEO
    arcDataManagement.add_field(river_path, start_x, 'DOUBLE')  # START_X_T
    arcDataManagement.add_field(river_path, start_y, 'DOUBLE')  # START_Y_T
    arcDataManagement.add_field(river_path, end_x, 'DOUBLE')  # END_X_T
    arcDataManagement.add_field(river_path, end_y, 'DOUBLE')  # END_Y_T
    arcDataManagement.add_field(river_path, start_lon, 'DOUBLE')  # START_X_T
    arcDataManagement.add_field(river_path, start_lat, 'DOUBLE')  # START_Y_T
    arcDataManagement.add_field(river_path, end_lon, 'DOUBLE')  # END_X_T
    arcDataManagement.add_field(river_path, end_lat, 'DOUBLE')  # END_Y_T
    fields = [seg_id, tosegment, BotElev, TopElev, Length, start_x, start_y, end_x, end_y, start_lon, start_lat,
              end_lon, end_lat, Subbasin, SubbasinR, MinEl, MaxEl, LENGTH_GEO, START_X_T, START_Y_T, END_X_T,
              END_Y_T]
    with arcpy.da.UpdateCursor(river_path, fields) as cursor:
        for row in cursor:
            row[fields.index(seg_id)] = row[fields.index(Subbasin)]
            row[fields.index(tosegment)] = row[fields.index(SubbasinR)]
            row[fields.index(BotElev)] = row[fields.index(MinEl)]
            row[fields.index(TopElev)] = row[fields.index(MaxEl)]
            row[fields.index(Length)] = row[fields.index(LENGTH_GEO)]
            row[fields.index(start_x)] = row[fields.index(START_X_T)]
            row[fields.index(start_y)] = row[fields.index(START_Y_T)]
            row[fields.index(end_x)] = row[fields.index(END_X_T)]
            row[fields.index(end_y)] = row[fields.index(END_Y_T)]
            row[fields.index(start_lon)] = row[fields.index(START_X_T)]
            row[fields.index(start_lat)] = row[fields.index(START_Y_T)]
            row[fields.index(end_lon)] = row[fields.index(END_X_T)]
            row[fields.index(end_lat)] = row[fields.index(END_Y_T)]
            cursor.updateRow(row)
    fieldArrays = arcpy.ListFields(river_path)
    _to_remove_fields = [from_area, to_area, Subbasin, SubbasinR, MinEl, MaxEl, LENGTH_GEO, MID_X, MID_Y, START_X_T,
                         START_Y_T, END_X_T, END_Y_T]
    for field in _to_remove_fields:
        arcDataManagement.delete_field(river_path, field)


def update_grid(grid_path):
    hru_lat = 'hru_lat'
    hru_long = 'hru_long'
    hru_id = 'hru_id'
    FID = 'FID'
    CENTROID_X = 'CENTROID_X'
    CENTROID_Y = 'CENTROID_Y'
    # 添加字段
    arcDataManagement.add_field(grid_path, hru_lat, 'DOUBLE')  # CENTROID_Y
    arcDataManagement.add_field(grid_path, hru_long, 'DOUBLE')  # CENTROID_X
    arcDataManagement.add_field(grid_path, hru_id, 'LONG')  # FID
    fields = [hru_lat, hru_long, hru_id, CENTROID_X, CENTROID_Y, FID]
    with arcpy.da.UpdateCursor(grid_path, fields) as cursor:
        for row in cursor:
            row[fields.index(hru_id)] = row[fields.index(FID)] + 1
            row[fields.index(hru_long)] = row[fields.index(CENTROID_X)]
            row[fields.index(hru_lat)] = row[fields.index(CENTROID_Y)]
            cursor.updateRow(row)
    fieldArrays = arcpy.ListFields(grid_path)
    _to_remove_fields = [CENTROID_X, CENTROID_Y]
    for field in _to_remove_fields:
        arcDataManagement.delete_field(grid_path, field)


def get_dpt_from_area(sj_list, point_id, seg_id, tosegment):
    """
    根据空间连接情况将防灾对象关联到对应的上游，更新防灾对象的from_node
    """
    start_map = {}
    _map = arcUtils.group_by_key(sj_list, point_id)
    for key in _map:
        _list = _map.get(key)
        if len(_list) > 1:
            start_set = arcUtils.get_id_from_list(_list, seg_id)
            end_set = arcUtils.get_id_from_list(_list, tosegment)
            start_node = list(set(start_set) - set(end_set))
            if len(start_node) > 1:
                raise
            start_map[key] = start_node[0]
        else:
            start_map[key] = _list[0][seg_id]
    return start_map


def update_river_with_dpt(river_path, dpt_from_area, seg_id, tosegment):
    """
    防灾对象作为下游的河段，tosegment 更新成0
    @param river_path: 河道 river.shp
    @param dpt_from_area: 防灾对象 起始点
    @return:
    """
    _values = dpt_from_area.values()
    fields = [seg_id, tosegment]
    with arcpy.da.UpdateCursor(river_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[fields.index(seg_id)]
            if _values.count(_temp_key) == 1:
                row[fields.index(tosegment)] = 0
                cursor.updateRow(row)


def update_dpt_point(dpt_point_path, dpt_from_area, point_id, river):
    """
    更新防灾对象的from_node
    @param dpt_point_path:
    @param dpt_from_area:
    @param river:  from_node 赋值给这个字段
    @return:
    """
    fields = [point_id, river]
    with arcpy.da.UpdateCursor(dpt_point_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[fields.index(point_id)]
            if dpt_from_area.has_key(_temp_key):
                row[fields.index(river)] = dpt_from_area.get(_temp_key)
                cursor.updateRow(row)


def copy_input(input_folder, river_path, watershed_path, grid_path):
    '''
    复制vic用shp
    '''
    new_river_path = input_folder + "/river.shp"
    new_watershed_path = input_folder + "/watershed.shp"
    new_grid_path = input_folder + "/grid.shp"
    arcpy.CopyFeatures_management(river_path, new_river_path)
    arcpy.CopyFeatures_management(watershed_path, new_watershed_path)
    arcpy.CopyFeatures_management(grid_path, new_grid_path)


def create_hrdro_output(file_path, data_list, river):
    text = ''
    for data in data_list:
        text = text + str(data[river])
        text = text + '\n'
        text = text + '-9999'
        text = text + '\n'
    text = text[:-1]
    file = open(file_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()


def create_hrdro_output_id(file_path, data_list, point_id):
    text = ''
    for data in data_list:
        text = text + str(data[point_id])
        text = text + '\n'
    text = text[:-1]
    file = open(file_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()


def create_hrdro_output_2_file_path(file_path, data_list, river):
    text = ''
    for data in data_list:
        text = text + str(data[river]) + '\t' + str(1) + '\n'
    text = text[:-1]
    file = open(file_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()


def generate_grid_file(grid_path, vic_path, _dem):
    data_list = arcUtils.shp_to_dict_list(grid_path, ["hru_lat", "hru_long"])
    # update grid
    _set_json = {}
    _set_json['grid'] = data_list
    _query = {}
    _query['dem'] = _dem
    _query_json = {}
    _query_json['query'] = _query
    _set_query = {}
    _set_query['$set'] = _set_json
    _query_json['set'] = _set_query
    _mongo.update_one('watershed_status', _query_json)
    print("grid 已更新")
    text = ''
    for data in data_list:
        text = text + str(data["hru_lat"]) + '\t' + str(data["hru_long"]) + '\n'
    text = text[:-1]
    file_path = vic_path + "/grid.txt"
    file = open(file_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()


def generate_vic_files(dic_out, river_path, river_break_path, watershed_path, grid_path, dpt_point_path, _dem):
    point_id = 'point_id'
    river = "river"
    # ################# 生成模型需要文件 #################
    hrdro_output_file = "hrdro_output.txt"
    hrdro_output_id_file = "hrdro_output_id.txt"
    hrdro_output_2_file = "hrdro_output2.txt"
    vic_path = dic_out + "/vic"
    _folder.clear_and_create_folder(vic_path)
    vic_out_path = dic_out + "/vic/out"
    _folder.clear_and_create_folder(vic_out_path)
    hrdro_output_file_path = vic_out_path + "/" + hrdro_output_file
    hrdro_output_id_file_path = vic_out_path + "/" + hrdro_output_id_file
    hrdro_output_2_file_path = vic_out_path + "/" + hrdro_output_2_file
    rsvr_village_file_path = vic_path + "/" + "rsvr_village.csv"
    # 1为不打断 ； 2为打断
    jiaohu_folder = vic_path + "/jiaohu"
    jiaohu2_folder = vic_path + "/jiaohu2"
    input_folder = vic_path + "/route/scripts/input"
    input2_folder = vic_path + "/route2/scripts/input"
    #
    soil_and_veg_folder = vic_path + "/params/soil"
    soil_txt_src_path = dic_out + "/soil.txt"
    soil_txt_dest_path = vic_path + "/params/soil/soil.txt"
    veg_param_src_path = dic_out + '/veg_param.txt'
    veg_param_dest_path = vic_path + '/params/veg_param.txt'
    _folder.clear_and_create_folder(soil_and_veg_folder)
    # #################
    # 生成不打断文件夹
    _folder.clear_and_create_folder(input_folder)
    copy_input(input_folder, river_path, watershed_path, grid_path)
    # 生成打断文件夹
    _folder.clear_and_create_folder(input2_folder)
    copy_input(input2_folder, river_break_path, watershed_path, grid_path)
    #  生成防灾对象表 csv
    _dpt_list = arcUtils.shp_to_dict_list(dpt_point_path, ['STNAME', 'STCD', river, point_id])
    arcUtils.save_file(_dpt_list, ['STNAME', 'STCD', river, point_id], rsvr_village_file_path, ',', with_header=True)
    #  生成 hrdro_output.txt , hrdro_output_id.txt
    create_hrdro_output(hrdro_output_file_path, _dpt_list, river)
    create_hrdro_output_id(hrdro_output_id_file_path, _dpt_list, point_id)
    # 折减系数文件（默认使用 1）
    create_hrdro_output_2_file_path(hrdro_output_2_file_path, _dpt_list, river)
    # 复制 /vic/out 到 两个 jiaohu 文件夹里
    arcUtils.copy_folder(vic_out_path, jiaohu_folder)
    arcUtils.copy_folder(vic_out_path, jiaohu2_folder)
    qobs_rows = arcUtils.get_rows(river_path)
    qobs_memo_file_name = vic_path + "/qobs_" + str(qobs_rows) + "_rows.txt"
    arcUtils.create_empty_file(qobs_memo_file_name)
    # update qobs rows
    # 初始化配置解析器
    config = configparser.ConfigParser()
    # 读取现有的配置文件，如果不存在则会创建一个新的
    config_file_path = 'config.ini'
    config.read(config_file_path)
    # 添加或更新配置节和键值对
    if 'QOBS' not in config.sections():
        config.add_section('QOBS')
    config.set('QOBS', 'qobs_rows', str(qobs_rows))
    # 将配置写回文件
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)
    print("qobs_rows 已保存到 {}".format(config_file_path))
    generate_grid_file(grid_path, vic_path, _dem)
    # 复制土壤植被参数
    arcUtils.copy_file(soil_txt_src_path, soil_txt_dest_path)
    arcUtils.copy_file(veg_param_src_path, veg_param_dest_path)


def get_unintersect_loc(intersect_loc, grid_loc, CENTROID_X, CENTROID_Y):
    x_set = arcUtils.get_id_from_list(intersect_loc, CENTROID_X)
    y_set = arcUtils.get_id_from_list(intersect_loc, CENTROID_Y)
    x_set_all = arcUtils.get_id_from_list(grid_loc, CENTROID_X)
    y_set_all = arcUtils.get_id_from_list(grid_loc, CENTROID_Y)
    x_diff = list(set(x_set_all) - set(x_set))
    y_diff = list(set(y_set_all) - set(y_set))
    return x_diff, y_diff


def clip_grid(grid_path, grid_clip_path, x_diff, CENTROID_X, y_diff, CENTROID_Y):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _input_file = s.split(grid_path)
    env.workspace = _path
    _path_temp, _output_file = s.split(grid_clip_path)
    sr = arcpy.Describe(grid_path).spatialReference
    create_file = arcpy.CreateFeatureclass_management(_path, _output_file, template=_input_file, spatial_reference=sr)
    _search_cursor = arcpy.SearchCursor(grid_path)
    _insert_cursor = arcpy.InsertCursor(grid_clip_path)
    for row in _search_cursor:
        if len(x_diff) > 0:
            if x_diff.count(row.getValue(CENTROID_X)) == 1:
                continue
        if len(y_diff) > 0:
            if y_diff.count(row.getValue(CENTROID_Y)) == 1:
                continue
        _insert_cursor.insertRow(row)


def update_dpt_point_without_river(dpt_point_path, field):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, input_file = s.split(dpt_point_path)
    env.workspace = _path
    sr = arcpy.Describe(dpt_point_path).spatialReference
    #
    section_null = dpt_point_path.replace('.shp', '_nul.shp')
    create_file_section_null = arcpy.CreateFeatureclass_management(_path, s.getName(section_null), template=input_file,
                                                                   spatial_reference=sr)
    search_null_cursor = arcpy.SearchCursor(dpt_point_path, field + '= 0')
    insert_cursor_null = arcpy.InsertCursor(create_file_section_null)
    for row in search_null_cursor:
        insert_cursor_null.insertRow(row)
    #
    section_null_map = arcUtils.to_map(section_null, "point_id")
    if len(section_null_map.keys()) == 0:
        return
        #
    section_non_null = dpt_point_path.replace('.shp', '_non_nul.shp')
    create_file_section_non_null = arcpy.CreateFeatureclass_management(_path, s.getName(section_non_null),
                                                                       template=input_file,
                                                                       spatial_reference=sr)
    search_non_null_cursor = arcpy.SearchCursor(dpt_point_path, field + '<> 0')
    insert_cursor_non_null = arcpy.InsertCursor(create_file_section_non_null)
    for row in search_non_null_cursor:
        insert_cursor_non_null.insertRow(row)
    point_id = "point_id"
    section_non_null_map = arcUtils.to_map(section_non_null)
    # near
    arcpy.Near_analysis(section_null, section_non_null)
    section_null_map = arcUtils.to_map(section_null, point_id)
    arcpy.AddField_management(dpt_point_path, "use_near", "TEXT", field_is_nullable="NULLABLE")
    NEAR_FID = 'NEAR_FID'
    fields = [field, point_id, "use_near"]
    with arcpy.da.UpdateCursor(dpt_point_path, fields, where_clause=field + ' = 0') as cursor:
        for row in cursor:
            near_id = section_null_map.get(row[fields.index(point_id)]).get(NEAR_FID)
            value = section_non_null_map.get(near_id).get(field)
            row[fields.index(field)] = value
            row[fields.index("use_near")] = 'true'
            cursor.updateRow(row)


def main():

    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini')
    _basin_name = config.get('general', 'basin_name')  # dem
    _precision = config.get('general', 'gridsize')
    _avg_rain = config.get('calculate_soil', 'avg_rain')

    # 指定保存文件的路径
    _workspace_path = os.path.dirname(os.path.abspath(__file__))
    save_file = "data.pkl"
    save_path = os.path.join(_workspace_path, 'data', save_file)
    # 读取字典
    with open(save_path, "rb") as f:
        dem = pickle.load(f)
    print(dem)

    # 工作空间路径
    _calculate_path = os.path.join(_workspace_path, 'data', 'watershed', _basin_name, 'calculate')
    _layer_path = dem[0]["layer_path"]
    _workspace_path_dem_layer_path = os.path.join(_workspace_path + _layer_path)
    _result_junction = os.path.join(_workspace_path, 'data', 'watershed', _basin_name, 'calculate')
    dic_out = _calculate_path

    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0
    # ################# 字符串常量 #################
    _area_id = 'area_id'
    MU_GLOBAL = 'MU_GLOBAL'
    SoilID = "SoilID"
    RASTERVALU = "RASTERVALU"
    CENTROID_X = 'CENTROID_X'
    CENTROID_Y = 'CENTROID_Y'
    point_id = 'point_id'
    seg_id = "seg_id"
    river = "river"
    tosegment = "tosegment"
    # ################# 路径常量 #################
    soil_in = os.path.join(_workspace_path, 'data', 'china_soil_texture_1m', 'chinanewsoil')  # 土壤文件
    vegetation_in = os.path.join(_workspace_path, 'data', 'umd_1km')
    soil_db_path = os.path.join(_workspace_path, 'data', 'china_soil_texture_1m', 'HWSD.mdb')
    soil_info_table = soil_db_path + '/HWSD_DATA'
    temp_db_path = os.path.join(dic_out, "Default.gdb")
    watershed_tif = os.path.join(dic_out, "watershed.tif")  # 集水区文件 (DEM)
    watershed_tif_clip = os.path.join(_workspace_path + dem[0]["clip_dem_path"])  # 区域dem
    # watershed_tif_clip_temp = os.path.join(_workspace_path_dem_layer_path, '投影.tif')  ## 有问题的
    watershed_path = os.path.join(dic_out, "watershed.shp")
    watershed_bak_path = watershed_path.replace('.shp', '_bak.shp')
    watershed_centroid_path = watershed_path.replace('.shp', '_centroid.shp')
    river_path = os.path.join(dic_out, "river.shp")  # 河道不打断
    river_break_path = os.path.join(dic_out, "river_break.shp")  # 河道打断
    river_bak_path = river_path.replace('.shp', '_bak.shp')
    basin_path = os.path.join(dic_out, "basin.shp")  # 流量边界矢量文件 basin.shp
    grid_path = os.path.join(dic_out, "grid.shp")
    grid_bak_path = grid_path.replace('.shp', '_bak.shp')
    grid_clip_path = os.path.join(dic_out, "grid_clip.shp")
    basin_raster_path = os.path.join(dic_out, 'basin_clip.tif')
    vegetation_raster_path = os.path.join(dic_out, 'basin_raster.tif')
    vegetation_raster_out = os.path.join(dic_out, 'vegetation_raster.tif')
    vegetation_point_out = os.path.join(dic_out, 'vegetation_point.shp')
    veg_param_path = os.path.join(dic_out, 'veg_param.txt')
    basin_point_path = os.path.join(dic_out, 'basin_clip.shp')
    basin_point_bak_path = basin_point_path.replace('.shp', '_bak.shp')
    basin_point_path_with_elev = basin_point_path.replace('.shp', '_elev.shp')
    basin_point_path_soil_clip = basin_point_path.replace('.shp', '_soil.shp')
    soil_clip = os.path.join(dic_out, "soil.tif")
    vegetation_clip = os.path.join(dic_out, "vegetation.tif")
    soil_txt_path = os.path.join(dic_out, "soil.txt")
    dpt_point_path = os.path.join(_workspace_path, 'data', 'point', _basin_name, 'pour_point_dpt.shp')
    spatial_join_path = os.path.join(dic_out, "sj_dpt_point_river.shp")
    sj_basin_grid = os.path.join(dic_out, "sj_basin_grid.shp")
    sj_grid_basin = os.path.join(dic_out, "sj_grid_basin.shp")
    all_area_path = os.path.join(dic_out, "all_area.shp")
    global_shp_path = os.path.join(_workspace_path_dem_layer_path, "global.shp")
    # ################# start logic ##############
    raster_exist = os.path.exists(basin_raster_path)
    if raster_exist:
        # 分两种情况获取点文件
        # 定义投影
        arcProjection.define_projection(basin_raster_path, 4326)
        # 栅格转点
        arcpy.RasterToPoint_conversion(basin_raster_path, basin_point_path, "VALUE")
        # arcConvert.raster_to_point(basin_raster_path, basin_point_path)  # 以同名的矢量文件保存
    # 保存原始状态
    arcpy.CopyFeatures_management(basin_point_path, basin_point_bak_path)
    # 值提取至点（区域dem）（高程）
    arcSpatialAnalyst.extract_values_to_points(basin_point_path, watershed_tif_clip)
    # 保存原始状态
    arcpy.CopyFeatures_management(basin_point_path, basin_point_path_with_elev)
    arcUtils.update_column(basin_point_path, RASTERVALU, "ELEV", 'LONG')
    # 土壤
    # 切割区域土壤
    arcDataManagement.clip_shp(soil_in, soil_clip, global_shp_path)
    # 值提取至点（区域土壤）
    arcSpatialAnalyst.extract_values_to_points(basin_point_path, soil_clip)
    # 保存原始状态
    arcpy.CopyFeatures_management(basin_point_path, basin_point_path_soil_clip)
    arcUtils.update_column(basin_point_path, RASTERVALU, SoilID, 'LONG')
    # 添加连接
    arcDataManagement.add_join(basin_point_path, SoilID, soil_info_table, MU_GLOBAL, qualified_field_names=False)
    # 添加几何属性
    arcpy.AddGeometryAttributes_management(basin_point_path, "POINT_X_Y_Z_M")
    arcUtils.copy_column(basin_point_path, "POINT_X", 'LNG', 'DOUBLE')
    arcUtils.copy_column(basin_point_path, "POINT_Y", 'LAT', 'DOUBLE')
    soil_table_check_fields = ['pointid', SoilID, 'T_SAND', 'T_CLAY', 'T_OC', 'S_SAND', 'S_CLAY', 'S_OC']
    check_properties(basin_point_path, soil_table_check_fields)
    soil_table_fields = [SoilID, 'T_SAND', 'T_CLAY', 'S_SAND', 'S_CLAY']
    soil_table_list = arcUtils.shp_to_dict_list(basin_point_path, soil_table_fields)
    soil_type_map = arcUtils.list_to_map(soil_table_list, SoilID)
    statistics_soil_type(soil_type_map, _data.soil_type_data_to_hydraulic_parameter,
                         _data.soil_type_data)
    _arr = arcUtils.shp_to_array(basin_point_path, soil_table_check_fields)
    soil_params = get_soil_params(_arr)
    basin_point_fields = [SoilID, 'pointid', 'LNG', 'LAT', 'ELEV']
    basin_point_list = arcUtils.shp_to_dict_list(basin_point_path, basin_point_fields)
    soil_table_data = create_soil_table(basin_point_list, soil_type_map, soil_params, _avg_rain)
    fields_order = ["RUN", "GRID", "LAT", "LNG", "lNFlLT", "Ds", "Ds_MAX", "Ws", "C", "EXPT_1", "EXPT_2", "EXPT_3",
                    "Ksat_1", "Ksat_2", "Ksat_3", "PHI_1", "PHI_2", "PHI_3", "MOIST_1", "MOIST_2", "MOIST_3", "ELEV",
                    "DEPTH_1", "DEPTH_2", "DEPTH_3", "AVG_T", "DP", "BUBLE1", "BUBLE2", "BUBLE3", "QUARZ1", "QUARZ2",
                    "QUARZ3", "BULKDN1", "BULKDN2", "BULKDN3", "PARTDN1", "PARTDN2", "PARTDN3", "OFF_GMT", "WcrFT1",
                    "WcrFT2", "WcrFT3", "WpFT1", "WpFT2", "WpFT3", "Z0_SOIL", "Z0_SNOW", "PRCP", "RESM1", "RESM2",
                    "RESM3", "FS_ACTV"]
    save_soil_txt(soil_table_data, fields_order, soil_txt_path)
    # 植被
    # 点转栅格
    arcConvert.point_to_raster(basin_point_path, 'pointid', vegetation_raster_path, cellsize=_precision)
    # 栅格计算器
    get_raster_with_vegetation(vegetation_raster_path, vegetation_in, vegetation_raster_out)
    # 栅格转点
    arcConvert.raster_to_point(vegetation_raster_out, vegetation_point_out)
    fields_vegetation = ['pointid', 'grid_code']
    vegetation_point_list = arcUtils.shp_to_dict_list(vegetation_point_out, fields_vegetation)
    calculate_vagetation_params(vegetation_point_list, veg_param_path)
    ### watershed
    # 备份原始状态
    arcpy.CopyFeatures_management(watershed_path, watershed_bak_path)
    arcUtils.area_to_point(watershed_path, watershed_centroid_path, 'CENTROID_X', 'CENTROID_Y', _area_id)
    # 值提取至点
    arcSpatialAnalyst.extract_values_to_points(watershed_centroid_path, watershed_tif_clip)
    watershed_centroid_map = arcUtils.to_map(watershed_centroid_path, _area_id)
    update_watershed(watershed_path, watershed_centroid_map)
    ### river
    # 保存原始状态
    arcpy.CopyFeatures_management(river_path, river_bak_path)
    # # 添加几何属性
    arcpy.AddGeometryAttributes_management(river_path, "LINE_START_MID_END")
    arcpy.AddGeometryAttributes_management(river_path, "LENGTH_GEODESIC", "METERS")
    update_river(river_path)
    # river 防灾对象
    arcDataManagement.add_field(dpt_point_path, point_id, 'LONG')
    arcUtils.update_field_by_order(dpt_point_path, point_id)
    arcAnalysis.spatial_join(dpt_point_path, river_path, spatial_join_path, match_option="INTERSECT",
                             join_operation="JOIN_ONE_TO_MANY")
    sj_list = arcUtils.shp_to_dict_list(spatial_join_path, [point_id, seg_id, tosegment])
    dpt_from_area = get_dpt_from_area(sj_list, point_id, seg_id, tosegment)
    sj_list_rsvr = arcUtils.shp_to_dict_list_filter(spatial_join_path, 'TYPE', 'RESERVOIR',
                                                    [point_id, seg_id, tosegment])
    rsvr_from_area = get_dpt_from_area(sj_list_rsvr, point_id, seg_id, tosegment)
    # 防灾对象不打断 --river_path
    arcpy.CopyFeatures_management(river_path, river_break_path)
    # 防灾对象打断(水库)
    update_river_with_dpt(river_break_path, rsvr_from_area, seg_id, tosegment)
    arcpy.AddField_management(dpt_point_path, river, 'LONG', field_is_nullable="NULLABLE")
    update_dpt_point(dpt_point_path, dpt_from_area, point_id, river)
    update_dpt_point_without_river(dpt_point_path, river)
    ###  grid
    if raster_exist:
        arcDataManagement.create_fishnet_by_raster(grid_path, basin_raster_path, _precision, _precision,
                                                   geometry_type="POLYGON")
    else:
        _precision_num = len(str(_precision).split(".")[1])
        _precision_num = _precision_num + 1
        arcDataManagement.create_fishnet(grid_path, all_area_path, _precision, _precision, _precision_num,
                                         geometry_type="POLYGON")
    # 保存原始状态
    arcpy.CopyFeatures_management(grid_path, grid_bak_path)
    # 裁剪grid
    arcpy.AddGeometryAttributes_management(grid_path, "CENTROID")
    arcAnalysis.spatial_join(grid_path, basin_path, sj_grid_basin,
                             match_option="INTERSECT", join_operation="JOIN_ONE_TO_ONE")
    intersect_loc = arcUtils.shp_to_dict_list_ignore_null(sj_grid_basin, 0, [CENTROID_X, CENTROID_Y], 'Join_Count')
    grid_loc = arcUtils.shp_to_dict_list(grid_path, [CENTROID_X, CENTROID_Y])
    #
    x_diff, y_diff = get_unintersect_loc(intersect_loc, grid_loc, CENTROID_X, CENTROID_Y)
    clip_grid(grid_path, grid_clip_path, x_diff, CENTROID_X, y_diff, CENTROID_Y)
    update_grid(grid_clip_path)
    # 生成vic文件
    generate_vic_files(dic_out, river_path, river_break_path, watershed_path, grid_clip_path, dpt_point_path, _basin_name)


def break_point_flg():
    pass


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
