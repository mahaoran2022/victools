# -*- coding: UTF-8 -*-

import arcpy
from arcpy import env
import codecs
import csv
import common.sp as s
import common.arcDataManagement as arcDataManagement
import common.arcObject as arcObject
import shutil
import common.arcProjection as arcProjection


def print_description(_source):
    desc = arcpy.Describe(_source)
    path, file = s.split(_source)
    print("Describe " + file + " : " + desc.datasetType)  # Table
    fieldArrays = arcpy.ListFields(_source)
    print(file + " 属性列表开始")
    for field in fieldArrays:
        print(field.name)
    print(file + " 属性列表结束")


def get_raster_cell_size(in_raster_path):
    return [float(arcpy.GetRasterProperties_management(in_raster_path, 'CELLSIZEX').getOutput(0)),
            float(arcpy.GetRasterProperties_management(in_raster_path, 'CELLSIZEY').getOutput(0))]


def to_map(_source, _key='FID'):
    fieldArrays = arcpy.ListFields(_source)
    fieldNameList = []
    for field in fieldArrays:
        fieldNameList.append(field.name)
    cursor_search = arcpy.SearchCursor(_source)
    result = {}
    for row in cursor_search:
        temp_dict = {}
        for fieldName in fieldNameList:
            temp_dict[fieldName] = row.getValue(fieldName)
        result[row.getValue(_key)] = temp_dict
    return result


def list_to_map(_source, _key='FID'):
    result = {}
    for item in _source:
        result[item[_key]] = item
    return result


def get_max_area_id(_source, _key='FID'):
    cursor_search = arcpy.SearchCursor(_source)
    result = 0
    for row in cursor_search:
        temp = row.getValue(_key)
        if temp > result:
            result = temp
    return result


def shp_to_dict_list(_input_shp, fields=['FID']):
    result = []
    rows = arcpy.SearchCursor(_input_shp)
    for row in rows:
        item = {}
        for field in fields:
            item[field] = row.getValue(field)
        result.append(item)
    return result


def shp_to_dict_list_ignore_null(_input_shp, ignore_value, fields=['FID'], ignore_fields='FID'):
    result = []
    rows = arcpy.SearchCursor(_input_shp)
    for row in rows:
        item = {}
        if row.getValue(ignore_fields) == ignore_value:
            continue
        for field in fields:
            item[field] = row.getValue(field)
        result.append(item)
    return result


def shp_to_dict_list_filter(_input_shp, filter_field, value, fields=['FID']):
    result = []
    rows = arcpy.SearchCursor(_input_shp)
    for row in rows:
        item = {}
        if row.getValue(filter_field) != value:
            continue
        for field in fields:
            item[field] = row.getValue(field)
        result.append(item)
    return result


def shp_to_array(_input_shp, fields):
    result = []
    rows = arcpy.SearchCursor(_input_shp)
    for row in rows:
        item = []
        for field in fields:
            item.append(row.getValue(field))
        result.append(item)
    return result


def get_list_by_key_from_shp(_input_table, _key):
    result = []
    rows = arcpy.SearchCursor(_input_table)
    for row in rows:
        result.append(row.getValue(_key))
    result = list(set(result))
    return result


def get_id_from_list(_input_list, _key):
    result = []
    for _item in _input_list:
        result.append(_item[_key])
    result = list(set(result))
    return result


def group_by_key(_list, _key):
    result = {}
    for data in _list:
        _item_key = data[_key]
        if not result.has_key(_item_key):
            result[_item_key] = []
        result[_item_key].append(data)
    return result


def list_to_keymap(_list, _key):
    result = {}
    for data in _list:
        _item_key = data[_key]
        result[_item_key] = data
    return result


def update_column(_src_path, _src_column, _new_column, _type):
    copy_column(_src_path, _src_column, _new_column, _type)
    arcDataManagement.delete_field(_src_path, _src_column)


def copy_column(_src_path, _src_column, _new_column, _type):
    # 添加字段
    arcDataManagement.add_field(_src_path, _new_column, _type)
    fields = [_src_column, _new_column]
    with arcpy.da.UpdateCursor(_src_path, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)


def copy_table_by_fields(_shp_path, _table_path, fields):
    shp_fields = arcpy.ListFields(_shp_path)
    fieldinfo = arcpy.FieldInfo()
    for field in shp_fields:
        if fields.count(field.name) == 1:
            fieldinfo.addField(field.name, field.name, "VISIBLE", "")
        else:
            fieldinfo.addField(field.name, field.name, "HIDDEN", "")
    out_view = s.getName(_table_path) + '_view'
    arcpy.MakeTableView_management(_shp_path, out_view, "", "", fieldinfo)
    arcpy.CopyRows_management(out_view, _table_path)


def copy_table(_input_table, _output_table):
    out_view = s.getName(_output_table) + '_view'
    arcpy.MakeTableView_management(_input_table, out_view)
    arcpy.CopyRows_management(out_view, _output_table)


