# -*- coding: UTF-8 -*-
# 河道定义
import arcpy
from arcpy import env
from arcpy.sa import *
import common.sp as s


def stream(fac_path, con_path, number_zones=None, area=None):
    # 允许覆盖
    env.overwriteOutput = True
    _path, fac_file = s.split(fac_path)
    # 工作空间
    env.workspace = _path
    # 分析，自动分级
    in_raster = fac_file
    if number_zones is None:
        column_value_info = arcpy.GetRasterProperties_management(in_raster, 'COLUMNCOUNT')
        column_value = column_value_info.getOutput(0)
        row_value_info = arcpy.GetRasterProperties_management(in_raster, 'ROWCOUNT')
        row_value = row_value_info.getOutput(0)
        max_value_info = arcpy.GetRasterProperties_management(in_raster, 'MAXIMUM')
        max_value = max_value_info.getOutput(0)
        min_value_info = arcpy.GetRasterProperties_management(in_raster, 'MINIMUM')
        min_value = min_value_info.getOutput(0)
        number_zones = 150
        if max_value == min_value:
            number_zones = 1
        elif number_zones > int(column_value) * int(row_value):
            number_zones = int(column_value) * int(row_value)
        else:
            if area is not None:
                number_zones = get_zone_number_from_area(area)
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    # Execute Slice
    out_slice = None
    print("number_zones:" + str(number_zones))
    if number_zones <= 1:
        out_slice = Slice(in_raster, number_zones, "EQUAL_INTERVAL")
    else:
        out_slice = Slice(in_raster, number_zones, "NATURAL_BREAKS")
    slice_path = fac_path + '1'
    # Save the output 
    out_slice.save(slice_path)

    _path1, slice_file = s.split(slice_path)
    # 筛选，去掉不大于1的部分
    in_raster = slice_file
    # Execute Con
    out_con = Con(in_raster, in_raster, "", "VALUE > 1")
    # Save the outputs 
    out_con.save(con_path)
    print("河道定义成功！")


##m=r"D:\ArcGIS\data\yalujiang.tiftuceng\fac"
##n=r"D:\ArcGIS\data\yalujiang.tiftuceng\str"
##str(m,n)
# 成功！


def get_zone_number_from_area(area):
    if 1 <= area < 50:
        print
        "流域面积∈[1,50)"
        number_zones = 3
    elif 0.5 <= area < 1:
        print
        "流域面积∈[0.5,1)"
        number_zones = 2
    elif 1 <= area < 50:
        print
        "流域面积∈[1,50)"
        number_zones = 3
    elif 50 <= area < 100:
        print
        "流域面积∈[50,100)"
        number_zones = 5
    elif 100 <= area < 500:
        print
        "流域面积∈[100,500)"
        number_zones = 8
    elif 500 <= area < 1000:
        print
        "流域面积∈[500,1000)"
        number_zones = 13
    elif 1000 <= area < 10000:
        print
        "流域面积∈[1k,1w)"
        if 1000 <= area < 5000:
            number_zones = 16
        else:
            number_zones = 21
    elif 10000 <= area < 50000:
        print
        "流域面积∈[1w,5w)"
        if 10000 <= area < 25000:
            number_zones = 26
        else:
            number_zones = 34
    elif 50000 <= area < 100000:
        print
        "流域面积∈[5w,10w)"
        if 50000 <= area < 70000:
            number_zones = 42
        else:
            number_zones = 55
    elif 100000 <= area < 500000:
        print
        "流域面积∈[10w,50w)"
        if 100000 <= area < 250000:
            number_zones = 68
        else:
            number_zones = 89
    elif 500000 <= area < 1500000:
        print
        "流域面积∈[50w,150w)"
        if 100000 <= area < 250000:
            number_zones = 110
        else:
            number_zones = 144
    elif 1500000 <= area < 3000000:
        print
        "流域面积∈[150w,300w)"
        if 1500000 <= area < 2100000:
            number_zones = 178
        else:
            number_zones = 233
    else:
        print
        "流域面积≥300w"
        if 3000000 <= area < 8000000:
            number_zones = 288
        else:
            number_zones = 377
    return number_zones


if __name__ == '__main__':
    stream("D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer/fac"
           , "D:/Workspace/arcgis-workspace/arcpy_workspace/dem/nierjiinput.imglayer/stream")
