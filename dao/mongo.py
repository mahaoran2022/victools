# -*- coding: UTF-8 -*-

import pymongo
from urllib import quote_plus
import common.constant as constant

the_user = constant.mongodb_connection['user']
the_password = constant.mongodb_connection['password']
the_host = constant.mongodb_connection['host'] + ':' + bytes(constant.mongodb_connection['port'])
the_port = constant.mongodb_connection['port']
the_db = constant.mongodb_connection['db']

the_uri = "mongodb://%s:%s@%s" % (quote_plus(the_user), quote_plus(the_password), the_host)

static_collections = [
    {
        "collection": "basin",
        "indices": [{"index": [("code", 1), ("dem", 1)], "index_unique": True, "index_name": "baisn_code_dem"}]
    },
    {
        "collection": "dem",
        "indices": [{"index": [("dem", 1)], "index_unique": True, "index_name": "dem_dem"}]
    },
    {
        "collection": "thiessen",
        "indices": [{"index": [("arcd", 1)], "index_unique": True, "index_name": "thiessen_arcd"}]
    },
    {
        "collection": "hand_drawn_watershed_property",
        "indices": [{"index": [("arcd", 1)], "index_unique": True, "index_name": "hand_drawn_watershed_property_arcd"}]
    },
    {
        "collection": "uploaded_watershed_property",
        "indices": [{"index": [("arcd", 1)], "index_unique": True, "index_name": "uploaded_watershed_property_arcd"}]
    },
    {
        "collection": "boundary",
        "indices": [{"index": [("boundary", 1)], "index_unique": True, "index_name": "boundary_boundary"}]
    },
    {
        "collection": "contour",
        "indices": [{"index": [("begtime", 1), ("endtime", 1), ("boundary", 1), ("type", 1)], "index_unique": True,
                     "index_name": "contour_begtime_endtime_boundary"}]
    },
    {
        "collection": "model_parameter_topmodel",
        "indices": [{"index": [("arcd", 1), ("dem", 1)], "index_unique": True,
                     "index_name": "model_parameter_topmodel_arcd_dem"}]
    },
    {
        "collection": "model_parameter_giuh",
        "indices": [{"index": [("arcd", 1), ("dem", 1), ("overland_flow_threshold", 1)], "index_unique": True,
                     "index_name": "model_parameter_giuh_arcd_dem_threshold"}]
    },
    {
        "collection": "model_parameter_slope_for_giuh",
        "indices": [{"index": [("arcd", 1), ("dem", 1)], "index_unique": True,
                     "index_name": "model_parameter_slope_for_giuh_arcd_dem"}]
    },
    {
        "collection": "soil_texture",
        "indices": [{"index": [("soil_texture", 1)], "index_unique": True, "index_name": "soil_texture_soil_texture"}]
    },
    {
        "collection": "model_parameter_horton",
        "indices": [{"index": [("arcd", 1), ("soil_texture", 1)], "index_unique": True,
                     "index_name": "model_parameter_horton_arcd_soil_texture"}]
    },
    {
        "collection": "soil_type_data",
        "indices": [{"index": [("soil_type_code", 1)], "index_unique": True, "index_name": "soil_type_data_code"}]
    },
    {
        "collection": "soil_type_to_hydraulic_parameter",
        "indices": [{"index": [("soil_type_code", 1)], "index_unique": True,
                     "index_name": "soil_type_to_hydraulic_parameter_code"}]
    },
    {
        "collection": "soil_type_to_loss_parameter",
        "indices": [
            {"index": [("soil_type_code", 1)], "index_unique": True, "index_name": "soil_type_to_loss_parameter_code"}]
    },
    {
        "collection": "model_parameter_loss",
        "indices": [{"index": [("arcd", 1), ("soil_texture", 1)], "index_unique": True,
                     "index_name": "model_parameter_loss_arcd_soil_texture"}]
    },
    {
        "collection": "land_use",
        "indices": [{"index": [("land_use", 1)], "index_unique": True, "index_name": "land_use_land_use"}]
    },
    {
        "collection": "land_use_and_soil_unit_to_cn",
        "indices": [{"index": [("land_use_first_code", 1), ("land_use_second_code", 1), ("hydro_condition", 1)],
                     "index_unique": True, "index_name": "land_use_and_soil_unit_to_cn_land_use"}]
    },
    {
        "collection": "soil_unit_from_saturated_hydraulic_conductivity",
        "indices": [{"index": [("soil_unit", 1)], "index_unique": True, "index_name": "soil_unit_soil_unit"}]
    },
    {
        "collection": "model_parameter_scs",
        "indices": [{"index": [("arcd", 1), ("dem", 1), ("land_use", 1), ("soil_texture", 1)], "index_unique": True,
                     "index_name": "model_parameter_scs_arcd_dem_land_use_soil_texture"}]
    },
    {
        "collection": "uploaded_basin",
        "indices": [{"index": [("shapefile_name", 1), ("the_id", 1)], "index_unique": True,
                     "index_name": "uploaded_basin_shapefile_name"}]
    }
]


