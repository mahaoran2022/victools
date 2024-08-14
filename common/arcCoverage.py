# -*- coding: UTF-8 -*-
import arcpy
from arcpy import env
import common.sp as s
import arcpy.cartography as cartography


# POINT_REMOVE | BEND_SIMPLIFY | WEIGHTED_AREA | EFFECTIVE_AREA
#  | 0.005 |  |
def simplify_polygon(in_feature_path, out_feature_path, algorithm, tolerance):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    in_feature = _file
    cartography.SimplifyPolygon(in_feature, out_feature_path, algorithm, tolerance, '', '', 'NO_KEEP')
    # 移除多余字段
    arcpy.DeleteField_management(out_feature_path,
                                 ['ID_1', 'Join_Count', 'TARGET_FID', 'ORIG_FID', 'InPoly_FID', 'SimPgnFlag',
                                  'MaxSimpTol', 'MinSimpTol'])
    print('简化面成功！')


def point_distance(in_feature_path, to_cover, out_info_table, search_radius=""):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    from_cover = _file
    # Execute PointDistance
    arcpy.PointDistance_arc(from_cover, to_cover, out_info_table, search_radius)
    print('点距离计算成功！')


def dissolve(in_feature_path, out_cover, dissolve_item, feature_type=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_cover = _file
    # Execute Dissolve
    arcpy.Dissolve_arc(in_cover, out_cover, dissolve_item, feature_type)
    print('融合成功！')
