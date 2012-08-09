# -*- coding: utf-8 -*-
from operator import attrgetter
from operator import methodcaller

from kotti import DBSession

from kotti_mapreduce.resources import EMRJobResource

def get_data(model, query_filter):
    session = DBSession()
    query = query_filter(session.query(model))
    return query.first()

def get_all_data(model, context=None, order_by=None, limit=None):
    """
    Get all data from model in given context.
    """
    session = DBSession()
    query = session.query(model)
    if context is not None:
        query = query.filter(model.parent_id == context.id)
    if order_by:
        query = order_by(query)
    if limit:
        query.limit(limit)
    data = query.all()
    return data

def get_resource_model(context):
    cloud_vendor = get_context_data(context, 'jobcontainer', ['cloud_vendor'])
    resource = None
    if cloud_vendor == u'aws':
        resource = EMRJobResource
    return resource

def get_resource(context):
    model = get_resource_model(context)
    if hasattr(context, "resource_id"):
        resource_id = context.resource_id
    else:
        resource_id = context.parent.resource_id
    query_filter = methodcaller("filter", model.id == resource_id)
    return get_data(model, query_filter)


def get_context_data(context, context_type, keys):
    if context.type != context_type:
        return get_context_data(context.parent, context_type, keys)
    else:
        return attrgetter(*keys)(context)
