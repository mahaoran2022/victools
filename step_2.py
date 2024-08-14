# -*- coding: UTF-8 -*-
import time
import calculate_watershed_v1
import calculate_soil_v1
import create_aoi_grid_v1

def main():
    # step 1:
    calculate_watershed_v1.main()
    # step 2:
    create_aoi_grid_v1.main()
    # step 3:
    calculate_soil_v1.main()
    pass


if __name__ == '__main__':
    start = time.time()
    main()
    # test end
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
