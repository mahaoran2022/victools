# -*- coding: UTF-8 -*-
import sys
import os.path
import shutil
# import pdb
import pickle
import time
import configparser
from arcpy import env
import arcpy
# print(dir(arcpy))
import common.arcConvert as arcConvert
import common.constant as constant
import common.sp as s
import common.folder as _folder
import common.arcAnalysis as arcAnalysis
import common.arcDataManagement as arcDataManagement
import common.arcSpatialAnalyst as arcSpatialAnalyst
import common.arcUtils as arcUtils


def get_dpt_point(_input_path, _output_path, _type_key, _type_list):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _input_file = s.split(_input_path)
    env.workspace = _path
    _path_temp, _output_file = s.split(_output_path)
    sr = arcpy.Describe(_input_path).spatialReference
    create_file = arcpy.CreateFeatureclass_management(_path, _output_file, template=_input_file, spatial_reference=sr)
    _search_cursor = arcpy.SearchCursor(_input_path)
    _insert_cursor = arcpy.InsertCursor(_output_path)
    for row in _search_cursor:
        if _type_list.count(row.getValue(_type_key)) == 1:
            _insert_cursor.insertRow(row)
    print("提取防灾对象成功")


def assign_river_area_by_length(is_line_area_data, _river_fid_new,
                                _area_id_new,
                                length_key):
    # group by river fid , find the longest data
    # river :[area:length]
    line_map = {}
    for item in is_line_area_data:
        _key_river = item[_river_fid_new]
        _key_area = item[_area_id_new]
        if not line_map.has_key(_key_river):
            line_map[_key_river] = {}
        line_map[_key_river][_key_area] = item[length_key]
    # river:area
    line_startArea_map = {}
    line_interArea_map = {}
    for _key in line_map.keys():
        _intersect_areas = line_map.get(_key)
        _inner_keys = _intersect_areas.keys()
        if len(_inner_keys) == 1:
            temp_dict = {}
            temp_dict[_inner_keys[0]] = _intersect_areas[_inner_keys[0]]
            line_startArea_map[_key] = temp_dict
            line_map.pop(_key)
            continue
        else:
            selected = {}
            temp_length = 0
            for _inner_key in _inner_keys:
                length = _intersect_areas[_inner_key]
                diff = abs(length - temp_length)
                same_flg = diff < 0.01
                if not same_flg and length < temp_length:
                    continue
                if not same_flg:
                    temp_length = length
                    selected.clear()
                selected[_inner_key] = length
            selected_keys = selected.keys()
            if len(selected_keys) == 1:
                temp_dict = {}
                temp_dict[selected_keys[0]] = selected[selected_keys[0]]
                line_startArea_map[_key] = temp_dict
            else:
                # 添加到第二轮筛选
                line_interArea_map[_key] = selected
    return line_startArea_map, line_interArea_map


def assign_river_area_by_startpoint(line_startArea_map, line_interArea_map, sj_startpoint_watershed_path,
                                    _river_fid_new,
                                    _area_id_new, length_key):
    select_keyset = line_interArea_map.keys()
    rows = arcpy.SearchCursor(sj_startpoint_watershed_path)
    data_list = []
    for row in rows:
        lineId = row.getValue(_river_fid_new)
        if select_keyset.count(lineId) == 1:
            item = {}
            item[_area_id_new] = row.getValue(_area_id_new)
            item[_river_fid_new] = lineId
            data_list.append(item)
    for data in data_list:
        item = {}
        item[data[_area_id_new]] = 0
        line_startArea_map[data[_river_fid_new]] = item


def get_is_watershed_table(intersect_watershed_ori, _area_id_new, _join_area_id_new, length_key):
    is_watershed_table = []
    rows = arcpy.SearchCursor(intersect_watershed_ori)
    for row in rows:
        left_id = row.getValue(_area_id_new)
        right_id = row.getValue(_join_area_id_new)
        if left_id == right_id:
            continue
        item = {}
        item[_area_id_new] = left_id
        item[_join_area_id_new] = right_id
        item[length_key] = row.getValue(length_key)
        is_watershed_table.append(item)
    return is_watershed_table


