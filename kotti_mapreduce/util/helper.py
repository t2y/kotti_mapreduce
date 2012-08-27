# -*- coding: utf-8 -*-
import tempfile
from operator import methodcaller
from StringIO import StringIO

from dateutil import tz
from dateutil.parser import parse as date_parser


def get_object_attributes(obj, attr_names, default=u''):
    return [(name, getattr(obj, name, default)) for name in attr_names]

def filter_object_attributes(obj, attr_names, default=u''):
    return dict(filter(lambda t: t[1],
                get_object_attributes(obj, attr_names, default)))

_CONVERT_DATETIME_ATTRS = [
    'creationdatetime',
    'startdatetime',
    'enddatetime',
]

def convert_local_datetime(jobflows, attr_names=_CONVERT_DATETIME_ATTRS,
                           tz_name='Asia/Tokyo', fmt='%Y/%m/%d %H:%M:%S'):
    format_date = methodcaller('strftime', fmt)
    for job in jobflows:
        for name in attr_names:
            local_dt = get_local_datetime(getattr(job, name, u''), tz_name)
            local_datetime = format_date(local_dt) if local_dt else u''
            setattr(job, name, local_datetime)

def get_local_datetime(dt_str, tz_name):
    """
    >>> local_dt = get_local_datetime(u'2012-07-19T05:04:28Z', 'Asia/Tokyo')
    >>> local_dt.tzname()
    'JST'
    >>> local_dt.hour
    14
    >>> get_local_datetime('', 'Asia/Tokyo')
    u''
    """
    local_dt = u''
    if dt_str:
        dt = date_parser(dt_str)
        local_dt = dt.astimezone(tz.gettz(tz_name))
    return local_dt

_SOFTLIMIT_FILE_SIZE = 10485760  # 10MB
_HARDLIMIT_FILE_SIZE = 1073741824  # 1GB

def get_temporary_file(size):
    if size < _SOFTLIMIT_FILE_SIZE:
        fp = StringIO()
    elif size < _HARDLIMIT_FILE_SIZE:
        fp = tempfile.TemporaryFile()
    else:
        fp = None
    return fp
