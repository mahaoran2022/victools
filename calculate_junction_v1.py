# -*- coding: UTF-8 -*-
# 初始化流域
import os.path
import sys
import time
import shutil
import configparser
import pickle
from arcpy import env
from arcpy.sa import *
import arcpy
import watershed.fill as fill
import watershed.fdr as fdr
import watershed.fac as fac
import watershed.stream as stream
import watershed.streamLink as streamLink
import watershed.streamOrder as streamOrder
import watershed.streamToFeature as streamToFeature
import watershed.polygonCreate as polygonCreate
import common.sp as s
import common.folder as _folder
import common.arcConvert as arcConvert
import common.arcDataManagement as arcDataManagement
import common.arcAnalysis as arcAnalysis
import common.constant as constant
import common.arcUtils as arcUtils


def add_point(points_out_path, erase_out, _file_path, _file_type):
    '''
    添加指定类型最近点
    :param points_out_path: 倾泻点文件
    :param erase_out: 去掉终点的河网对应点集
    :param _file_path: 输入文件路径
    :param _file_type: 输入文件合并点类型
    '''
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(points_out_path)
    # Set the workspace
    env.workspace = _path
    arcpy.Near_analysis(_file_path, erase_out)
    point_shape_map = arcUtils.to_map(erase_out)
    # points_out_path 添加新点
    cursor = arcpy.InsertCursor(points_out_path)
    rows = arcpy.SearchCursor(_file_path)  # 查询游标
    for row in rows:
        row_new = cursor.newRow()
        row_new.setValue('shape', point_shape_map.get(row.getValue('NEAR_FID')).get('Shape'))
        row_new.setValue('from_node', row.getValue('FID'))
        row_new.setValue('to_node', row.getValue('NEAR_FID'))
        row_new.setValue('DISTANCE', row.getValue('NEAR_DIST'))
        row_new.setValue('STCD', row.getValue('STCD'))
        row_new.setValue('STNAME', row.getValue('STNAME'))
        row_new.setValue('TYPE', _file_type)
        cursor.insertRow(row_new)


def snap_pour_point(_points_out_path, _river_corr_point, _river_outflow_point, _river_feature_points):
    '''
    捕捉倾泻点
    :param _points_out_path: 倾泻点输出路径
    :param _river_corr_point:河网对应点集
    :param _river_outflow_point: 河网出流点（最近距离点）
    :param _river_feature_points: 河网要素点
    :return:
    '''
    arcpy.env.overwriteOutput = True  # 允许覆盖
    _path, _points_out_file = s.split(_points_out_path)
    # 定义坐标系以及各种字段
    sr = arcpy.SpatialReference("WGS 1984")
    result_path = _path
    result_file = _points_out_file
    create_file = arcpy.CreateFeatureclass_management(result_path, result_file, "POINT", "", "", "", sr)
    arcpy.AddField_management(create_file, "from_node", "LONG")
    arcpy.AddField_management(create_file, "to_node", "LONG")
    arcpy.AddField_management(create_file, "DISTANCE", "DOUBLE", field_is_nullable="NULLABLE")
    arcpy.AddField_management(create_file, "TARGET_FID", "LONG", field_is_nullable="NULLABLE")
    arcpy.AddField_management(create_file, "TYPE", "TEXT")
    _fields = []
    _fields.append('shape')
    _fields.append('from_node')
    _fields.append('to_node')
    _fields.append('DISTANCE')
    _fields.append('TARGET_FID')
    _fields.append('TYPE')
    cur = arcpy.da.InsertCursor(create_file, _fields)
    point_shape_map = arcUtils.to_map(_river_corr_point, 'pointid')
    for _outflow_point_key in _river_outflow_point.keys():
        _outflow_point = _river_outflow_point.get(_outflow_point_key)
        point_geometry = point_shape_map.get(_outflow_point['TARGET_FID'])
        cur.insertRow((point_geometry.get('Shape'), _outflow_point['from_node'], _outflow_point['to_node'],
                       _outflow_point['DISTANCE'], _outflow_point['TARGET_FID'], "RIVER"))
    # 处理河网要素
    cursor = arcpy.InsertCursor(create_file)
    cursor_search = arcpy.SearchCursor(_river_feature_points)
    _node_set = _river_outflow_point.keys()
    for row in cursor_search:
        _key = str(row.getValue('from_node')) + "_" + str(row.getValue('to_node'))
        if _node_set.count(_key) == 0:
            row_new = cursor.newRow()
            row_new.setValue('shape', row.getValue('Shape'))
            row_new.setValue('from_node', row.getValue('from_node'))
            row_new.setValue('to_node', row.getValue('to_node'))
            row_new.setValue('TYPE', "RIVER")
            cursor.insertRow(row_new)
    print("点要素生成成功！")


