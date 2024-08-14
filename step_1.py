# -*- coding: UTF-8 -*-
import calculate_junction_v1
import time


def main():
    calculate_junction_v1.main()


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('Running time: %s Seconds' % (end - start))
