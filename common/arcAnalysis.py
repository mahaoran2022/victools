# -*- coding: UTF-8 -*-
import arcpy
from arcpy import env
import common.sp as s
import common.checkFile as checkFile
import common.constant as constant


# 擦除
def erase(_input_path, _erase_path, _output_path):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(_input_path)
    env.workspace = _path
    arcpy.Erase_analysis(_input_path, _erase_path, _output_path, '#')
    print("擦除成功！")


# 更新
# keep_borders BORDERS | NO_BORDERS
# cluster_tolerance 所有要素坐标（节点和折点）之间的最小距离以及坐标可以沿 X 和/或 Y 方向移动的距离
def update(_input_path, _update_path, _output_path, keep_borders=None, cluster_tolerance=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(_input_path)
    # Set the workspace
    env.workspace = _path

    # Process: Update
    arcpy.Update_analysis(_input, _update_path, _output_path, keep_borders, cluster_tolerance)
    print("更新成功！")


# 裁剪
def clip(_input_path, _clip_path, _output_path):
    # 允许覆盖
    env.overwriteOutput = True
    _path, _input = s.split(_input_path)
    env.workspace = _path
    _tempt_input_path = _input_path.replace(".shp", "_tempt.shp")
    checkFile.check_lock_and_wait_second(_tempt_input_path, 0.2)
    # 复制一份 防止出现方案锁
    arcpy.CopyFeatures_management(_input_path, _tempt_input_path)
    # 裁剪时_input会出现方案锁 构造临时的输入文件
    arcpy.Clip_analysis(_tempt_input_path, _clip_path, _output_path)
    # 再将之删除
    arcpy.Delete_management(_tempt_input_path)
    print("裁剪成功！")


def spatial_join(target_feature_path, join_feature_path, out_feature_path
                 , join_operation=None, join_type=None, field_mapping=None, match_option=None, search_radius=None,
                 distance_field_name=None):
    """
    空间连接
    join_operation JOIN_ONE_TO_ONE | JOIN_ONE_TO_MANY
    join_type KEEP_ALL | KEEP_COMMON
    field_mapping
    match_option INTERSECT | CONTAINS | WITHIN ...
    search_radius
    distance_field_name
    """
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(target_feature_path)
    env.workspace = _path
    target_feature = _file
    # todo lock
    # checkFile.check_lock_and_wait_second(join_feature_path, 0.2)
    arcpy.SpatialJoin_analysis(target_feature, join_feature_path, out_feature_path
                               , join_operation, join_type, field_mapping, match_option, search_radius,
                               distance_field_name)
    print('空间连接成功！')


# FID
def feature_to_features(in_features_path=None, field_name=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_features_path)
    # Set the workspace
    env.workspace = _path
    in_features = _file
    rows = arcpy.SearchCursor(in_features)
    if not field_name:
        field_name = 'FID'
    features = []
    for row in rows:
        selected_field_value = row.getValue(field_name)
        where_clause = ''
        if isinstance(selected_field_value, str) or isinstance(selected_field_value, unicode):
            where_clause = field_name + " = '" + bytes(selected_field_value) + "'"
        elif isinstance(selected_field_value, int) or isinstance(selected_field_value, str):
            where_clause = field_name + " = " + bytes(selected_field_value)
        else:
            continue
        out_feature_path = _path + "/" + bytes(selected_field_value) + ".shp"
        arcpy.Select_analysis(in_features, out_feature_path, where_clause)
        features.append(out_feature_path)
    if len(features) > 0:
        print('按字段分割矢量成功！')
    else:
        features.append(in_features_path)
        print('按字段分割矢量失败！')
    return features


def select(in_features_path, out_feature_path, where_clause):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_features_path)
    # Set the workspace
    env.workspace = _path
    arcpy.Select_analysis(in_features_path, out_feature_path, where_clause)
    print('选择成功！')


# 邻近
def near(in_features_path, near_features_path, search_radius):
    env.overwriteOutput = True  # 允许覆盖
    _path, in_features = s.split(in_features_path)
    env.workspace = _path
    arcpy.Near_analysis(in_features, near_features_path, search_radius)
    print("邻近成功！")


# 乘
def times(in_raster_path, in_constant, out_raster):
    env.overwriteOutput = True  # 允许覆盖
    _path, in_raster = s.split(in_raster_path)
    env.workspace = _path
    arcpy.Times_3d(in_raster, in_constant, out_raster)
    print("乘成功！")


def point_distance(in_feature_path, near_features, out_table, search_radius=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_features = _file
    # Execute PointDistance
    arcpy.PointDistance_analysis(in_features, near_features, out_table, search_radius)
    print('点距离计算成功！')


def intersect(in_features_path, out_feature_class, join_attributes=None, cluster_tolerance=None, output_type=None):
    env.overwriteOutput = True  # 允许覆盖
    in_features = []
    for in_feature in in_features_path:
        _path, _file = s.split(in_feature)
        in_features.append(_file)
    env.workspace = _path
    arcpy.Intersect_analysis(in_features, out_feature_class, join_attributes, cluster_tolerance, output_type)
    print('相交分析计算成功！')