def group_by_watershed(line_startArea_map, is_line_area_data, space_list, _river_fid_new, _area_id_new, _end_x, _end_y):
    space_map = {}
    for space in space_list:
        _key_area = space[_river_fid_new]
        space_map[_key_area] = space
    area_set = []
    duplicated_set = []
    assigned_line = []
    for _line in line_startArea_map.keys():
        startArea = line_startArea_map.get(_line)
        _item = startArea.keys()[0]
        assigned_line.append(_line)
        if area_set.count(_item) > 0:
            duplicated_set.append(_item)
            assigned_line.remove(_line)
        area_set.append(_item)
    # assigned_area = list(set(area_set) - set(duplicated_set))
    area_map = {}
    line_map = {}
    for data in is_line_area_data:
        _key_area = data[_area_id_new]
        _key_line = data[_river_fid_new]
        if duplicated_set.count(_key_area) > 0:
            if not area_map.has_key(_key_area):
                area_map[_key_area] = []
            area_map[_key_area].append(_key_line)
        if not line_map.has_key(_key_line):
            line_map[_key_line] = []
        line_map[_key_line].append(_key_area)
    # [areaId:riverFid]
    intersect_point_one_area = []
    # [areaId:[riverFid]]
    intersect_point_two_area = []
    intersect_point_two_area_no_assigned = []
    for _key_area in area_map.keys():
        lines = area_map.get(_key_area)
        if len(lines) > 2:
            _set = []
            _duplicated_set = []
            loc_line_list = []
            for lineId in lines:
                line = space_map.get(lineId)
                line_key = str(line[_end_x]) + "_" + str(line[_end_y])
                if _set.count(line_key) > 0:
                    _duplicated_set.append(line_key)
                _set.append(line_key)
                loc_line_list.append({line_key: line[_river_fid_new]})
            _duplicated_set = list(set(_duplicated_set))
            length = len(_duplicated_set)
            if length == 1:
                for loc_line in loc_line_list:
                    _line = loc_line.values()[0]
                    if loc_line.keys()[0] == _duplicated_set[0]:
                        if assigned_line.count(_line) == 0 or (
                                len(line_map.get(_line)) == 1 and line_map.get(_line)[0] == _key_area):
                            intersect_point_one_area.append({_key_area: loc_line.values()[0]})
            elif length == 2:
                # pdb.set_trace()
                for loc_line in loc_line_list:
                    _line = loc_line.values()[0]
                    if loc_line.keys()[0] == _duplicated_set[0]:
                        if assigned_line.count(_line) == 0 or (
                                len(line_map.get(_line)) == 1 and line_map.get(_line)[0] == _key_area):
                            intersect_point_two_area_no_assigned.append({_key_area: loc_line.values()[0]})
                intersect_point_two_area.append({_key_area: lines})
    return intersect_point_one_area, intersect_point_two_area, intersect_point_two_area_no_assigned


def group_by_line(space_list_intersect, _river_fid_new, _area_id_new):
    # line:[{area:loc}]
    space_list_map = {}
    for data in space_list_intersect:
        _key = data[_river_fid_new]
        if not space_list_map.has_key(_key):
            space_list_map[_key] = []
        space_list_map[_key].append({data[_area_id_new]: data})
    return space_list_map


def group_by_end_loc(space_list, _river_fid_new, _end_x, _end_y):
    locEnd_line_map = {}
    for data in space_list:
        line_key = str(data[_end_x]) + "_" + str(data[_end_y])
        if not locEnd_line_map.has_key(line_key):
            locEnd_line_map[line_key] = []
        locEnd_line_map[line_key].append(data[_river_fid_new])
    return locEnd_line_map


def loc_group_by_river(space_list, _river_fid_new):
    space_map = {}
    for line in space_list:
        space_map[line[_river_fid_new]] = line
    return space_map


def deal_one_intersect_watershed(is_line_area_data, intersect_point_one_area, line_area_sj_list, line_startArea_map,
                                 locEnd_line_map,
                                 space_map, _river_fid_new, _area_id_new, _start_x, _start_y):
    """
    @param is_line_area_data:  [area-line相交长度]
    @param intersect_point_one_area: [areaId:riverFid]
    @param line_area_sj_list:[spacejoin-line-area]
    @param line_startArea_map:
    @param locEnd_line_map: end_loc :[lineFid]
    @param space_map: river_fid: [loc]
    """
    print("intersect_point_one_area")
    print(intersect_point_one_area)
    # pdb.set_trace()
    # 等待分配的河道
    lines_to_assign = {}
    lines_to_assign_keys = []
    for data in intersect_point_one_area:
        lines_to_assign[data.values()[0]] = data.keys()[0]
        lines_to_assign_keys.append(data.values()[0])
    # group by line
    # 相交表
    line_map = {}
    for data in line_area_sj_list:
        _key = data[_river_fid_new]
        if lines_to_assign_keys.count(_key) == 1:
            if not line_map.has_key(_key):
                line_map[_key] = []
            line_map[_key].append(data[_area_id_new])
    # group by line all
    # 分割表
    line_map_intersect_all = {}
    for data in is_line_area_data:
        _key = data[_river_fid_new]
        if not line_map_intersect_all.has_key(_key):
            line_map_intersect_all[_key] = []
        line_map_intersect_all[_key].append(data[_area_id_new])
    for _key in line_map.keys():
        _map = line_map.get(_key)
        if len(_map) == 2 and lines_to_assign.has_key(_key):
            area_old = lines_to_assign.get(_key)
            _map.remove(area_old)
            item = {}
            item[_map[0]] = 0
            line_startArea_map[_key] = item
            line_map.pop(_key)
    # river_fid:[area_id]
    line_sept_map = {}
    for item in is_line_area_data:
        _key_river = item[_river_fid_new]
        _key_area = item[_area_id_new]
        if line_map.has_key(_key_river):
            if not line_sept_map.has_key(_key_river):
                line_sept_map[_key_river] = []
            line_sept_map[_key_river].append(_key_area)
    line_sept_one = []
    line_sept_two = []
    line_sept_more = []
    for _key in line_sept_map.keys():
        _list = line_sept_map.get(_key)
        if len(_list) == 1:
            line_sept_one.append(_key)
        if len(_list) == 2:
            # todo
            line_sept_two.append(_key)
        if len(_list) > 2:
            # todo
            line_sept_more.append(_key)
    # 查找线的上游连接点并赋值
    for _line in line_sept_one:
        line = space_map.get(_line)
        line_key = str(line[_start_x]) + "_" + str(line[_start_y])
        if not locEnd_line_map.has_key(line_key):
            raise
        upstream = locEnd_line_map.get(line_key)
        if len(upstream) > 1:
            raise
        areas_of_upstream = line_map_intersect_all.get(upstream[0])
        self_areas = line_map.get(_line)
        assign_area = list(set(areas_of_upstream) & set(self_areas))
        if len(assign_area) != 1:
            raise
        item = {}
        item[assign_area[0]] = 0
        line_startArea_map[_line] = item
        line_map.pop(_line)
    print("line_map")
    print(line_map)
    # pdb.set_trace()
    print("如果不为空，则没有分割完成，需要继续计算")
    print("********************")


