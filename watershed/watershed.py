# -*- coding: UTF-8 -*-
# 流域边界生成
from __future__ import print_function
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s
import common.checkFile as checkFile


# 参数为输入输出地址
def watershed(_pour_point, _flow_direction_in, _watershed, check_exist, _arcd=None, in_pour_point_field=None):
    if check_exist and checkFile.file_is_exist(_watershed):
        return
    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0

    a, b = s.split(_watershed)
    # Set environment settings
    env.workspace = a
    in_flow_direction = _flow_direction_in
    if _arcd is not None:
        # in_flow_direction = _flow_direction_in
        _flow_direction_out = _flow_direction_in.replace('/fdr', '/f') + _arcd
        # 检查方案锁
        checkFile.check_lock_and_wait_second(_flow_direction_out, 0.2)
        # Copy to cloud raster format
        arcpy.Copy_management(_flow_direction_in, _flow_direction_out)
        # Set local variables
        in_flow_direction = _flow_direction_out
    in_pour_point_data = _pour_point
    if in_pour_point_field is None:
        in_pour_point_field = "FID"
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # 检查方案锁
    checkFile.check_lock_and_wait_second(in_pour_point_data, 2)
    # 栅格对象属性
    raster = Raster(_flow_direction_in)
    # 配置计算范围
    env.extent = raster.extent
    # Execute Watershed
    out_watershed = Watershed(in_flow_direction, in_pour_point_data, in_pour_point_field)
    # 检查方案锁
    checkFile.check_lock_and_wait_second(_watershed, 0.2)
    # Save the output
    out_watershed.save(_watershed)
    if _arcd is not None:
        # Delete Automatically Generated File
        arcpy.Delete_management(in_flow_direction)
    # 恢复默认环境值
    arcpy.ResetEnvironments()
    print("流域生成成功！")

# m=r"D:\ArcGIS\data\yalujiang.tiftuceng\pour"
# p="fdr"
# n=r"D:\ArcGIS\data\yalujiang.tiftuceng\liuyu"
# liuyu(m,p,n)
# dic_out="D:/ArcGIS/nierjiinput.imgtuceng"
# for i in range(1):
#    liuyu_in=dic_out+"/pourpoint"+str(i)+".shp"
#    liuyu_out=dic_out+"/liuyu"+str(i)
#    liuyu(liuyu_in,"fdr",liuyu_out)


def area_watershed(_in_feature, _erase_feature, _out_feature, _delete):
    _path, _file = s.split(_in_feature)
    env.workspace = _path
    erase_input = _file
    erase_feature = _erase_feature
    erase_output = _out_feature
    checkFile.check_lock_batch_and_wait_second([_in_feature, _erase_feature, _out_feature], 0.5)
    arcpy.Erase_analysis(erase_input, erase_feature, erase_output)
    if _delete:
        arcpy.Delete_management(erase_input)
    print("区间流域生成成功！")

