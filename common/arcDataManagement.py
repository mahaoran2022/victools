# -*- coding: UTF-8 -*-
# 数据管理工具
from __future__ import print_function
import arcpy
from arcpy import env
import checkFile
import constant
import sp as s


def polygon_to_line(in_feature_path, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_feature = _file
    arcpy.PolygonToLine_management(in_feature, out_feature_path)
    print("面转线成功！")


def feature_to_polygon(in_feature_path, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_feature = _file
    arcpy.FeatureToPolygon_management(in_feature, out_feature_path)
    print("要素转面成功！")


# 融合
# dissolve_field e.g. ["LANDUSE", "TAXCODE"]
# statistics_fields e.g. [[field, {statistic_type}],...]
# statistic_type SUM | MEAN | MIN | MAX | COUNT ...
# multi_part MULTI_PART允许多部分要素 | SINGLE_PART
# unsplit_lines DISSOLVE_LINES将线融合为单个要素 | UNSPLIT_LINES
def dissolve(in_feature_path, out_feature_path, dissolve_fields=None, statistics_fields=None, multi_part=None,
             unsplit_lines=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_feature = _file
    # todo lock
    # checkFile.check_lock_and_wait_second(in_feature_path, 0.2)
    # checkFile.check_lock_and_wait_second(out_feature_path, 0.2)
    arcpy.Dissolve_management(in_feature_path, out_feature_path, dissolve_fields, statistics_fields, multi_part,
                              unsplit_lines)
    print("融合成功！")


def merge(in_feature_paths, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    if in_feature_paths and len(in_feature_paths) > 0:
        _path, _file = s.split(in_feature_paths[0])
        env.workspace = _path
        arcpy.Merge_management(in_feature_paths, out_feature_path)
    print("合并成功！")


# condition: AREA | PERCENT | AREA_AND_PERCENT | AREA_OR_PERCENT
# part_area 消除小于此面积的部分
# part_area_percent 消除小于此要素总外部面积百分比的部分
# part_option CONTAINED_ONLY | ANY
def eliminate_polygon_part(in_feature_path, out_feature_path, condition, part_area, part_area_percent, part_option):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    # 栅格转点要素
    env.workspace = _path
    checkFile.check_lock_and_wait_second(in_feature_path, 2)
    # in_feature = _file
    arcpy.EliminatePolygonPart_management(in_feature_path, out_feature_path, condition
                                          , (part_area if part_area > 0 else "")
                                          , (part_area_percent if part_area_percent > 0 else "")
                                          , part_option)
    print("消除面部件成功！")


# 多部件至单部件
def multipart_to_singlepart(in_feature_path, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    # _path, _file = s.split(in_feature_path)
    # 栅格转点要素
    env.workspace = constant.tempt_workspace_path
    # in_feature = _file
    arcpy.MultipartToSinglepart_management(in_feature_path, out_feature_path)
    print("多部件至单部件成功！")


def minimum_bounding_geometry(in_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    out_feature_path = in_feature_path.replace('.shp', '_min.shp')
    arcpy.MinimumBoundingGeometry_management(in_feature_path, out_feature_path,
                                             "CONVEX_HULL", "NONE")
    print("最小边界几何构建成功!")
    return out_feature_path


def feature_vertices_to_points(in_feature_path, point_location, out_feature_path=None):
    """
    要素折点转点
    point_location:
    ALL —在每个输入要素折点处创建一个点。这是默认设置。
    MID —在每个输入线或面边界的中点（不一定是折点）处创建一个点。
    START —在每个输入要素的起点（第一个折点）处创建一个点。
    END —在每个输入要素的终点（最后一个折点）处创建一个点。
    BOTH_ENDS —在每个输入要素的起始点和终点处各创建一个点，共创建两个点。
    DANGLE —在输入线的起点或终点（如果该点不与另一条线的任何位置相连）创建一个悬挂点。该选项不适用于面输入
    """
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_feature = _file
    if out_feature_path is None:
        out_feature_path = in_feature_path.replace('.shp', '_vertices.shp')
    arcpy.FeatureVerticesToPoints_management(in_feature_path,
                                             out_feature_path,
                                             point_location)
    print("要素折点转点成功!")
    return out_feature_path


def feature_to_point(in_feature_path, out_feature_path, point_location=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    in_features = _file
    arcpy.FeatureToPoint_management(in_features, out_feature_path, point_location)
    print("要素转点成功!")


def copy_raster(in_raster_path, out_raster_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_raster_path)
    env.workspace = _path
    arcpy.CopyRaster_management(in_raster_path, out_raster_path)
    print("复制文件")


def copy(in_feature_path, out_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    checkFile.check_lock_and_wait_second(out_feature_path, 0.2)
    arcpy.Copy_management(in_feature_path, out_feature_path)
    print("复制文件")


def delete(in_feature_path):
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    checkFile.check_lock_and_wait_second(in_feature_path, 0.2)
    arcpy.Delete_management(in_feature_path)
    print("删除文件")


# 添加字段
# field_type TEXT | FLOAT | DOUBLE | SHORT | LONG | DATE | BLOB | RASTER | GUID
# field_precision 可存储在字段中的位数
# field_scale 可存储在字段中的小数位数
def add_field(in_table_path, field_name, field_type, field_precision=None, field_scale=None):
    _path, _in_table = s.split(in_table_path)
    env.workspace = _path
    arcpy.AddField_management(_in_table, field_name, field_type, field_precision, field_scale)


# 计算字段
# expression = "getClass(float(!SHAPE.area!))"
# expression_type = "PYTHON_9.3"
# code_block = """
#     def getClass(area):
#         if area <= 1000:
#             return 1
#         if area > 1000 and area <= 10000:
#             return 2
#         else:
#             return 3"""
def calculate_field(in_table_path, field_name, expression, expression_type, code_block=None):
    _path, _in_table = s.split(in_table_path)
    env.workspace = _path
    arcpy.CalculateField_management(_in_table, field_name, expression, expression_type, code_block)
    print("计算字段填入！")


# 删除字段
# drop_field e.g. [drop_field,...]
def delete_field(in_table_path, drop_field):
    _path, _in_table = s.split(in_table_path)
    env.workspace = _path
    arcpy.DeleteField_management(_in_table, drop_field)
    print("删除字段！")


# 排序
# sort_field [[sort_field, direction],...]
# direction ASCENDING | DESCENDING
def sort_field(in_table_path, sort_field, out_table_path=None):
    _path, _in_table = s.split(in_table_path)
    env.workspace = _path
    if out_table_path is not None:
        arcpy.Sort_management(in_table_path, out_table_path, sort_field)
    else:
        out_table_path = in_table_path.replace('.shp', '.dbf').replace('.dbf', '_tempt.dbf')
        arcpy.Sort_management(in_table_path, out_table_path, sort_field)
        copy(out_table_path, in_table_path)
        delete(out_table_path)
    print("排序！")


# 清除工作空间缓存
def clear_workspace_cache(in_data=None):
    if in_data is not None:
        arcpy.Delete_management("in_memory")
        arcpy.management.ClearWorkspaceCache({in_data})
    else:
        arcpy.Delete_management("in_memory")
        arcpy.ClearWorkspaceCache_management()


# 获得栅格属性
# property_type MINIMUM —输入栅格中所有像元的最小值 | MAXIMUM —输入栅格中所有像元的最大值 | MEAN —输入栅格中所有像元的平均值 | STD —输入栅格中所有像元的标准差
def get_raster_properties(in_raster_path, property_type):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_raster_path)
    env.workspace = _path
    # Get the geoprocessing result object
    _result = arcpy.GetRasterProperties_management(_file, property_type)
    # Get the elevation standard deviation value from geoprocessing result object
    print("获得栅格属性")
    return float(_result.getOutput(0))


def get_count(in_feature_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    # Get the geoprocessing result object
    _result = arcpy.GetCount_management(_file)[0]
    # Get the elevation standard deviation value from geoprocessing result object
    print("矢量文件数")
    return _result


def clip_rectangle(in_feature_path, out_raster, xmin, ymin, xmax, ymax):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    rectangle = str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + str(ymax)
    _result = arcpy.Clip_management(
        _file, rectangle,
        out_raster, "#", "#", "NONE")
    print("剪裁计算成功！" + rectangle)
    return _result


def clip_shp(in_feature_path, out_raster, shp_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_feature_path)
    env.workspace = _path
    _result = arcpy.Clip_management(
        _file, "",
        out_raster, shp_path, "#", "NONE")
    print("剪裁计算成功！")
    return _result


def add_join(in_layer_or_view, in_field, join_table, join_field, out_layer_or_view=None, qualified_field_names=True,
             join_type=None):
    '''
    join_type（可选） 指定如何处理输入中与连接表中的记录相匹配的记录。
        KEEP_ALL —输入图层或表视图中的所有记录都将包含在输出中，也称为外部连接。这是默认设置。
        KEEP_COMMON —只有输入中那些与连接表中行相匹配的记录才会显示在结果中，也称为内部连接。
    '''
    env.overwriteOutput = True  # 允许覆盖
    env.qualifiedFieldNames = qualified_field_names
    _path, _file = s.split(in_layer_or_view)
    env.workspace = _path
    # Create a feature layer
    layerName = "new_layer"
    arcpy.MakeFeatureLayer_management(_file, layerName)
    # Join the feature layer to a table
    arcpy.AddJoin_management(layerName, in_field, join_table, join_field, join_type)
    if out_layer_or_view is None:
        out_layer_or_view = in_layer_or_view.replace('.shp', '_copy.shp')
        arcpy.CopyFeatures_management(layerName, out_layer_or_view)
        arcpy.Copy_management(out_layer_or_view, in_layer_or_view)
        arcpy.Delete_management(out_layer_or_view)
    else:
        arcpy.CopyFeatures_management(layerName, out_layer_or_view)
    print("添加连接计算成功！")


def add_join_table(in_table, in_field, join_table, join_field, out_table=None, join_type=None):
    '''
    join_type（可选） 指定如何处理输入中与连接表中的记录相匹配的记录。
        KEEP_ALL —输入图层或表视图中的所有记录都将包含在输出中，也称为外部连接。这是默认设置。
        KEEP_COMMON —只有输入中那些与连接表中行相匹配的记录才会显示在结果中，也称为内部连接。
    '''
    # 创建表视图
    in_layer_or_view = s.getName(in_table) + '_view'
    arcpy.MakeTableView_management(in_table, in_layer_or_view)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)
    arcpy.CopyRows_management(in_layer_or_view, out_table)
    print("添加连接计算成功！")


def create_file_gdb(tempt_workspace_path):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(tempt_workspace_path)
    # Set workspace
    env.workspace = _path
    # Set local variables
    out_folder_path = _path
    out_name = _file
    # Execute CreateFileGDB
    arcpy.CreateFileGDB_management(out_folder_path, out_name)
    print("创建数据库成功！")


def split_line_at_point(in_features_path, point_features, out_feature_class, search_radius=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(in_features_path)
    env.workspace = _path
    in_features = _file
    arcpy.SplitLineAtPoint_management(in_features, point_features, out_feature_class,
                                      search_radius)
    print("在点处分割线成功！")


def create_fishnet_by_raster(out_feature_path, _raster_path, cell_width, cell_height, number_rows="",
                             number_columns="", corner_coord=None, labels=None, template=None, geometry_type=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(out_feature_path)
    env.workspace = _path
    out_feature_class = _file
    _left = float(arcpy.GetRasterProperties_management(_raster_path, "LEFT").getOutput(0))
    _top = float(arcpy.GetRasterProperties_management(_raster_path, "TOP").getOutput(0))
    _right = float(arcpy.GetRasterProperties_management(_raster_path, "RIGHT").getOutput(0))
    _bottom = float(arcpy.GetRasterProperties_management(_raster_path, "BOTTOM").getOutput(0))
    origin_coord = str(_left) + ' ' + str(_bottom)
    y_axis_coord = str(_left) + ' ' + str(_top)
    print([_left, _right, _bottom, _top])
    arcpy.CreateFishnet_management(out_feature_class, origin_coord, y_axis_coord, cell_width, cell_height, number_rows,
                                   number_columns, corner_coord, labels, _raster_path, geometry_type)
    print("创建渔网成功！")


def create_fishnet(out_feature_path, _in_shp_path, cell_width, cell_height, _precision_num, number_rows="",
                   number_columns="", corner_coord=None, labels=None, template=None, geometry_type=None):
    env.overwriteOutput = True  # 允许覆盖
    _path, _file = s.split(out_feature_path)
    env.workspace = _path
    out_feature_class = _file
    # 备份，虽然文档写这个是只读属性，但是实操的时候属性读过就消失
    _in_shp_path_temp = _in_shp_path.replace('.shp', '_tmp.shp')
    arcpy.CopyFeatures_management(_in_shp_path, _in_shp_path_temp)
    desc = arcpy.Describe(_in_shp_path_temp)
    _left = desc.extent.XMin
    _left = float(int(_left * 10 ** _precision_num)) / 10 ** _precision_num
    _right = desc.extent.XMax
    _right = float(int(_right * 10 ** _precision_num)) / 10 ** _precision_num
    _bottom = desc.extent.YMin
    _bottom = float(int(_bottom * 10 ** _precision_num)) / 10 ** _precision_num
    _top = desc.extent.YMax
    _top = float(int(_top * 10 ** _precision_num)) / 10 ** _precision_num
    print([_left, _right, _bottom, _top])
    origin_coord = str(_left) + ' ' + str(_bottom)
    y_axis_coord = str(_left) + ' ' + str(_top)
    arcpy.CreateFishnet_management(out_feature_class, origin_coord, y_axis_coord, cell_width, cell_height, number_rows,
                                   number_columns, corner_coord, labels, _in_shp_path, geometry_type)
    print("创建渔网成功！")


if __name__ == '__main__':
    in_put = "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/anhui/anhui.imglayer/basin_join.shp"
    out_put = "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/anhui/anhui.imglayer/basin_dissolve.shp"
    dissolve(in_put, out_put, ['to_node'])
    print(out_put)