def deal_two_intersect_watershed(intersect_point_two_area, intersect_point_two_area_no_assigned, line_startArea_map,
                                 space_map,
                                 _river_fid_new, _area_id_new, _start_x, _start_y, _end_x, _end_y, is_line_area_data,
                                 line_area_sj_list, locEnd_line_map, space_list_map):
    no_assigned_map_area_line = {}
    for dict in intersect_point_two_area_no_assigned:
        _key = dict.keys()[0]
        _value = dict.values()[0]
        if not no_assigned_map_area_line.has_key(_key):
            no_assigned_map_area_line[_key] = []
            no_assigned_map_area_line[_key].append(_value)

    for area_map in intersect_point_two_area:
        areaId = area_map.keys()[0]
        lines = area_map.values()[0]
        end_map = {}
        start_map = {}
        for lineId in lines:
            line = space_map.get(lineId)
            line_key_end = str(line[_end_x]) + "_" + str(line[_end_y])
            line_key_start = str(line[_start_x]) + "_" + str(line[_start_y])
            end_map[line_key_end] = lineId
            start_map[line_key_start] = lineId
        up_line = list(set(start_map.keys()) - set(end_map.keys()))
        up_streams = []
        for _item in up_line:
            up_streams.append(start_map.get(_item))
        down_line = list(set(end_map.keys()) - set(start_map.keys()))
        down_stream = end_map.get(down_line[0])
        intersect_point_one_area = []
        # pdb.set_trace()
        _temp_list = []
        if no_assigned_map_area_line.has_key(areaId):
            _temp_list = no_assigned_map_area_line.get(areaId)
        if len(_temp_list) > 0:
            for upnode in up_streams:
                if _temp_list.count(upnode) > 0:
                    intersect_point_one_area.append({areaId: upnode})
        if len(intersect_point_one_area) > 0:
            # print("line_startArea_map in two before")
            # print(line_startArea_map)
            # print("********************")
            deal_one_intersect_watershed(is_line_area_data, intersect_point_one_area, line_area_sj_list,
                                         line_startArea_map,
                                         locEnd_line_map,
                                         space_map, _river_fid_new, _area_id_new, _start_x, _start_y)
            # print("line_startArea_map in two after")
            # print(line_startArea_map)
            # print("********************")
        # deal down node
        _temp_list = space_list_map.get(down_stream)
        line_map = {}
        for _item in _temp_list:
            if _item.keys().count(areaId) == 0:
                datum = _item.values()[0]
                line_key = str(datum[_start_x]) + "_" + str(datum[_start_y])
                line_map[line_key] = datum[_area_id_new]
        for _item in _temp_list:
            if _item.keys().count(areaId) == 1:
                datum = _item.values()[0]
                line_key = str(datum[_end_x]) + "_" + str(datum[_end_y])
                new_area = line_map.get(line_key)
                temp_dict = {}
                temp_dict[new_area] = 0
                line_startArea_map[down_stream] = temp_dict


def update_river(split_line_out, line_startArea_map, _river_fid_new, _river_new_field_from_area):
    fields = [_river_fid_new, _river_new_field_from_area]
    with arcpy.da.UpdateCursor(split_line_out, fields) as cursor:
        for row in cursor:
            _temp_key = row[0]
            if line_startArea_map.has_key(_temp_key):
                row[1] = line_startArea_map.get(_temp_key).keys()[0]
            cursor.updateRow(row)


