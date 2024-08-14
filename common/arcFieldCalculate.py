# -*- coding: UTF-8 -*-

import arcpy
from arcpy import env
import common.sp as s


# ACRES | ARES | HECTARES | SQUARECENTIMETERS | SQUAREDECIMETERS | SQUAREINCHES | SQUAREFEET | SQUAREKILOMETERS | SQUAREMETERS | SQUAREMILES | SQUAREMILLIMETERS | SQUAREYARDS | SQUAREMAPUNITS
def get_area(shape_address, field_name, unit):
    # field_name = field_name.upper()
    _exist = field_exist(shape_address, field_name)
    if not _exist:
        arcpy.AddField_management(shape_address, field_name, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(shape_address, field_name, "!shape.geodesicArea@" + unit + "!", "PYTHON_9.3")
    print "面积计算完成！"


# CENTIMETERS | DECIMALDEGREES | DECIMETERS | FEET | INCHES | KILOMETERS | METERS | MILES | MILLIMETERS | NAUTICALMILES | POINTS | UNKNOWN | YARDS
def get_length(shape_address, field_name, unit):
    # field_name = field_name.upper()
    _exist = field_exist(shape_address, field_name)
    if not _exist:
        arcpy.AddField_management(shape_address, field_name, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(shape_address, field_name, "!shape.geodesicLength@" + unit + "!", "PYTHON_9.3")
    print "长度计算完成！"


def set_area_percent(shape_address, area_field_name, area, percent_field_name):
    _exist = field_exist(shape_address, percent_field_name)
    if not _exist:
        arcpy.AddField_management(shape_address, percent_field_name, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # cursor = arcpy.UpdateCursor(shape_address)
    _fields = []
    _fields.append(area_field_name)
    _fields.append(percent_field_name)
    with arcpy.da.UpdateCursor(shape_address, _fields) as cursor:
        # Update the road buffer distance field based on road type.
        #   Road type is either 1,2,3,4  Distance is in meters.
        for row in cursor:
            # row.setValue(percent_field_name, row.getValue(area_field_name) / area)
            row[1] = row[0] / area
            cursor.updateRow(row)
    print "百分比添加完成！"


def field_exist(shape_address, field_name):
    a, b = s.split(shape_address)
    env.workspace = a
    desc = arcpy.Describe(shape_address)
    # field_name = field_name.upper()
    for field in desc.fields:
        if field.Name.upper() == field_name.upper():
            return True
            break
    return False


def add_text_field(shape_address, field_name):
    _exist = field_exist(shape_address, field_name)
    if not _exist:
        arcpy.AddField_management(shape_address, field_name, "TEXT")
