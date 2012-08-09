# -*- coding: utf-8 -*-
from os.path import join as pathjoin
from urlparse import urlparse

from boto.s3.connection import S3Connection

from kotti_mapreduce.util.helper import filter_object_attributes


_S3_CONNECTION_SETTINGS = [
    'aws_access_key_id',
    'aws_secret_access_key',
]

def get_s3_connection(resource):
    settings = filter_object_attributes(resource, _S3_CONNECTION_SETTINGS)
    return S3Connection(**settings)

def get_s3_log_keys(s3_conn, log_uri, jobflow_ids):
    parse_result = urlparse(log_uri)
    bucket = s3_conn.get_bucket(parse_result.netloc)
    keys_list = []
    for jobflow_id in jobflow_ids:
        key_path = pathjoin(parse_result.path[1:], jobflow_id)
        keys_list.append(bucket.list(key_path))
    return keys_list

def get_s3_keys_list(s3_conn, uri_list):
    keys_list = []
    for uri in uri_list:
        parse_result = urlparse(uri)
        bucket = s3_conn.get_bucket(parse_result.netloc)
        keys_list.append(bucket.list(parse_result.path[1:]))
    return keys_list
