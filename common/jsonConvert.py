# -*- coding: UTF-8 -*-
import json


def jsonfile_to_json_str(_path):
    s = jsonfile_to_json(_path)
    s = json.dumps(s)
    return s


def jsonfile_to_json(_path):
    f = file(_path)
    s = json.load(f)
    return s


def json_to_string(_json):
    s = json.dumps(_json)
    return s


def esri_to_geo(esri_json):
    geo_json = {}
    geo_json.update({'type': 'FeatureCollection'})
    geo_features = []
    if 'features' in esri_json:
        esri_features = esri_json['features']
        if type(esri_features) is 'list':
            for esri_feature in esri_features:
                geo_feature = {}
                geo_feature.update({'type': 'Feature'})
                if 'attributes' in esri_feature:
                    geo_feature.update({'properties': esri_feature['attributes']})
                if 'geometry' in esri_feature:
                    geometry = esri_feature['geometry']
                    if 'x' in geometry:
                        geo_feature.update({'geometry': geo_point(geometry)})
                    elif 'points' in geometry:
                        geo_feature.update({'geometry': geo_points(geometry)})
                    elif 'paths' in geometry:
                        geo_feature.update({'geometry': geo_line(geometry)})
                    elif 'rings' in geometry:
                        geo_feature.update({'geometry': geo_polygon(geometry)})
                geo_features.append(geo_feature)
    geo_json.update({'features': geo_features})
    return geo_json


def geo_to_esri(geo_json, id_attribute):
    esri_json = get_esri_geo(geo_json, id_attribute)
    spatial_reference = {}
    spatial_reference.update({'wkid': 4326})
    esri_json.update({'spatialReference': spatial_reference})
    return esri_json


def get_esri_geo(geo_json, id_attribute):
    esri_json = {}
    id_attribute = id_attribute if id_attribute is not None else 'OBJECTID'
    if 'type' in geo_json:
        _type = geo_json['type']
        if _type == 'Point':
            coords = geo_json['coordinates']
            esri_json.update({'x': coords[0]})
            esri_json.update({'y': coords[1]})
        elif _type == 'MultiPoint':
            esri_json.update({'points': geo_json['coordinates']})
        elif _type == 'LineString':
            coords_list = []
            coords_list.append(geo_json['coordinates'])
            esri_json.update({'paths': coords_list})
        elif _type == 'MultiLineString':
            esri_json.update({'paths': geo_json['coordinates']})
        elif _type == 'Polygon':
            coordinates = geo_json['coordinates']
            rings = orient_rings(coordinates)
            esri_json.update({'rings': rings})
        elif _type == 'MultiPolygon':
            multi_coordinates = geo_json['coordinates']
            multi_rings = flatten_multipolygon_rings(multi_coordinates)
            esri_json.update({'rings': multi_rings})
        elif _type == 'Feature':
            if 'geometry' in geo_json:
                geometry = get_esri_geo(geo_json['geometry'], id_attribute)
                esri_json.update({'geometry': geometry})
            if 'properties' in geo_json:
                properties = geo_json['properties']
                if 'id' in properties:
                    properties.update({id_attribute: geo_json['id']})
                esri_json.update({'attributes': properties})
        elif _type == 'FeatureCollection':
            esri_features = []
            if 'features' in geo_json:
                geo_features = geo_json['features']
                for geo_feature in geo_features:
                    esri_features.append(get_esri_geo(geo_feature, id_attribute))
            esri_json.update({'features': esri_features})
            esri_json.update({'geometryType': 'esriGeometryPolygon'})
        elif _type == 'GeometryCollection':
            esri_features_collection = []
            if 'geometries' in geo_json:
                geometries = geo_json['geometries']
                for geometry in geometries:
                    esri_features_collection.append(get_esri_geo(geometry, id_attribute))
            esri_json.update({'geometries': esri_features_collection})
        esri_json.update({'geometryType': 'esriGeometryPolygon'})
    return esri_json


def geo_point(geometry):
    esri_geo = {}
    esri_geo.update({'type': 'point'})
    coords = []
    if 'x' in geometry:
        x = geometry['x']
        y = geometry['y']
        coords.append(x)
        coords.append(y)
    esri_geo.update({'coordinates': coords})
    return esri_geo


def geo_points(geometry):
    esri_geo = {}
    if 'points' in geometry:
        points = geometry['points']
        if len(points) == 1:
            esri_geo.update({'type': 'Point'})
            esri_geo.update({'coordinates': points[0]})
        else:
            esri_geo.update({'type': 'MultiPoint'})
            esri_geo.update({'coordinates': points})
    return esri_geo


def geo_line(geometry):
    esri_geo = {}
    if 'paths' in geometry:
        paths = geometry['paths']
        if len(paths) == 1:
            esri_geo.update({'type': 'LineString'})
            esri_geo.update({'coordinates': paths[0]})
        else:
            esri_geo.update({'type': 'MultiLineString'})
            esri_geo.update({'coordinates': paths})
    return esri_geo


def geo_polygon(geometry):
    esri_geo = {}
    if 'rings' in geometry:
        rings = geometry['rings']
        if len(rings) == 1:
            esri_geo.update({'type': 'Polygon'})
            esri_geo.update({'coordinates': rings})
        else:
            coords = []
            _type = ''
            _len = len(coords) - 1
            for ring in rings:
                if ring_is_clockwise(ring):
                    item = [ring]
                    _len += 1
                else:
                    coords[_len].append(ring)
            if len(coords) == 1:
                _type = 'Polygon'
            else:
                _type = 'MultiPolygon'
            esri_geo.update({'type': _type})
            esri_geo.update({'coordinates': (coords[0] if len(coords) == 1 else coords)})
    return esri_geo


def ring_is_clockwise(rings):
    total = 0
    pt1 = []
    pt2 = []
    _len = len(rings) - 1
    for i in range(_len):
        pt1 = rings[i]
        pt2 = rings[i + 1]
        total += (pt2[0] - pt1[0]) * (pt2[1] + pt1[1])
    return total >= 0


def orient_rings(polygon):
    rings_list = []
    outer_ring = close_ring(polygon[0])
    if len(outer_ring) >= 4:
        if not ring_is_clockwise(outer_ring):
            outer_ring.reverse()
        rings_list.append(outer_ring)
        del polygon[0]
        for hole in polygon:
            hole = close_ring(hole)
            if len(hole) >= 4:
                if ring_is_clockwise(hole):
                    hole.reverse()
                rings_list.append(hole)
    return rings_list


def close_ring(coords):
    if not points_equal(coords[0], coords[len(coords) - 1]):
        coords.append(coords[0])
    return coords


def points_equal(a, b):
    _len = len(a)
    for i in range(_len):
        if cmp(a[i], b[i]) != 0:
            return False
    return True


def flatten_multipolygon_rings(rings):
    polygon_list = []
    for ring in rings:
        polygons = orient_rings(ring)
        _len = len(polygons) - 1
        for i in range(_len, -1, -1):
            polygon = polygons[i]
            polygon_list.append(polygon)
    return polygon_list