def update_watershed(watershed_ori_path, replace_map, _area_id_new):
    fields = [_area_id_new]
    with arcpy.da.UpdateCursor(watershed_ori_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[0]
            if replace_map.has_key(_temp_key):
                row[0] = replace_map.get(_temp_key)
            cursor.updateRow(row)


def create_tree(river_path, _river_new_field_from_area, _river_new_field_to_area, _start_x, _start_y, _end_x,
                _end_y):
    # 添加几何属性
    arcpy.AddGeometryAttributes_management(river_path, "LINE_START_MID_END")
    # 添加字段
    arcDataManagement.add_field(river_path, _river_new_field_to_area, 'LONG')
    basinMap = {}
    search_cursor = arcpy.SearchCursor(river_path)
    for row in search_cursor:
        _temp_key = str(row.getValue(_start_x)) + "_" + str(row.getValue(_start_y))
        basinMap[_temp_key] = row.getValue(_river_new_field_from_area)
    fields = ["FID", _river_new_field_to_area, _start_x, _start_y, _end_x,
              _end_y]
    with arcpy.da.UpdateCursor(river_path, fields) as cursor:
        for row in cursor:
            _temp_key = str(row[4]) + "_" + str(row[5])
            if basinMap.has_key(_temp_key):
                row[1] = basinMap[_temp_key]
            cursor.updateRow(row)
    _to_remove_fields = ['START_X', 'START_Y', 'MID_X', 'MID_Y', 'END_X', 'END_Y']
    for field in _to_remove_fields:
        arcDataManagement.delete_field(river_path, field)
    print("河网节点更新成功！")


def sept_shp_null(input_path, property, section_null, section_non_null):
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, input_file = s.split(input_path)
    env.workspace = _path
    sr = arcpy.Describe(input_path).spatialReference
    #
    create_file_section_null = arcpy.CreateFeatureclass_management(_path, s.getName(section_null), template=input_file,
                                                                   spatial_reference=sr)
    search_null_cursor = arcpy.SearchCursor(input_path, property + ' = 0')
    insert_cursor_null = arcpy.InsertCursor(create_file_section_null)
    for row in search_null_cursor:
        insert_cursor_null.insertRow(row)
    #
    create_file_section_non_null = arcpy.CreateFeatureclass_management(_path, s.getName(section_non_null),
                                                                       template=input_file,
                                                                       spatial_reference=sr)
    search_non_null_cursor = arcpy.SearchCursor(input_path, property + ' <> 0')
    insert_cursor_non_null = arcpy.InsertCursor(create_file_section_non_null)
    for row in search_non_null_cursor:
        insert_cursor_non_null.insertRow(row)
    print("sept_shp_null")


def get_null_intersect_non_null(is_watershed_table, null_area_ids, non_null_area_ids, _area_id_new, _join_area_id_new,
                                length_key):
    join_map = {}
    for row in is_watershed_table:
        left = row[_area_id_new]
        right = row[_join_area_id_new]
        if null_area_ids.count(left) == 0 or non_null_area_ids.count(right) == 0:
            continue
        if not join_map.has_key(left):
            join_map[left] = {}
        join_map[left][row[length_key]] = right
    null_non_map = {}
    for _key in join_map.keys():
        neighbour_dict = join_map.get(_key)
        length_list = neighbour_dict.keys()
        length_list.sort(reverse=True)
        _length = length_list[0]
        null_non_map[_key] = neighbour_dict.get(_length)
    return null_non_map


def group_by_from_area(area_line_spatial_join_list, area_line_intersect_list, from_area_all,
                       _area_id_new,
                       _river_new_field_from_area,
                       _river_new_field_to_area):
    # 相同起点的河道 空间连接 相交多少面
    from_node_map_sj = {}
    # 按面分组
    area_id_map = {}
    for _item in area_line_spatial_join_list:
        key = _item[_river_new_field_from_area]
        if not from_node_map_sj.has_key(key):
            from_node_map_sj[key] = []
        from_node_map_sj[key].append(_item[_area_id_new])
        #
        key_1 = _item[_area_id_new]
        if not area_id_map.has_key(key_1):
            area_id_map[key_1] = []
        area_id_map[key_1].append(_item)
    templist = {}
    for _key in from_node_map_sj:
        _list = from_node_map_sj.get(_key)
        if len(_list) == 1:
            continue
        _list = list(set(_list) - set(from_area_all))
        if len(_list) > 0:
            for area in _list:
                if not templist.has_key(area):
                    templist[area] = []
                templist[area].append(_key)
    # print(templist)
    from_node_map_is = {}
    for _item in area_line_intersect_list:
        key = _item[_area_id_new]
        if not from_node_map_is.has_key(key):
            from_node_map_is[key] = []
        from_node_map_is[key].append(_item)
    replace_watershed_map = {}
    area_river_multi_intersect = []
    for _key in templist.keys():
        replace_list = templist.get(_key)
        if len(replace_list) == 1:
            replace_watershed_map[_key] = replace_list[0]
        else:
            if not from_node_map_is.has_key(_key):
                area_river_multi_intersect.append(_key)
                continue
            from_node_list = from_node_map_is.get(_key)
            if len(from_node_list) != 1:
                # 查询上下游
                start_node = get_start_node(from_node_list, _river_new_field_from_area, _river_new_field_to_area)
                replace_watershed_map[_key] = start_node
            else:
                replace_watershed_map[_key] = from_node_list[0][_river_new_field_from_area]
    for area_item in area_river_multi_intersect:
        print(area_item)
        areas = area_id_map.get(area_item)
        replace_watershed_map[area_item] = areas[0][_river_new_field_from_area]
    return replace_watershed_map


def get_start_node(from_node_list, _river_new_field_from_area, _river_new_field_to_area):
    start_set = []
    end_set = []
    for _item in from_node_list:
        start_set.append(_item[_river_new_field_from_area])
        end_set.append(_item[_river_new_field_to_area])
    _list = list(set(start_set) - set(end_set))
    if len(_list) > 1:
        print("有多连接")
    return _list[0]


def update_watershed_properties(watershed_path, zonal_statistics_map, _area_id_new, area_geo, centroid_x, centroid_y,
                                min, max, mean):
    Subbasin = 'Subbasin'
    Area = 'Area'
    Lat = 'Lat'
    Long = 'Long'
    Elev = 'Elev'
    ElevMin = 'ElevMin'
    ElevMax = 'ElevMax'
    # 添加字段
    arcDataManagement.add_field(watershed_path, Subbasin, 'LONG')  # _area_id_new
    arcDataManagement.add_field(watershed_path, Area, 'DOUBLE')  # area_geo
    arcDataManagement.add_field(watershed_path, Lat, 'DOUBLE')  # y
    arcDataManagement.add_field(watershed_path, Long, 'DOUBLE')  # x
    arcDataManagement.add_field(watershed_path, Elev, 'DOUBLE')  # mean
    arcDataManagement.add_field(watershed_path, ElevMin, 'LONG')  # min
    arcDataManagement.add_field(watershed_path, ElevMax, 'LONG')  # max
    fields = [_area_id_new, Subbasin, Area, Lat, Long, Elev, ElevMin, ElevMax, area_geo, centroid_y,
              centroid_x]
    with arcpy.da.UpdateCursor(watershed_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[0]
            if zonal_statistics_map.has_key(_temp_key):
                item = zonal_statistics_map.get(_temp_key)
                row[fields.index(Subbasin)] = _temp_key
                row[fields.index(Area)] = row[fields.index(area_geo)]  # todo unit squar meter
                row[fields.index(Lat)] = row[fields.index(centroid_y)]
                row[fields.index(Long)] = row[fields.index(centroid_x)]
                row[fields.index(Elev)] = item[mean]
                row[fields.index(ElevMin)] = item[min]
                row[fields.index(ElevMax)] = item[max]
            cursor.updateRow(row)


def update_river_properties(river_path, zonal_statistics_river_map, _river_new_field_from_area,
                            _river_new_field_to_area, min, max):
    Subbasin = 'Subbasin'
    SubbasinR = 'SubbasinR'
    MinEl = 'MinEl'
    MaxEl = 'MaxEl'
    # 添加字段
    arcDataManagement.add_field(river_path, Subbasin, 'LONG')  # from_node
    arcDataManagement.add_field(river_path, SubbasinR, 'LONG')  # area_geo
    arcDataManagement.add_field(river_path, MinEl, 'LONG')  # min
    arcDataManagement.add_field(river_path, MaxEl, 'LONG')  # max
    fields = [_river_new_field_from_area, _river_new_field_to_area, Subbasin, SubbasinR, MinEl, MaxEl]
    with arcpy.da.UpdateCursor(river_path, fields) as cursor:
        for row in cursor:
            _temp_key = row[fields.index(_river_new_field_from_area)]
            if zonal_statistics_river_map.has_key(_temp_key):
                item = zonal_statistics_river_map.get(_temp_key)
                row[fields.index(Subbasin)] = _temp_key
                row[fields.index(SubbasinR)] = row[fields.index(_river_new_field_to_area)]
                row[fields.index(MinEl)] = item[min]
                row[fields.index(MaxEl)] = item[max]
            cursor.updateRow(row)


def update_watershed_according_to_river(watershed_path, replace_map):
    fields = ['area_id']
    _values = replace_map.values()
    _values.sort()
    _value = _values[len(_values) - 1]
    with arcpy.da.UpdateCursor(watershed_path, fields) as cursor:
        for row in cursor:
            if replace_map.has_key(row[0]):
                row[0] = replace_map.get(row[0])
                cursor.updateRow(row)
            else:
                _value = _value + 1
                row[0] = _value
                cursor.updateRow(row)


def makeBasinSigle(basin_path, area_geo):
    arcpy.AddGeometryAttributes_management(basin_path, "AREA_GEODESIC", Area_Unit='SQUARE_METERS')
    area_list = arcUtils.shp_to_array(basin_path, [area_geo])
    area_max = max(area_list)
    fields = [area_geo]
    with arcpy.da.UpdateCursor(basin_path, fields) as cursor:
        for row in cursor:
            value = row[fields.index(area_geo)]
            if value < area_max[0] - 1:
                cursor.deleteRow()


def main():
    '''
    根据输入出口点文件、汇流点文件，生成集水区、流域、河网 shape文件(watershed.shp, basin.shp and river.shp)
    '''

    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini')
    _basin_name = config.get('general', 'basin_name')  # dem
    _pour_point_one = config.get('calculate_watershed', 'pour_point_one')   # 出口点
    _pour_point = config.get('calculate_watershed', 'pour_point')     # 汇流点

    # 指定保存文件的路径
    _workspace_path = os.path.dirname(os.path.abspath(__file__))
    save_file = "data.pkl"
    save_path = os.path.join(_workspace_path, 'data', save_file)
    # 读取字典
    with open(save_path, "rb") as f:
        dem = pickle.load(f)
    print(dem)
    # 定义路径常量
    _workspace_path = os.path.dirname(os.path.abspath(__file__))
    _workspace_path_dem_layer_path = os.path.join(_workspace_path, 'data', 'dem',  _basin_name)
    _calculate_path = os.path.join(_workspace_path, 'data', 'watershed', _basin_name, 'calculate')
    dic_in = os.path.join(_workspace_path, 'data', 'point', _basin_name)
    dic_out = _calculate_path
    # _layer_path = dem["layer_path"]

    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0
    # ################# 字符串常量 #################
    id_str = 'Id'
    join_id_str = id_str + '_1'
    _start_x = "START_X"
    _start_y = "START_Y"
    _end_x = "END_X"
    _end_y = "END_Y"
    _area_id_new = 'area_id'
    _join_area_id_new = _area_id_new + '_1'
    _river_new_field_from_area = 'from_area'
    _river_new_field_to_area = 'to_area'
    _river_fid_new = 'river_fid'
    length_key = 'LENGTH_GEO'
    area_geo = 'AREA_GEO'
    centroid_x = 'CENTROID_X'
    centroid_y = 'CENTROID_Y'
    MIN = 'MIN'
    MAX = 'MAX'
    MEAN = 'MEAN'
    # ################# 路径常量 #################
    temp_db_path = dic_out + "/Default.gdb"
    zonal_statistics_table = temp_db_path + "/zonal_statistics"
    zonal_statistics_river_table = temp_db_path + "/zonal_statistics_river"
    zonal_statistics_river_table_second = temp_db_path + "/zonal_statistics_river_second"
    fdr_path = _workspace_path + dem[0]["layer_path"] + "/fdr"
    stream_feature_out = _workspace_path + dem[0]["layer_path"] + "/stream_order_feature.shp"  # 河网矢量文件
    pour_point_one = os.path.join(dic_in, _pour_point_one)
    pour_point_path = os.path.join(dic_in, _pour_point)
    basin_tif = dic_out + "/basin.tif"  # 流域边界文件
    basin_path = dic_out + "/basin.shp"  # 流量边界矢量文件 basin.shp
    watershed_tif = dic_out + "/watershed.tif"  # 集水区文件 (DEM)
    watershed_tif_clip = _workspace_path + dem[0]['dem_path']  # 区域dem
    watershed_ori_path = dic_out + "/watershed_ori.shp"  # 集水区矢量文件
    watershed_dissolve_path = dic_out + "/watershed_dissolved.shp"
    watershed_path = dic_out + "/watershed.shp"
    watershed_path_bak = watershed_path.replace('.shp', '_bak.shp')
    clip_river_path = dic_out + "/river_clip_out.shp"  # 裁剪得到的矢量文件
    pour_point_clip_path = pour_point_path.replace('.shp', '_clip.shp')
    dpt_point_path = pour_point_path.replace('.shp', '_dpt.shp')
    sj_startpoint_watershed_path = dic_out + "/sj_startpoint_watershed.shp"
    sj_watershed_river_path = dic_out + "/sj_watershed_river.shp"
    sj_watershed_river_null_path = sj_watershed_river_path.replace('.shp', '_null.shp')
    sj_watershed_river_non_null_path = sj_watershed_river_path.replace('.shp', '_non_null.shp')
    sj_watershed_ds_river_path = dic_out + "/sj_watershed_ds_river.shp"
    sj_splitline_watershed_path = dic_out + "/sj_splitline_watershed.shp"
    split_line_out = dic_out + "/splited_line.shp"  # 在点处分割线
    river_path = dic_out + "/river.shp"
    river_path_no_stat = dic_out + "/river_no_stat.shp"
    vertices_out = split_line_out.replace('.shp', '_vertices.shp')
    intersect_river_watershed = dic_out + "/is_river_watershed.shp"
    intersect_river_watershed_1 = dic_out + "/is_river_watershed_1.shp"
    intersect_watershed_ori = dic_out + "/intersect_watershed_ori.shp"
    # ################# start logic ##############
    # 新建计算路径
    # _temp_flag = os.path.exists(_calculate_path)
    # if _temp_flag:
    #     shutil.rmtree(_calculate_path)
    # shutil.copytree(_workspace_path, _calculate_path)
    # 创建数据库
    arcDataManagement.create_file_gdb(temp_db_path)
    # 合并出口点的汇流点文件
    arcUtils.merge_table(pour_point_path, pour_point_one)
    # 计算流域边界
    # 出口点 集水区
    arcSpatialAnalyst.watershed(fdr_path, pour_point_one, basin_tif)
    # 出口点集水区 矢量化
    arcConvert.raster_to_polygon(basin_tif, False, basin_path)
    makeBasinSigle(basin_path, area_geo)
    # 计算像元大小
    [cell_size_x, cell_size_y] = arcUtils.get_raster_cell_size(basin_tif)
    cell_size = min(cell_size_x, cell_size_y)
    # 按流域边界剪裁汇流点文件
    arcAnalysis.clip(pour_point_path, basin_path, pour_point_clip_path)
    # 汇流点 集水区 使用extent
    desc = arcpy.Describe(basin_path)
    arcSpatialAnalyst.watershed(fdr_path, pour_point_clip_path, watershed_tif, "FID", desc.extent)
    # 汇流点 矢量化 获得 原始集水区矢量文件
    arcConvert.raster_to_polygon(watershed_tif, False, watershed_ori_path)
    watershed_ori_path_temp = watershed_ori_path.replace(".shp", "_temp.shp")
    arcAnalysis.clip(watershed_ori_path, basin_path, watershed_ori_path_temp)
    # 恢复剪裁
    arcpy.CopyFeatures_management(watershed_ori_path_temp, watershed_ori_path)
    # 给集水区一个固定id
    arcDataManagement.add_field(watershed_ori_path, _area_id_new, 'LONG')
    # 计算字段
    arcDataManagement.calculate_field(watershed_ori_path, field_name=_area_id_new, expression="!Id!",
                                      expression_type="PYTHON_9.3")
    # 初步计算河网
    # 按出口点求得的流域 裁剪 河网矢量
    arcAnalysis.clip(stream_feature_out, basin_path, clip_river_path)
    # 提取防灾对象
    arcUtils.copy_shp_by_key(pour_point_clip_path, dpt_point_path, "TYPE", ["VILLAGE", "RESERVOIR"])
    print("提取防灾对象成功")
    # 在点处分割线（只用水库跟村屯，离河道距离小于一个像元的不计）
    arcDataManagement.split_line_at_point(clip_river_path, dpt_point_path, split_line_out, cell_size)
    # 计算字段 更新河网起点 为 watershed的 面id
    arcDataManagement.add_field(split_line_out, _river_new_field_from_area, 'LONG')
    # 给河道一个固定id
    arcDataManagement.add_field(split_line_out, _river_fid_new, 'LONG')
    # 计算字段
    arcDataManagement.calculate_field(split_line_out, field_name=_river_fid_new, expression="!FID!",
                                      expression_type="PYTHON_9.3")
    #  相交
    arcAnalysis.intersect([split_line_out, watershed_ori_path], intersect_river_watershed, join_attributes="ALL",
                          output_type="LINE")
    arcpy.AddGeometryAttributes_management(intersect_river_watershed, "LENGTH_GEODESIC", "METERS")
    # area-line 相交长度list
    is_line_area_data = arcUtils.shp_to_dict_list(intersect_river_watershed, [_river_fid_new, _area_id_new, length_key])
    # 按相交线长度分配河道给集水区
    line_startArea_map, line_interArea_map = assign_river_area_by_length(is_line_area_data, _river_fid_new,
                                                                         _area_id_new,
                                                                         length_key)
    print("按相交线长度分配河道给集水区")
    # print(line_startArea_map)
    # print("********************")
    # 要素折点转点
    arcDataManagement.feature_vertices_to_points(split_line_out, 'START', vertices_out)  # 河网起点点点集
    # 空间连接
    arcAnalysis.spatial_join(vertices_out, watershed_ori_path, sj_startpoint_watershed_path,
                             match_option="INTERSECT", join_operation="JOIN_ONE_TO_MANY")
    # 按河道起点分配河道给集水区
    assign_river_area_by_startpoint(line_startArea_map, line_interArea_map, sj_startpoint_watershed_path,
                                    _river_fid_new,
                                    _area_id_new, length_key)
    print("按河道起点分配河道给集水区")
    # print(line_startArea_map)
    # print("********************")
    # 按集水区分组
    arcpy.AddGeometryAttributes_management(split_line_out, "LINE_START_MID_END")
    space_list = arcUtils.shp_to_dict_list(split_line_out, [_river_fid_new, _start_x, _start_y, _end_x, _end_y])
    # end_loc :[lineFid]
    locEnd_line_map = group_by_end_loc(space_list, _river_fid_new, _end_x, _end_y)
    # river_fid: [loc]
    space_map = loc_group_by_river(space_list, _river_fid_new)
    # 空间连接
    arcAnalysis.spatial_join(split_line_out, watershed_ori_path, sj_splitline_watershed_path,
                             match_option="INTERSECT", join_operation="JOIN_ONE_TO_MANY")
    line_area_sj_list = arcUtils.shp_to_dict_list(sj_splitline_watershed_path, [_river_fid_new, _area_id_new])
    # 查找集水区内的河道交点
    # intersect_point_one_area:[areaId:riverFid]
    intersect_point_one_area, intersect_point_two_area, intersect_point_two_area_no_assigned = group_by_watershed(
        line_startArea_map,
        is_line_area_data,
        space_list,
        _river_fid_new, _area_id_new,
        _end_x,
        _end_y)
    arcpy.AddGeometryAttributes_management(intersect_river_watershed, "LINE_START_MID_END")
    space_list_intersect = arcUtils.shp_to_dict_list(intersect_river_watershed, [_river_fid_new, _area_id_new, _start_x,
                                                                                 _start_y, _end_x, _end_y])
    space_list_map = group_by_line(space_list_intersect, _river_fid_new, _area_id_new)
    # 集水区中只有一个交点
    deal_one_intersect_watershed(is_line_area_data, intersect_point_one_area, line_area_sj_list, line_startArea_map,
                                 locEnd_line_map, space_map, _river_fid_new, _area_id_new, _start_x,
                                 _start_y)
    deal_two_intersect_watershed(intersect_point_two_area, intersect_point_two_area_no_assigned, line_startArea_map,
                                 space_map,
                                 _river_fid_new, _area_id_new, _start_x, _start_y, _end_x, _end_y, is_line_area_data,
                                 line_area_sj_list, locEnd_line_map, space_list_map)
    update_river(split_line_out, line_startArea_map, _river_fid_new, _river_new_field_from_area)
    arcDataManagement.dissolve(split_line_out, river_path, _river_new_field_from_area)
    # 给河道id重新赋值
    replace_map = arcUtils.update_field_by_order_with_result(river_path, _river_new_field_from_area)
    # print("replace_map")
    # print(replace_map)
    # 更新 to_node
    create_tree(river_path, _river_new_field_from_area, _river_new_field_to_area, _start_x, _start_y, _end_x,
                _end_y)
    #  ################# 更新集水区 ##############
    # 按河道更新集水区id
    if len(replace_map) > 0:
        update_watershed_according_to_river(watershed_ori_path, replace_map)
    # 空间连接
    arcAnalysis.spatial_join(watershed_ori_path, river_path, sj_watershed_river_path,
                             match_option="INTERSECT", join_operation="JOIN_ONE_TO_MANY")
    sept_shp_null(sj_watershed_river_path, _river_new_field_from_area, sj_watershed_river_null_path,
                  sj_watershed_river_non_null_path)
    null_area_ids = arcUtils.get_list_by_key_from_shp(sj_watershed_river_null_path, _area_id_new)
    non_null_area_ids = arcUtils.get_list_by_key_from_shp(sj_watershed_river_non_null_path, _area_id_new)
    # 相交
    arcAnalysis.intersect([watershed_ori_path, watershed_ori_path], intersect_watershed_ori, join_attributes="ALL",
                          output_type="LINE")
    arcpy.AddGeometryAttributes_management(intersect_watershed_ori, "LENGTH_GEODESIC", "METERS")
    is_watershed_table = get_is_watershed_table(intersect_watershed_ori, _area_id_new, _join_area_id_new, length_key)
    null_non_map = get_null_intersect_non_null(is_watershed_table, null_area_ids, non_null_area_ids, _area_id_new,
                                               _join_area_id_new,
                                               length_key)
    update_watershed(watershed_ori_path, null_non_map, _area_id_new)
    arcDataManagement.dissolve(watershed_ori_path, watershed_dissolve_path, _area_id_new)
    # 相交
    arcAnalysis.spatial_join(watershed_dissolve_path, river_path, sj_watershed_ds_river_path, match_option="INTERSECT",
                             join_operation="JOIN_ONE_TO_MANY")
    area_line_spatial_join_list = arcUtils.shp_to_dict_list(sj_watershed_ds_river_path,
                                                            [_area_id_new, _river_new_field_from_area,
                                                             _river_new_field_to_area])
    #  相交
    arcAnalysis.intersect([watershed_dissolve_path, river_path], intersect_river_watershed_1, join_attributes="ALL",
                          output_type="LINE")
    area_line_intersect_list = arcUtils.shp_to_dict_list(intersect_river_watershed_1,
                                                         [_area_id_new, _river_new_field_from_area,
                                                          _river_new_field_to_area])
    from_area_all = arcUtils.get_list_by_key_from_shp(river_path, _river_new_field_from_area)
    replace_watershed_map = group_by_from_area(area_line_spatial_join_list, area_line_intersect_list, from_area_all,
                                               _area_id_new,
                                               _river_new_field_from_area,
                                               _river_new_field_to_area)
    update_watershed(watershed_dissolve_path, replace_watershed_map, _area_id_new)
    arcDataManagement.dissolve(watershed_dissolve_path, watershed_path, _area_id_new)
    # 保存原始状态
    arcpy.CopyFeatures_management(watershed_path, watershed_path_bak)
    ############################ 计算子流域参数 #############################
    # 集水区
    # 添加几何属性
    arcpy.AddGeometryAttributes_management(watershed_path, "AREA_GEODESIC", Area_Unit='SQUARE_METERS')
    arcpy.AddGeometryAttributes_management(watershed_path, "CENTROID")
    # 以表格显示分区统计
    arcSpatialAnalyst.ZonalStatisticsAsTable(watershed_path, _area_id_new, watershed_tif_clip, zonal_statistics_table,
                                             statistics_type='MIN_MAX_MEAN')
    zonal_statistics_list = arcUtils.shp_to_dict_list(zonal_statistics_table, [_area_id_new, MIN, MAX, MEAN])
    zonal_statistics_map = arcUtils.list_to_keymap(zonal_statistics_list, _area_id_new)
    update_watershed_properties(watershed_path, zonal_statistics_map, _area_id_new, area_geo, centroid_x, centroid_y,
                                MIN, MAX, MEAN)
    # 以表格显示分区统计
    arcSpatialAnalyst.ZonalStatisticsAsTable(river_path, _river_new_field_from_area, watershed_tif_clip,
                                             zonal_statistics_river_table,
                                             statistics_type='MIN_MAX_MEAN')
    # 筛选出没有统计的河道
    river_map = arcUtils.shp_to_dict_list(river_path, [_river_new_field_from_area])
    river_list = arcUtils.maplist_to_fieldlist(river_map, _river_new_field_from_area)
    stat_map = arcUtils.shp_to_dict_list(zonal_statistics_river_table, [_river_new_field_from_area])
    stat_list = arcUtils.maplist_to_fieldlist(stat_map, _river_new_field_from_area)
    river_no_stat = list(set(river_list) - set(stat_list))
    if len(river_no_stat) > 1:
        # 构造重做河道
        arcUtils.copy_shp_by_key(river_path, river_path_no_stat, _river_new_field_from_area, river_no_stat)
        # 再一次 以表格显示分区统计
        arcSpatialAnalyst.ZonalStatisticsAsTable(river_path_no_stat, _river_new_field_from_area, watershed_tif_clip,
                                                 zonal_statistics_river_table_second,
                                                 statistics_type='MIN_MAX_MEAN')
        # 追加表格
        arcUtils.merge_table(zonal_statistics_river_table, zonal_statistics_river_table_second)
    #
    zonal_statistics_river_list = arcUtils.shp_to_dict_list(zonal_statistics_river_table,
                                                            [_river_new_field_from_area, MIN, MAX])
    zonal_statistics_river_map = arcUtils.list_to_keymap(zonal_statistics_river_list, _river_new_field_from_area)
    update_river_properties(river_path, zonal_statistics_river_map, _river_new_field_from_area,
                            _river_new_field_to_area, MIN, MAX)


def break_point_flg():
    pass


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