def make_river_outflow_point(stream_order_out, dic_out, river_corr_point, _precision):
    '''
    生成河网出流点
    :param stream_order_out: 河网分级
    :param dic_out: 输出文件目录
    :param river_corr_point: 河网对应点集
    :param _precision: 精度（像元）
    :return: 河网距离元组，河网矢量文件，要素折点转点(END)点集，去掉终点的河网对应点集
    '''
    # 栅格河网矢量化
    stream_to_feature_out = dic_out + "/stream_order_feature" + ".shp"  # 河网矢量文件
    streamToFeature.stream_to_feature(stream_order_out, "fdr", stream_to_feature_out)
    # 要素折点转点(END)
    vertices_end_out = stream_to_feature_out.replace('.shp', '_vertices_end.shp')
    arcDataManagement.feature_vertices_to_points(stream_to_feature_out, 'END', vertices_end_out)  # 河网终点点集
    # 擦除
    erase_out = stream_to_feature_out.replace('.shp', '_erased.shp')  # 去掉终点的河网对应点集
    arcAnalysis.erase(river_corr_point, vertices_end_out, erase_out)
    # 空间连接
    spatial_join_path = dic_out + "/spatial_join" + ".shp"  # 带河网信息的去点后河网对应点集
    arcAnalysis.spatial_join(erase_out, stream_to_feature_out, spatial_join_path)
    # 创建数据库
    temp_db_path = dic_out + "/Default.gdb"
    arcDataManagement.create_file_gdb(temp_db_path)
    # 点距离 2*像元
    temp_var, near_features = s.split(spatial_join_path)
    distance_table = temp_db_path + "/distance_table"
    search_radius = _precision * 5
    arcAnalysis.point_distance(vertices_end_out, near_features, distance_table, search_radius)
    # 添加连接 input
    join_table_input = temp_db_path + "/join_table_input"
    arcDataManagement.add_join_table(distance_table, "INPUT_FID", vertices_end_out, "FID", join_table_input)
    # 添加连接 near
    out_table_name = s.getName(distance_table)
    join_table_near = temp_db_path + "/join_table_near"
    arcDataManagement.add_join_table(join_table_input, out_table_name + "_NEAR_FID", spatial_join_path, "FID",
                                     join_table_near)
    # join_table_near 中 寻找最近点
    input_table_name_prefix = s.getName(join_table_input) + "_" + s.getName(vertices_end_out) + "_"
    distance_table_name_prefix = s.getName(join_table_input) + "_" + s.getName(distance_table) + "_"  # 因为连接两次
    near_table_name_prefix = s.getName(spatial_join_path) + "_"
    _from_node = "from_node"
    _to_node = "to_node"
    _input_from = input_table_name_prefix + _from_node
    _near_from = near_table_name_prefix + _from_node
    _input_to = input_table_name_prefix + _to_node
    _near_to = near_table_name_prefix + _to_node
    _distance = distance_table_name_prefix + 'DISTANCE'
    _pointid = near_table_name_prefix + 'pointid'
    cursor_search = arcpy.SearchCursor(join_table_near)
    min_dict = {}
    for row in cursor_search:
        temp_dict = {}
        if row.getValue(_input_from) == row.getValue(_near_from) and row.getValue(_input_to) == row.getValue(_near_to):
            temp_dict['from_node'] = row.getValue(_input_from)
            temp_dict['to_node'] = row.getValue(_input_to)
            temp_dict['DISTANCE'] = row.getValue(_distance)
            temp_dict['TARGET_FID'] = row.getValue(_pointid)
            _temp_key = str(temp_dict['from_node']) + "_" + str(temp_dict['to_node'])
            if (min_dict.has_key(_temp_key)):
                _item = min_dict[_temp_key]
                temp_min_distance = _item['DISTANCE']
                if (temp_dict['DISTANCE'] < temp_min_distance):
                    min_dict[_temp_key] = temp_dict
            else:
                min_dict[_temp_key] = temp_dict
    return min_dict, stream_to_feature_out, vertices_end_out, erase_out


def move_specific_files(src_dir, dest_dir, file_names):
    """
    将源文件夹中的特定文件移动到目标文件夹中。

    :param src_dir: 源文件夹路径
    :param dest_dir: 目标文件夹路径
    :param file_names: 需要移动的文件名列表（不包括扩展名）
    """
    # 确保目标文件夹存在，如果不存在则创建它
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # 遍历源文件夹中的所有文件
    for file_name in os.listdir(src_dir):
        # 获取文件名和扩展名
        name, ext = os.path.splitext(file_name)

        # 检查文件名是否在目标列表中
        if name in file_names:
            full_file_name = os.path.join(src_dir, file_name)
            # 确保是文件而不是文件夹
            if os.path.isfile(full_file_name):
                # 移动文件到目标文件夹
                shutil.copy(full_file_name, dest_dir)
                print("Moved: {} to {}".format(full_file_name, dest_dir))

