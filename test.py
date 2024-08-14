# -*- coding: UTF-8 -*-
import sys
import pdb
import shutil

import common.data as _data
import common.arcUtils as arcUtils
import numpy as np
import calculate_soil


def break_point_flag():
    pass


def breakpoint():
    pdb.set_trace()


def create_file():
    with open('C:/Users/xiong/Desktop/aaaaa.txt', 'w') as f:
        lines = ['Hello, world!', 'Welcome to Python']
        f.writelines(lines)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    dic_out = 'C:/work/vic-tool-py-data/watershed/shizihe/calculate'
    grid_path = dic_out + "/grid.shp"
    watershed_path = dic_out + "/watershed.shp"
    watershed_bak_path = watershed_path.replace('.shp', '_bak.shp')
    river_path = dic_out + "/river.shp"  # 河道不打断
    river_break_path = dic_out + "/river_break.shp"  # 河道打断
    river_bak_path = river_path.replace('.shp', '_bak.shp')
    dpt_point_path = dic_out + '/pour_point_dpt.shp'
    basin_path = dic_out + "/basin.shp"  # 流量边界矢量文件 basin.shp
    sj_basin_grid = dic_out + "/sj_basin_grid.shp"
    grid_clip_path = dic_out + "/grid_clip.shp"
    vic_path = dic_out + "/vic"
    #########################
    calculate_soil.generate_grid_file(grid_clip_path, vic_path)
