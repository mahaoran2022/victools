# -*- coding: UTF-8 -*-
# 填洼
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def fill(origin_dem_path, fill_path):
    # 允许覆盖
    env.overwriteOutput = True
    # 参数为输入输出地址
    _path, origin_dem_file = s.split(origin_dem_path)
    # 设置程序输入文件的目录
    env.workspace = _path
    # 设置输入文件（文件名）
    in_surface_raster = origin_dem_file
    # 检查 ArcGIS Spatial Analyst 许可
    arcpy.CheckOutExtension("Spatial")
    # 运行填洼程序
    out_fill = Fill(in_surface_raster)
    # 保存输出
    out_fill.save(fill_path)
    print("填洼成功！")
# m=r"D:\ArcGIS\数据\ASTGTM_N29E112W111.tif"
# n=r"D:\ArcGIS\arcdata\fill"
# fill(m,n)