def area_to_point(_in_value_path, _out_shp_path, _x, _y, _id):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(_out_shp_path)
    # Set the workspace
    env.workspace = _path
    sr = arcpy.Describe(_in_value_path).spatialReference
    create_file = arcpy.CreateFeatureclass_management(_path, _file, "POINT", "", "", "", sr)
    arcpy.AddField_management(create_file, _id, "LONG")
    cursor = arcpy.da.InsertCursor(create_file, ['SHAPE@XY', _id])
    rows = arcpy.SearchCursor(_in_value_path)  # 查询游标
    for row in rows:
        _point = arcpy.Point()
        _point.X = row.getValue(_x)
        _point.Y = row.getValue(_y)
        point_geometry = arcpy.PointGeometry(_point)
        cur_id = row.getValue(_id)
        cursor.insertRow((point_geometry, cur_id))
    del cursor


def merge_table(_source_path, _input):
    insert_cursor = arcpy.InsertCursor(_source_path)
    rows = arcpy.SearchCursor(_input)
    for row in rows:
        insert_cursor.insertRow(row)


def maplist_to_fieldlist(_input, _field):
    result = []
    for item in _input:
        result.append(item.get(_field))
    return result


def copy_shp_by_key(_input_path, _output_path, _type_key, _type_list):
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


def update_field_by_order(_src_path, point_id):
    fields = ['FID', point_id]
    with arcpy.da.UpdateCursor(_src_path, fields) as cursor:
        for row in cursor:
            row[1] = row[0] + 1
            cursor.updateRow(row)


def update_field_by_order_with_result(_src_path, point_id):
    fields = ['FID', point_id]
    result = {}
    with arcpy.da.UpdateCursor(_src_path, fields) as cursor:
        for row in cursor:
            result[row[1]] = row[0] + 1
            row[1] = row[0] + 1
            cursor.updateRow(row)
    return result


def save_file(data_list, fields_order, file_path, seperator, with_header=True):
    print("开始生成文件")
    text = ''
    if with_header:
        text += seperator.join(fields_order) + '\n'

    for data in data_list:
        line = ''
        for field in fields_order:
            value = data[field]
            # 检查是否是字符串且不是unicode对象
            if isinstance(value, str) and not isinstance(value, unicode):
                value = value.decode('gb18030')  # 先解码为unicode
            line += unicode(value) + seperator  # 再转为utf-8
        text += line[:-1] + '\n'  # 去掉最后的分隔符，加换行符

    # if with_header:
    #     for field in fields_order:
    #         text = text + unicode(field) + seperator
    #     text = text[:-1]
    #     text = text + '\n'
    # for data in data_list:
    #     for field in fields_order:
    #         data[field] = data[field].decode('gb18030').encode('utf-8')
    #         text = text + unicode(data[field]) + seperator
    #     text = text[:-1]
    #     text = text + '\n'
    # text = text[:-1]
    # 使用 codecs 模块以 UTF-8 编码写入文件
    with codecs.open(file_path, 'w', encoding='utf-8') as file:
        file.write(u'\ufeff')  # 写入BOM
        file.write(text)
        file.close()
        print("文件生成成功！")


def copy_file(src_path, dest_path):
    shutil.copy(src_path, dest_path)


def copy_folder(source_path, target_path):
    """
    目标文件夹不应该存在，如果一定要存在，需要改shutil里面的源码，创建文件夹那段
    """
    shutil.copytree(source_path, target_path)


def get_field_list(_path):
    fieldArrays = arcpy.ListFields(_path)
    fieldNameList = []
    for field in fieldArrays:
        fieldNameList.append(field.name)
    return fieldNameList


def checkFieldExist(_path, fields):
    fieldArrays = get_field_list(_path)
    for field in fields:
        if not field in fieldArrays:
            return False
    return True


def get_rows(_path):
    result = arcpy.GetCount_management(_path)
    count = int(result.getOutput(0))
    return count


def create_empty_file(file_path):
    text = ''
    file = open(file_path, 'w')
    file.write(text)  # 写入内容信息
    file.close()


# 按大地坐标系进行输出--raster
def to_geographic(in_raster_path):
    sr = arcObject.get_property(in_raster_path).spatialReference
    aun = sr.angularUnitName
    if aun is None or aun != 'Degree':
        arcProjection.project_raster_by_factory_code(in_raster_path, 4326)


# 按大地坐标系进行输出--shp
def to_geographic_shp(in_feature_path):
    sr = arcObject.get_property(in_feature_path).spatialReference
    aun = sr.angularUnitName
    if aun is None or aun != 'Degree':
        sr = arcpy.SpatialReference(4326)
        arcProjection.project(in_feature_path, None, sr)


def create_area_shp(point_data_all, gridSize, _out_shp_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(_out_shp_path)
    # Set the workspace
    env.workspace = _path
    features = []
    for _item in point_data_all:
        points = [[_item["_x"], _item["_y"]], [_item["_x"] + gridSize, _item["_y"]],
                  [_item["_x"] + gridSize, _item["_y"] + gridSize], [_item["_x"], _item["_y"] + gridSize]
                  ]
        _polygon = arcpy.Array([arcpy.Point(*p) for p in points])
        features.append(arcpy.Polygon(_polygon))
    arcpy.CopyFeatures_management(features, _out_shp_path)
    # 添加几何属性
    arcpy.AddGeometryAttributes_management(_out_shp_path, "CENTROID")
