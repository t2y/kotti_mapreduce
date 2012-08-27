# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import ifilterfalse
from operator import attrgetter
from operator import itemgetter
from operator import methodcaller

from boto.ec2.regioninfo import RegionInfo
from boto.emr import BootstrapAction
from boto.emr.connection import EmrConnection
from boto.emr.step import JarStep
from boto.emr.step import ScriptRunnerStep
from boto.emr.step import StreamingStep

from kotti_mapreduce.resources import Bootstrap
from kotti_mapreduce.util.helper import convert_local_datetime
from kotti_mapreduce.util.helper import filter_object_attributes
from kotti_mapreduce.util.model import get_data


_EMR_CONNECTION_SETTINGS = [
    'aws_access_key_id',
    'aws_secret_access_key',
]

# http://docs.amazonwebservices.com/general/latest/gr/rande.html#emr_region
_EMR_REGION_TO_ENDPOINT = {
    'us-east-1': 'elasticmapreduce.us-east-1.amazonaws.com',
    'us-west-1': 'elasticmapreduce.us-west-1.amazonaws.com',
    'us-west-2': 'elasticmapreduce.us-west-2.amazonaws.com',
    'eu-west-1': 'elasticmapreduce.eu-west-1.amazonaws.com',
    'ap-southeast-1': 'elasticmapreduce.ap-southeast-1.amazonaws.com',
    'ap-northeast-1': 'elasticmapreduce.ap-northeast-1.amazonaws.com',
    'sa-east-1': 'elasticmapreduce.sa-east-1.amazonaws.com',
}

def get_emr_connection(resource):
    settings = filter_object_attributes(resource, _EMR_CONNECTION_SETTINGS)
    if resource.region:
        region = RegionInfo(name=resource.region,
                            endpoint=_EMR_REGION_TO_ENDPOINT[resource.region])
        settings.update(region=region)
    return EmrConnection(**settings)

_SHOW_EMR_OBJECT_ATTRS = [
    'jobflowid',
    'state',
    'keepjobflowalivewhennosteps',
    'creationdatetime',
    'startdatetime',
    'enddatetime',
    'steps',
    'bootstrapactions',
]

_SHOW_EMR_STEPS_OBJECT_ATTRS = [
    'name',
    'state',
    'jar',
    'startdatetime',
    'enddatetime',
    'args',
]

_SHOW_EMR_BOOTSTRAPS_OBJECT_ATTRS = [
    'name',
    'path',
    'args',
]

_SHOW_EMR_STEP_ARGS_OBJECT_ATTRS = [
    'value',
]

def serialize_emr_obj(jobflow, attr_names=_SHOW_EMR_OBJECT_ATTRS):
    def serialize(attr_names, steps_or_args):
        return [serialize_emr_obj(attr, attr_names) for attr in steps_or_args]

    data = []
    for name in attr_names:
        attr = getattr(jobflow, name, u'')
        if name == 'steps':
            convert_local_datetime(attr)
            attr = serialize(_SHOW_EMR_STEPS_OBJECT_ATTRS, attr)
        elif name == 'bootstrapactions':
            attr = serialize(_SHOW_EMR_BOOTSTRAPS_OBJECT_ATTRS, attr)
        elif name == 'args':
            args = serialize(_SHOW_EMR_STEP_ARGS_OBJECT_ATTRS, attr)
            attr = u" ".join(map(itemgetter('value'), args))
        data.append((name, attr))
    return dict(data)

def get_jobflows_for_json(emr_conn, jobflow_ids=None, is_all=False):
    jobflows = []
    if is_all:
        jobflows = emr_conn.describe_jobflows()
    elif jobflow_ids:
        jobflows = emr_conn.describe_jobflows(jobflow_ids=jobflow_ids)
    convert_local_datetime(jobflows)  # FIXME: pass tzinfo
    res_jobflows = map(serialize_emr_obj, jobflows)
    return res_jobflows

def get_jobflow_ids(context):
    if hasattr(context, 'jobflow_id'):
        jobflow_ids = [context.jobflow_id] if context.jobflow_id else []
    else:
        getter = attrgetter('jobflow_id')
        jobflow_ids = filter(None, map(getter, context.children))
    return jobflow_ids

def is_runnable_jobflow(context):
    def is_runnable_state(state):
        return state in (u'', u'STARTING', u'WAITING', u'RUNNING')

    is_runnable = False
    target_steps = list(ifilterfalse(attrgetter('step_run'), context.children))
    if target_steps and is_runnable_state(context.state):
        is_runnable = True
    return is_runnable

def get_jobstep_type(jobtype):
    if jobtype == u'hive':
        return ScriptRunnerStep
    elif jobtype == u'streaming':
        return StreamingStep
    elif jobtype == u'custom-jar':
        return JarStep
    else:
        raise NotImplemented('Unsupported jobtype')


_JOBSTEP_NAME = '{0} from kotti_mapreduce {1}'

def _get_jobstep_name(name_template, num, now):
    return name_template.format('Step {0}'.format(num), now)