def main():
    '''
    根据输入区域dem，村屯、水库点集文件，生成汇流点文件
    '''
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini')

    # 读取 general 配置
    _basin_name = config.get('general', 'basin_name')
    _dem_file = config.get('general', 'dem_file')
    _xmin = config.getfloat('general', 'xmin')
    _ymin = config.getfloat('general', 'ymin')
    _xmax = config.getfloat('general', 'xmax')
    _ymax = config.getfloat('general', 'ymax')
    _precision = config.getfloat('general', 'gridsize')
    _village_file = config.get('general', 'village_file')
    _rsvr_file = config.get('general', 'rsvr_file')
    _river_file = config.get('general', 'river_file')
    _number_zones = config.getint('general', 'number_zones')

    # 基于读取的配置文件设置其他参数
    _file_name = _dem_file.rsplit(".")[0]
    _surffix = _dem_file.rsplit(".")[1]

    _workspace_path = os.path.dirname(os.path.abspath(__file__))
    _rsvr_path = os.path.join(_workspace_path, 'data', 'shp', _basin_name, _rsvr_file)
    _river_path = os.path.join(_workspace_path, 'data', 'shp', _basin_name, _river_file)
    # 检查文件是否存在
    _rsvr_file_exist = os.path.isfile(_rsvr_path)
    _river_file_exist = os.path.isfile(_river_path)

    _rsvr_file = "rsvr_file.shp" if _rsvr_file_exist else None
    _river_file = "zhangge_river84.shp" if _river_file_exist else None

    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0
    # 检查 水库 的 STCD 和 STNAME
    if _rsvr_file_exist:
        # _rsvr_path = _workspace_path + '/' + _rsvr_file
        _rsvr_path = os.path.join(_workspace_path, 'data', 'shp', _basin_name, _rsvr_file)
        check_result = arcUtils.checkFieldExist(_rsvr_path, ['STCD', 'STNAME'])
        if not check_result:
            msg = '水库文件字段不完整'
            raise Exception(msg)

    # 检查 村屯 的 STCD 和 STNAME
    # _village_path = _workspace_path + '/' + _village_file
    _village_path = os.path.join(_workspace_path, 'data', 'shp', _basin_name, _village_file)
    check_result = arcUtils.checkFieldExist(_village_path, ['STCD', 'STNAME'])
    if not check_result:
        msg = '村屯文件字段不完整'
        raise Exception(msg)

    # dem数据结构
    dem = [{"dem": _basin_name}]

    # 创建图层文件夹
    # dic_in = _workspace_path + "/" + _dem_file
    dic_in = os.path.join(_workspace_path, 'data', 'dem', _basin_name, _dem_file)
    # dic_out = dic_in + 'layer'
    dic_out = _folder.create_layer(dic_in)
    dem[0].update({"dem_path": dic_in.replace(_workspace_path, '')})  # 保存相对路径
    dem[0].update({"layer_path": dic_out.replace(_workspace_path, '')})  # 保存相对路径

    # 保证栅格的空间参考为大地坐标，转成4326
    arcUtils.to_geographic(dic_in)
    file_in = dic_out + "/" + _file_name + '_clip.' + _surffix
    # 按范围外扩 10 * 精度
    _scale = 10
    _left = _xmin - _precision * _scale
    _bottom = _ymin - _precision * _scale
    _right = _xmax + _precision * _scale
    _top = _ymax + _precision * _scale
    try:
        arcDataManagement.clip_rectangle(dic_in, file_in, _left, _bottom, _right, _top)
    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))

    # arcDataManagement.clip_rectangle(dic_in, file_in, _left, _bottom, _right, _top)
    [cell_size_x, cell_size_y] = arcUtils.get_raster_cell_size(file_in)
    cell_size = min(cell_size_x, cell_size_y)
    dem[0].update({"cell_size": cell_size})  # cell_size


    # 填洼
    fill_out = dic_out + "/fill"
    fill.fill(file_in, fill_out)
    if _river_file_exist:
        # 将流道矢量数据转换为栅格
        stream_raster = dic_out + "/stream_raster.tif"
        # _river_file_path = _workspace_path + "/" + _river_file
        _river_file_path = os.path.join(_workspace_path, 'data', 'shp', _basin_name, _river_file)
        arcUtils.to_geographic_shp(_river_file_path)


        arcpy.PolylineToRaster_conversion(_river_file_path, "FID", stream_raster, "MAXIMUM_LENGTH", "NONE",
                                          fill_out)
        # 剪裁
        _river_file_clip = dic_out + "/stream_raster_clip.tif"
        arcDataManagement.clip_shp(stream_raster, _river_file_clip, fill_out)
        # 烧入流道
        burned_dem = dic_out + "/burned_dem.tif"
        fill_out_raster = Raster(fill_out)
        # 设置栅格环境，以确保所有栅格对齐
        arcpy.env.snapRaster = fill_out_raster
        arcpy.env.extent = fill_out_raster.extent
        arcpy.env.cellSize = fill_out_raster.meanCellWidth
        burned_dem_result = Con(IsNull(_river_file_clip), fill_out_raster,
                                Con(fill_out_raster < 0, fill_out_raster / 0.8, fill_out_raster * 0.8))
        burned_dem_result.save(burned_dem)
        fill.fill(burned_dem, fill_out)
    # 流向 -> 提取流域
    fdr_out = dic_out + "/fdr"
    fdr.fdr(fill_out, fdr_out)
    # 流量
    fac_out = dic_out + "/fac"
    fac.fac(fdr_out, fac_out)
    # 河道定义
    str_out = dic_out + "/stream"
    stream.stream(fac_out, str_out, _number_zones)
    # 河流链接
    stream_link_out = dic_out + "/stream_link"
    streamLink.stream_link(str_out, "fdr", stream_link_out)
    # 河网分级
    stream_order_out = dic_out + "/stream_order"
    streamOrder.stream_order(stream_link_out, "fdr", stream_order_out)
    # 分支开始
    # 生成河网对应点集
    river_corr_point = stream_order_out + ".shp"
    arcConvert.raster_to_point(stream_order_out, river_corr_point)  # 以同名的矢量文件保存
    # 生成河网出流点
    river_outflow_tub, stream_to_feature_out, pour_point_out, erase_out = make_river_outflow_point(stream_order_out,
                                                                                                   dic_out,
                                                                                                   river_corr_point,
                                                                                                   cell_size)
    # 补充河网要素点
    river_feature_points = dic_out + "/river_feature_points.shp"
    #  使用 要素折点转点
    arcDataManagement.feature_vertices_to_points(stream_to_feature_out, 'END', river_feature_points)
    # 分支结束
    # 捕捉倾泻点
    points_out_path = dic_out + "/pour_point.shp"
    snap_pour_point(points_out_path, river_corr_point, river_outflow_tub, river_feature_points)
    # 添加站名站码
    arcpy.AddField_management(points_out_path, "STCD", "TEXT", field_is_nullable="NULLABLE")
    arcpy.AddField_management(points_out_path, "STNAME", "TEXT", field_is_nullable="NULLABLE")
    # 构造流域范围面
    file_in_shp = dic_out + "/global.shp"
    coords_list = [[1, _left, _bottom], [1, _right, _bottom], [1, _right, _top], [1, _left, _top]]
    polygonCreate.polygon(file_in_shp, coords_list)
    # 裁剪村屯
    _village_path_clip = _village_path.replace('.shp', '_clip.shp')
    arcAnalysis.clip(_village_path, file_in_shp, _village_path_clip)
    # 添加村屯
    add_point(points_out_path, erase_out, _village_path_clip, "VILLAGE")
    if _rsvr_file_exist:
        # 裁剪水库
        _rsvr_path_clip = _rsvr_path.replace('.shp', '_clip.shp')
        arcAnalysis.clip(_rsvr_path, file_in_shp, _rsvr_path_clip)
        # 添加水库
        add_point(points_out_path, erase_out, _rsvr_path, "RESERVOIR")
    dem[0].update({"points_out_path": points_out_path.replace(_workspace_path, '')})  # 保存相对路径
    dem[0].update({"stream_order": river_corr_point.replace(_workspace_path, '')})  # 保存相对路径
    dem[0].update({"clip_dem_path": file_in.replace(_workspace_path, '')})  # 保存相对路径

    # 示例使用
    source_directory = dic_out
    destination_directory = _workspace_path + "/data/point/" + _basin_name
    files_to_move = ["pour_point", "river_feature_points", "pour_point.shp", "river_feature_points.shp"]

    move_specific_files(source_directory, destination_directory, files_to_move)
    # 保存字典
    # 指定保存文件的路径
    save_file = "data.pkl"
    save_path = os.path.join(_workspace_path, 'data', save_file)
    # 使用 pickle 保存字典
    with open(save_path, "wb") as f:
        pickle.dump(dem, f)

def break_point_flg():
    pass


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
