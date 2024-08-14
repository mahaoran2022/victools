# -*- coding: UTF-8 -*-
# 流量计算
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def fac(fdr_path, fac_path):
    # 允许覆盖
    env.overwriteOutput = True
    _path, fdr_file = s.split(fdr_path)
    # Set environment settings
    env.workspace = _path
    # Set local variables
    in_flow_direction_raster = fdr_file
    in_weight_raster = ""
    data_type = "FLOAT"
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute FlowAccumulation
    out_flow_accumulation = FlowAccumulation(in_flow_direction_raster, in_weight_raster, data_type)
    # Save the output 
    out_flow_accumulation.save(fac_path)
    print("流量计算成功！")
##m=r"D:\ArcGIS\arcdata\fdr"
##n=r"D:\ArcGIS\arcdata\fac"
##fac(m,n)

