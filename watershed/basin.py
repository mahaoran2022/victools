# -*- coding: UTF-8 -*-
# 生成盆域
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def basin(fdr_path, basin_path):
    # 允许覆盖
    env.overwriteOutput = True

    a, b = s.split(fdr_path)

    arcpy.CheckOutExtension("Spatial")

    env.workspace = a
    # Set local variables
    in_flow_direction_raster = b
    # Execute FlowDirection
    out_basin = Basin(in_flow_direction_raster)
    # Save the output
    out_basin.save(basin_path)
    print("盆域分析成功！")