def create_db(connection, _db):
    connection[_db]


def create_collection(db, _collection):
    db[_collection]
    collection = db.get_collection(_collection)
    for static_collection in static_collections:
        if _collection == static_collection['collection']:
            if static_collection['indices']:
                for index in static_collection['indices']:
                    if index['index_unique'] and index['index_unique'] is True:
                        if index['index_name']:
                            collection.create_index(index['index'], unique=True, name=index['index_name'])
                        else:
                            collection.create_index(index['index'], unique=True)
                    else:
                        if index['index_name']:
                            collection.create_index(index['index'], name=index['index_name'])
                        else:
                            collection.create_index(index['index'])


def query_list(_collection, _query):
    return query_list_with_db(the_db, _collection, _query)


def query_list_with_db(_db, _collection, _query):
    connection = pymongo.MongoClient(the_uri, the_port)
    db = connection.get_database(_db)
    collection = db.get_collection(_collection)
    json_list = []
    for json in collection.find(_query):
        json_list.append(json)
    connection.close()
    return json_list


def query_one(_collection, _query):
    return query_one_with_db(the_db, _collection, _query)


def query_one_with_db(_db, _collection, _query):
    connection = pymongo.MongoClient(the_uri, the_port)
    db = connection.get_database(_db)
    collection = db.get_collection(_collection)
    json = collection.find_one(_query)
    connection.close()
    return json


def insert_batch(_collection, json):
    return insert_batch_with_db(the_db, _collection, json)


def insert_batch_with_db(_db, _collection, json):
    connection = pymongo.MongoClient(the_uri, the_port)
    db_list = connection.list_database_names()
    if _db in db_list:
        print("数据库已存在！")
    else:
        create_db(connection, _db)
    db = connection.get_database(_db)
    collection_list = db.list_collection_names()
    if _collection in collection_list:
        print("集合已存在！")
    else:
        create_collection(db, _collection)
    collection = db.get_collection(_collection)
    collection.insert(json)
    print("数据插入完成！")
    connection.close()


def update_one(_collection, _query_json):
    return update_one_with_db(the_db, _collection, _query_json)


def update_one_with_db(_db, _collection, _query_json):
    connection = pymongo.MongoClient(the_uri, the_port)
    db = connection.get_database(_db)
    collection = db.get_collection(_collection)
    collection.update_one(_query_json['query'], _query_json['set'])
    print("数据更新完成！")
    connection.close()


def delete_batch(_collection, _query):
    return delete_batch_with_db(the_db, _collection, _query)


def delete_batch_with_db(_db, _collection, _query):
    connection = pymongo.MongoClient(the_uri, the_port)
    db = connection.get_database(_db)
    collection = db.get_collection(_collection)
    collection.delete_many(_query)
    print("数据删除成功！")
    connection.close()


if __name__ == '__main__':
    # query_list('geo', 'dem', {'dem': 'nierji'})
    _query = {'boundary': 'songliao', 'boundary_path': 'boundary/songliao_polygon.shp'}
    insert_batch('boundary', _query)
