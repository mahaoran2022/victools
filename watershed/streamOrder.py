# -*- coding: UTF-8 -*-
# 河网分级
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def stream_order(stream_link_path, fdr_file, stream_order_path):
    _path, stream_link_file = s.split(stream_link_path)
    # Set environment settings
    env.workspace = _path
    # Set local variables
    in_stream_Link_raster = stream_link_file
    in_flow_direction_raster = fdr_file
    order_method = "STRAHLER"
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute StreamOrder
    out_stream_order = StreamOrder(in_stream_Link_raster, in_flow_direction_raster, order_method)
    # Save the output 
    out_stream_order.save(stream_order_path)
    print("河网分级成功！")
# m=r"D:\ArcGIS\数据\ASTGTM_N29E112W111图层\strlink"
# p="fdr7"
# n=r"D:\ArcGIS\arcdata\hewang"
# hewang(m,p,n)

