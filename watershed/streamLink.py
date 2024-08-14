# -*- coding: UTF-8 -*-
# 河流链接
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def stream_link(stream_path, fdr_file, stream_link_path):
    # 允许覆盖
    env.overwriteOutput = True
    # 破解版不允许并行
    env.parallelProcessingFactor = 0
    # 参数为输入输出地址
    _path, stream_file = s.split(stream_path)
    # Set environment settings
    env.workspace = _path
    in_stream_raster = stream_file
    in_flow_direction = fdr_file
    # Check out the ArcGISSpatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute StreamLink
    out_stream_link = StreamLink(in_stream_raster, in_flow_direction)
    # Save the output 
    out_stream_link.save(stream_link_path)
    print("河流链接成功！")
##m=r"D:\ArcGIS\数据\ASTGTM_N29E112W111图层\str"
##p="fdr7"
##n=r"D:\ArcGIS\arcdata\strlink2"
##strlnk(m,p,n)