def make_hive_jobsteps(now, resource, steps, hive_site, need_preprocessing):
    class ExtraStep(object):
        def __init__(self, step_name, step_args):
            self.step_name = step_name
            self.step_args = step_args

    def insert_setup_hive_step(steps, resource):
        version = u''
        if resource.hive_versions:
            version = u'--hive-versions\n{0}'.format(resource.hive_versions)
        setup_hive_step = ExtraStep(
            '{0} Setup Hive from kotti_mapreduce {1}',
            """
            s3://us-east-1.elasticmapreduce/libs/hive/hive-script
            --base-path
            s3://us-east-1.elasticmapreduce/libs/hive/
            --install-hive
            {0}
            """.format(version)
        )
        steps.insert(0, setup_hive_step)

    def insert_install_hive_site(steps, hive_site):
        install_hive_site_step = ExtraStep(
            '{0} Install Hive Site from kotti_mapreduce {1}',
            """
            s3://us-east-1.elasticmapreduce/libs/hive/hive-script
            --base-path
            s3://us-east-1.elasticmapreduce/libs/hive/
            --install-hive-site
            --hive-site={0}
            """.format(hive_site)
        )
        steps.insert(0, install_hive_site_step)

    # preprocessing for hive application
    # take care in the processing order about steps.insert(0, extra_step)
    if need_preprocessing:
        if hive_site:
            insert_install_hive_site(steps, hive_site)
        insert_setup_hive_step(steps, resource)

    job_steps = []
    for i, step in enumerate(steps):
        _name = step.step_name if step.step_name else _JOBSTEP_NAME
        step.step_name = _get_jobstep_name(_name, i, now)
        script_step = ScriptRunnerStep(name=step.step_name,
                        action_on_failure=resource.action_on_failure,
                        step_args=step.step_args.split())
        job_steps.append(script_step)
    return job_steps

def make_streaming_jobsteps(now, resource, steps):
    job_steps = []
    for i, step in enumerate(steps):
        step.step_name = _get_jobstep_name(_JOBSTEP_NAME, i, now)
        stream_step = StreamingStep(name=step.step_name,
                        action_on_failure=resource.action_on_failure,
                        mapper=step.mapper,
                        reducer=step.reducer,
                        input=step.input_uri,
                        output=step.output_uri)
        job_steps.append(stream_step)
    return job_steps

def make_custom_jobsteps(now, resource, steps):
    job_steps = []
    for i, step in enumerate(steps):
        step.step_name = _get_jobstep_name(_JOBSTEP_NAME, i, now)
        jar_step = JarStep(name=step.step_name,
                           jar=step.jar_uri,
                           action_on_failure=resource.action_on_failure,
                           step_args=step.step_args.split())
        job_steps.append(jar_step)
    return job_steps

def make_jobsteps(now, resource, context, target_steps):
    need_preprocessing = True if not context.jobflow_id else False
    if context.jobtype == u'hive':
        return make_hive_jobsteps(now, resource, target_steps,
                                  context.hive_site, need_preprocessing)
    elif context.jobtype == u'streaming':
        return make_streaming_jobsteps(now, resource, target_steps)
    elif context.jobtype == u'custom-jar':
        return make_custom_jobsteps(now, resource, target_steps)
    else:
        return None

def get_bootstraps(jobflow):
    bs = [get_data(Bootstrap, methodcaller("filter", Bootstrap.title == title))
            for title in jobflow.bootstrap_titles]
    return filter(lambda x: x is not None, bs)

def get_bootstrap_actions(jobflow):
    return [BootstrapAction(bs.action_type, bs.path_uri,
                bs.optional_args.split()) for bs in get_bootstraps(jobflow)]

_JOBFLOW_NAME = '{0} Job Flow from kotti_mapreduce {1}'
_JOBFLOW_PARAMS = [
    'log_uri',
    'keep_alive',
    'enable_debugging',
    'master_instance_type',
    'slave_instance_type',
    'num_instances',
    'ami_version',
    'hadoop_version',
]

def run_jobflow(emr_conn, resource, context):
    now = datetime.now().strftime('%Y-%m-%d %H%M%S')
    target_steps = list(ifilterfalse(attrgetter('step_run'), context.children))
    job_steps = make_jobsteps(now, resource, context, target_steps)
    jobflow_name = _JOBFLOW_NAME.format(context.jobtype.title(), now)

    if context.jobflow_id:
        emr_conn.add_jobflow_steps(context.jobflow_id, job_steps)
    else:
        bootstraps = get_bootstrap_actions(context)
        params = filter_object_attributes(resource, _JOBFLOW_PARAMS)
        context.jobflow_id = emr_conn.run_jobflow(jobflow_name,
                                                  steps=job_steps,
                                                  bootstrap_actions=bootstraps,
                                                  **params)

    _ = map(lambda step: setattr(step, 'step_run', True), target_steps)
    if resource.termination_protection:
        emr_conn.set_termination_protection(context.jobflow_id,
                                            resource.termination_protection)

def set_jobflow_state(context, res_jobflows):
    if context.type == u'jobservice':
        for i, res_jobflow in enumerate(res_jobflows):
            context.children[i].state = res_jobflow['state'].upper()
    elif context.type == u'jobflow' and res_jobflows:
        context.state = res_jobflows[0]['state'].upper()
