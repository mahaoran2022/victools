# -*- coding: UTF-8 -*-
# 流向计算
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


# fill文件也可采用原始dem文件
def fdr(fill_path, fdr_path):
    # 允许覆盖
    env.overwriteOutput = True
    _path, fdr_file = s.split(fill_path)
    # Set environment settings
    env.workspace = _path
    # Set local variables
    in_surface_raster = fdr_file
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute FlowDirection
    out_flow_direction = FlowDirection(in_surface_raster)
    out_flow_direction.save(fdr_path)
    print("流向计算成功！")
    # m="D:/ArcGIS/nierjiinput.imgtuceng/fill"
    # n="D:/ArcGIS/nierjiinput.imgtuceng/fdr"
    # fdr(m,n)
