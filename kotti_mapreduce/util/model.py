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
    def get_resource_id(context):
        if hasattr(context, "resource_id"):
            return context.resource_id
        else:
            return get_resource_id(context.parent)

    model = get_resource_model(context)
    resource_id = get_resource_id(context)
    query_filter = methodcaller("filter", model.id == resource_id)
    return get_data(model, query_filter)

def get_context_or_parent(context, context_type):
    if context.type == context_type:
        return context
    else:
        return get_context_or_parent(context.parent, context_type)

def get_context_data(context, context_type, keys):
    if context.type == context_type:
        return attrgetter(*keys)(context)
    else:
        return get_context_data(context.parent, context_type, keys)
