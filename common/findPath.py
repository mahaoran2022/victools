# -*- coding: UTF-8 -*-
import common.getTable as getTable


# 找到所有从start到end的路径
def find_all_path(_graph, _start, _end, path=[]):
    path = path + [_start]
    if _start == _end:
        return [path]

    paths = []  # 存储所有路径
    for node in _graph[_start]:
        if node not in path:
            new_paths = find_all_path(_graph, node, _end, path)
            for new_path in new_paths:
                paths.append(new_path)
    return paths


# 各起止节点路径组合
def find_all_path_combination(_graph_json):
    starts = _graph_json['starts']
    ends = _graph_json['ends']
    graph = _graph_json['graph']
    _all_path = []
    for start in starts:
        for end in ends:
            _all_path_one = find_all_path(graph, start, end)
            _all_path.extend(_all_path_one)
    print("查得所有路径组合！")
    return _all_path


# 拓扑图谱
def get_graph(_list, from_node_field, to_node_field):
    _graph_json = {}
    _graph = {}
    _starts = []
    _ends = []
    # # 获得属性列表
    # _list = getTable.get_table_list(_stream_path, None)
    # 遍历属性列表 获得graph start end
    for _map in _list:
        is_start = True
        is_end = True
        if from_node_field in _map and to_node_field in _map:
            if _map[from_node_field] in _graph:
                _graph[_map[from_node_field]].append(_map[to_node_field])
            else:
                to_node_list = []
                to_node_list.append(_map[to_node_field])
                _graph.update({_map[from_node_field]: to_node_list})

            for _map_judge in _list:
                if from_node_field in _map_judge and to_node_field in _map_judge:
                    if _map[from_node_field] == _map_judge[to_node_field]:
                        is_start = False
                    if _map[to_node_field] == _map_judge[from_node_field]:
                        is_end = False
            if is_start:
                _starts.append(_map[from_node_field])
            if is_end:
                _ends.append(_map[to_node_field])
    _graph_json.update({'graph': _graph})
    _graph_json.update({'starts': _starts})
    _graph_json.update({'ends': _ends})
    print("拓扑图谱构造完成！")
    return _graph_json


# 最长路径
def get_longest_path(_list, from_node_field, to_node_field, length_field, _all_path):
    length = 0
    longest_path_list = []
    for _path in _all_path:
        num = len(_path)
        tempt_length = 0
        tempt_longest_path_list = []
        for i in range(num - 1):
            for _map in _list:
                if _map[from_node_field] == _path[i] and _map[to_node_field] == _path[i + 1]:
                    tempt_length += _map[length_field]
                    tempt_longest_path_list.append(_map)
        if tempt_length > length:
            length = tempt_length
            longest_path_list = tempt_longest_path_list
    print("获得最长路径！")
    return length, longest_path_list


if __name__ == '__main__':
    # graph = {'A': ['B', 'C', 'D'],
    #          'B': ['E'],
    #          'C': ['D', 'F'],
    #          'D': ['B', 'E', 'G'],
    #          'E': [],
    #          'F': ['D', 'G'],
    #          'G': ['E']}
    # all_path = find_all_path(graph, 'A', 'G')
    # print(u"\r所有路径：", all_path)

    table_list = [
        {'from_node': '34', 'to_node': '37', 'shape_Length': 0.16268}
        , {'from_node': '27', 'to_node': '37', 'shape_Length': 2.261914}
        , {'from_node': '32', 'to_node': '38', 'shape_Length': 0.705838}
        , {'from_node': '37', 'to_node': '38', 'shape_Length': 0.521631}
        , {'from_node': '38', 'to_node': '40', 'shape_Length': 0.821385}
        , {'from_node': '39', 'to_node': '40', 'shape_Length': 0.346926}
        , {'from_node': '40', 'to_node': '47', 'shape_Length': 0.133914}
    ]
    # 拓扑图谱
    graph_json = get_graph(table_list, 'from_node', 'to_node')
    # 路径组合
    all_path = find_all_path_combination(graph_json)
    # 最长路径
    longest_path, longest_path_list = get_longest_path(table_list, 'from_node', 'to_node', 'shape_Length', all_path)
    print all_path
