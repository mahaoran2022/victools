# -*- coding: UTF-8 -*-
# 栅格河网矢量化
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def stream_to_feature(stream_order_path, fdr_file, stream_order_feature_path):
    # 参数为输入输出地址
    _path, stream_order_file = s.split(stream_order_path)
    # Set environment settings
    env.workspace = _path
    # Set local variables
    in_stream_raster = stream_order_file
    # Set local variables
    in_flow_direction = fdr_file
    out_stream_feature = stream_order_feature_path

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute
    StreamToFeature(in_stream_raster, in_flow_direction, out_stream_feature, "NO_SIMPLIFY")

    print("河网矢量化")


# if __name__ == "__main__":
#     dic_out = "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer"
#     strTftr_in = dic_out + "/streamorder"
#     strTftr_out = dic_out + "/streamorderfeature" + ".shp"
#     stream_to_feature(strTftr_in, "fdr", strTftr_out)