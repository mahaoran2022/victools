# -*- coding: UTF-8 -*-
# 栅格转换


# 度转米
def degree_to_meter(cell):
    cell_degree = 0.0008333
    cell_meter = 90
    degree = cell * cell_meter / cell_degree
    if 85 < degree < 95:
        return 90
    elif 25 < degree < 35:
        return 30
    elif 7.5 < degree < 12.5:
        return 10
    elif 2.5 < degree < 7.5:
        return 5
    elif 0.5 < degree < 1.5:
        return 1
    else:
        return degree
    # if abs(cell - cell_degree) < 0.000001:
    #     return cell_meter
    # elif abs(cell - cell_degree / 3) < 0.000001:
    #     return cell_meter / 3   # 30
    # elif abs(cell - cell_degree / 7.2) < 0.000001:
    #     return cell_meter / 7.2   # 12.5
    # elif abs(cell - cell_degree / 9) < 0.000001:
    #     return cell_meter / 9   # 10
    # elif abs(cell - cell_degree / 9) < 0.000001:
    #     return cell_meter / 18   # 5
    # elif abs(cell - cell_degree / 9) < 0.000001:
    #     return cell_meter / 45   # 2
    # elif abs(cell - cell_degree / 90) < 0.000001:
    #     return cell_meter / 90   # 1
    # elif abs(cell - cell_degree / 180) < 0.000001:
    #     return cell_meter / 180   # 0.5
    # else:
    #     return cell / 180
