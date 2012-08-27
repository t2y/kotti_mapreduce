# -*- coding: utf-8 -*-
from itertools import chain
from os.path import basename
from operator import attrgetter
from operator import methodcaller

import colander
import validictory
from deform.widget import HiddenWidget
from deform.widget import PasswordWidget
from deform.widget import TextAreaWidget
from deform.widget import TextInputWidget
from deform.widget import SelectWidget
from kotti.views.edit import ContentSchema
from kotti.views.edit import generic_edit
from kotti.views.edit import generic_add
from kotti.views.form import CommaSeparatedListWidget
from kotti.views.form import ObjectType
from kotti.views.util import ensure_view_selector
from kotti.views.util import template_api
from pyramid.response import Response
from sqlalchemy import asc
from sqlalchemy import desc

from kotti_mapreduce import _
from kotti_mapreduce.resources import Bootstrap
from kotti_mapreduce.resources import EMRJobResource
from kotti_mapreduce.resources import JobContainer
from kotti_mapreduce.resources import JobFlow
from kotti_mapreduce.resources import JobService
from kotti_mapreduce.resources import JobStep
from kotti_mapreduce.util.datastore import get_s3_connection
from kotti_mapreduce.util.datastore import get_s3_log_keys
from kotti_mapreduce.util.job import is_runnable_jobflow
from kotti_mapreduce.util.job import get_bootstraps
from kotti_mapreduce.util.job import get_emr_connection
from kotti_mapreduce.util.job import get_jobflow_ids
from kotti_mapreduce.util.job import get_jobflows_for_json
from kotti_mapreduce.util.job import run_jobflow
from kotti_mapreduce.util.job import set_jobflow_state
from kotti_mapreduce.util.helper import get_object_attributes
from kotti_mapreduce.util.helper import get_temporary_file
from kotti_mapreduce.util.model import get_all_data
from kotti_mapreduce.util.model import get_context_data
from kotti_mapreduce.util.model import get_context_or_parent
from kotti_mapreduce.util.model import get_resource
from kotti_mapreduce.util.model import get_resource_model


_SUPPORT_CLOUD_VENDOR = [u'aws']

def cloud_vendor_validator(node, value):
    if not value in _SUPPORT_CLOUD_VENDOR:
        raise colander.Invalid(node, _(u'Not supported vendor: ${vendor}',
                               mapping=dict(vendor=value)))

class JobContainerSchema(ContentSchema):
    cloud_vendor = colander.SchemaNode(
        colander.String(),
        title=_(u'Cloud vendor'),
        description=_(u'Cloud vendor name.'),
        validator=cloud_vendor_validator,
        default='aws')

@ensure_view_selector
def edit_job_container(context, request):
    return generic_edit(context, request, JobContainerSchema())

def add_job_container(context, request):
    return generic_add(context, request, JobContainerSchema(),
                       JobContainer, JobContainer.type_info.title)

def view_job_container(context, request):
    resource_model = get_resource_model(context)
    jobresources = get_all_data(resource_model, context,
                        methodcaller('order_by', asc(resource_model.title)))
    jobservices = get_all_data(JobService, context,
                        methodcaller('order_by', desc(JobService.id)))
    bootstraps = get_all_data(Bootstrap, context,
                        methodcaller('order_by', desc(Bootstrap.id)))
    return {
        'api': template_api(context, request),
        'jobresources': jobresources,
        'jobservices': jobservices,
        'bootstraps': bootstraps,
    }


_SUPPORT_ACTION_ON_FAILURE = [
    u'CANCEL_AND_WAIT',
    u'CONTINUE',
    u'TERMINATE_JOB_FLOW',
]

_SUPPORT_INSTANCE_TYPE = [
    (u'm1.small', u'Small (m1.small)'),
    (u'c1.medium', u'High-CPU Medium (c1.medium)'),
    (u'm1.large', u'Large (m1.large)'),
    (u'm1.xlarge', u'Extra Large (m1.xlarge)'),
    (u'c1.xlarge', u'High-CPU Extra Large (c1.xlarge)'),
    (u'm2.xlarge', u'High-Memory Extra Large (m2.xlarge)'),
    (u'm2.2xlarge', u'High-Memory Double Extra Large (m2.2xlarge)'),
    (u'm2.4xlarge', u'High-Memory Quad Extra Large (m2.4xlarge)'),
]


class EMRJobResourceSchema(ContentSchema):
    aws_access_key_id = colander.SchemaNode(
        colander.String(),
        title=_(u'AWS access key ID'),
        description=_(u'AWS access key ID to use AWS API.'),
    )
    aws_secret_access_key = colander.SchemaNode(
        colander.String(),
        title=_(u'AWS secret access key'),
        description=_(u'AWS secret access key to use AWS API.'),
        widget=PasswordWidget(),
    )
    region = colander.SchemaNode(
        colander.String(),
        title=_(u'AWS region'),
        description=_(u'AWS region code where a MapReduce job is executed.'),
        default='us-east-1')
    master_instance_type = colander.SchemaNode(
        colander.String(),
        title=_(u'Master instance type'),
        description=_(u'EC2 instance type of the master node.'),
        widget=SelectWidget(values=_SUPPORT_INSTANCE_TYPE),
        default='m1.small',
    )
    slave_instance_type = colander.SchemaNode(
        colander.String(),
        title=_(u'Slave instance type'),
        description=_(u'EC2 instance type of the slave nodes.'),
        widget=SelectWidget(values=_SUPPORT_INSTANCE_TYPE),
        default='m1.small',
    )
    ec2_keyname = colander.SchemaNode(
        colander.String(),
        title=_(u'EC2 key pair name'),
        description=_(u'EC2 key pair filename.'),
        missing=u'',
    )
    ec2_keyfile = colander.SchemaNode(
        colander.String(),
        title=_(u'EC2 key pair private key file'),
        description=_(u'EC2 key pair private key contents.'),
        widget=TextAreaWidget(cols=40, rows=5),
        missing=u'',
    )
    num_instances = colander.SchemaNode(
        colander.Integer(),
        title=_(u'Number of instances'),
        description=_(u'Number of instances in the Hadoop cluster.'),
        default=1,
    )
    action_on_failure = colander.SchemaNode(
        colander.String(),
        title=_(u'Action on failure'),
        description=_(u'Action to take if a step terminates.'),
        widget=SelectWidget(values=map(lambda x: (x, x),
                                       _SUPPORT_ACTION_ON_FAILURE)),
        default=u'TERMINATE_JOB_FLOW')
    keep_alive = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Keep alive'),
        description=_(u'Denotes whether the cluster '
                      'should stay alive upon completion.'),
        default=False,
    )
    enable_debugging = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Enable debugging'),
        description=_(u'Denotes whether AWS console debugging '
                      'should be enabled.'),
        default=False,
    )
    termination_protection = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Termination protection'),
        description=_(u'Set termination protection on jobflows.'),
        default=False)
    log_uri = colander.SchemaNode(
        colander.String(),
        title=_(u'log URI'),
        description=_(u'URI of the S3 bucket to place logs.'),
    )
    ami_version = colander.SchemaNode(
        colander.String(),
        title=_(u'AMI version'),
        description=_(u'Amazon Machine Image (AMI) version '
                      'to use for instances.'),
        default='latest',
    )
    hadoop_version = colander.SchemaNode(
        colander.String(),
        title=_(u'Hadoop version'),
        description=_(u'Version of Hadoop to use. This no longer.'),
        missing=u'',
    )
    hive_versions = colander.SchemaNode(
        colander.String(),
        title=_(u'Hive version'),
        description=_(u'Version of Hive to use.'),
        missing=u'',
    )

@ensure_view_selector
def edit_emrjob_resource(context, request):
    return generic_edit(context, request, EMRJobResourceSchema())

def add_emrjob_resource(context, request):
    return generic_add(context, request, EMRJobResourceSchema(),
                       EMRJobResource, EMRJobResource.type_info.title)

def view_emrjob_resource(context, request):
    return {
        'api': template_api(context, request),
        'resource_models': [EMRJobResource, JobService, Bootstrap],
    }


@colander.deferred
def deferred_resource_data(node, kw):
    values = None
    context = kw['request'].context
    resource = get_resource_model(context)
    if resource:
        order_by = methodcaller('order_by', asc(resource.title))
        job_container = get_context_or_parent(context, u'jobcontainer')
        data = get_all_data(resource, job_container, order_by=order_by)
        values = map(attrgetter('id', 'title'), data)
    return SelectWidget(values=values)

class JobServiceSchema(ContentSchema):
    resource_id = colander.SchemaNode(
        colander.Integer(),
        title=_(u'Resource'),
        description=_(u'Resource name.'),
        widget=deferred_resource_data,
    )

@ensure_view_selector
def edit_jobservice(context, request):
    return generic_edit(context, request, JobServiceSchema())

def add_jobservice(context, request):
    return generic_add(context, request, JobServiceSchema(),
                       JobService, JobService.type_info.title)

def view_jobservice(context, request):
    return {
        'api': template_api(context, request),
        'bootstraps': False,
        'is_runnable': False,
        'resource': get_resource(context),
        'resource_models': [EMRJobResource, JobService, Bootstrap],
    }


@colander.deferred
def deferred_bootstrap_validator(node, kw):
    def raise_invalid_bootstrap(node, value):
        raise colander.Invalid(
            node, _(u"The Bootstrap is not found."))

    request = kw['request']
    if request.POST:
        parent = request.context.parent
        context = get_context_or_parent(parent, u'jobcontainer')
        bootstraps = get_all_data(Bootstrap, context)
        availables = [bootstrap.title for bootstrap in bootstraps]
        posted_bootstraps = request.params.get('bootstrap_titles')
        if posted_bootstraps:
            for posted_bootstrap in posted_bootstraps.split(','):
                if posted_bootstrap not in availables:
                    return raise_invalid_bootstrap

@colander.deferred
def deferred_bootstrap_widget(node, kw):
    parent = kw['request'].context.parent
    context = get_context_or_parent(parent, u'jobcontainer')
    bootstraps = get_all_data(Bootstrap, context)
    availables = [bootstrap.title.encode('utf-8') for bootstrap in bootstraps]
    widget = CommaSeparatedListWidget(
        template='kotti_mapreduce:templates/deform/bootstrap-list',
        available_bootstraps=availables,
    )
    return widget

_SUPPORT_JOBTYPE = [
    u'hive',
    u'custom-jar',
    u'streaming',
]

class JobFlowSchema(ContentSchema):
    jobflow_id = colander.SchemaNode(
        colander.String(),
        title=_(u'Job flow ID'),
        description=_(u'specify only if you have existing job flow.'),
        missing=u'',
    )
    jobtype = colander.SchemaNode(
        colander.String(),
        title=_(u'Job type'),
        description=_(u'Application type for job flow.'),
        widget=SelectWidget(values=map(lambda x: (x, x), _SUPPORT_JOBTYPE)))
    state = colander.SchemaNode(
        colander.String(),
        title=_(u'Job flow state'),
        description=_(u'Job flow state.'),
        widget=HiddenWidget(),
        missing=u'',
    )
    hive_site = colander.SchemaNode(
        colander.String(),
        title=_(u'Hive site'),
        description=_(u'Use metastore located outside of the cluster.'),
        missing=u'',
    )
    bootstrap_titles = colander.SchemaNode(
        ObjectType(),
        title=_('Bootstraps'),
        description=_(u'Input a bootstrap name registered in advance.'),
        validator=deferred_bootstrap_validator,
        widget=deferred_bootstrap_widget,
        missing=[],
    )

@ensure_view_selector
def edit_jobflow(context, request):
    return generic_edit(context, request, JobFlowSchema())

def add_jobflow(context, request):
    return generic_add(context, request, JobFlowSchema(),
                       JobFlow, JobFlow.type_info.title)

def view_jobflow_with_ajax(context, request):
    req_type = request.params.get('type')
    resource = get_resource(context)
    emr_conn = get_emr_connection(resource)

    if req_type == 'runjobflow' and is_runnable_jobflow(context):
        run_jobflow(emr_conn, resource, context)

    jobflow_ids = get_jobflow_ids(context)

    if req_type == 'terminate' and jobflow_ids:
        emr_conn.terminate_jobflows(jobflow_ids)
        # FIXME: enforce a termination against protection

    if req_type == 'getlog':
        s3_conn = get_s3_connection(resource)
        keys_list = get_s3_log_keys(s3_conn, resource.log_uri, jobflow_ids)
        bucket_name = keys_list[0].bucket.name if keys_list else u''
        keys = [dict(get_object_attributes(key, ['name', 'size']))
                        for key in chain.from_iterable(keys_list)]
        return {'keys': keys, 'bucket_name': bucket_name}
    else:  # refresh
        res_jobflows = get_jobflows_for_json(emr_conn, jobflow_ids)
        set_jobflow_state(context, res_jobflows)
        return res_jobflows

def view_jobflow(context, request):
    return {
        'api': template_api(context, request),
        'bootstraps': get_bootstraps(context),
        'is_runnable': is_runnable_jobflow(context),
        'resource': get_resource(context),
        'resource_models': [JobFlow],
    }


_SUPPORT_ACTION_TYPE = [
    ('', u''),
    ('hadoop', u'Configure Hadoop'),
    ('daemon', u'Configure Daemons'),
    ('ganglia', u'Install Ganglia'),
    ('memory', u'Memory Intensive Configuration'),
    ('runif', u'Run If'),
    ('custom', u'Custom Action'),
]

class BootstrapSchema(ContentSchema):
    action_type = colander.SchemaNode(
        colander.String(),
        title=_(u'Action Type'),
        description=_(u'The action type.'),
        widget=SelectWidget(values=_SUPPORT_ACTION_TYPE),
        default=u'',
    )
    path_uri = colander.SchemaNode(
        colander.String(),
        title=_(u'Path URI'),
        description=_(u'The Path URI.'),
        missing=u'',
    )
    optional_args = colander.SchemaNode(
        colander.String(),
        title=_(u'Optional arguments'),
        description=_(u'Arguments to pass to the bootstrap.'),
        widget=TextAreaWidget(cols=40, rows=5),
        missing=u'',
    )

@ensure_view_selector
def edit_bootstrap(context, request):
    return generic_edit(context, request, BootstrapSchema())

def add_bootstrap(context, request):
    return generic_add(context, request, BootstrapSchema(),
                       Bootstrap, Bootstrap.type_info.title)

def view_bootstrap(context, request):
    return {
        'api': template_api(context, request),
        'resource_models': [EMRJobResource, JobService, Bootstrap],
    }


_TEXT_AREA_WIDGET_PARAMS = [
    u'step_args',
]

_HIVE_PARAMS = [
    u'step_args',
]

_STREAMING_PARAMS = [
    u'mapper',
    u'reducer',
    u'input_uri',
    u'output_uri',
]

_CUSTOM_JAR_PARAMS = [
    u'jar_uri',
    u'step_args',
]

_JOBTYPE_PARAMS = {
    "hive": _HIVE_PARAMS,
    "streaming": _STREAMING_PARAMS,
    "custom-jar": _CUSTOM_JAR_PARAMS,
}

@colander.deferred
def deferred_jobstep_widget(node, kw):
    jobtype = get_context_data(kw['request'].context, 'jobflow', ['jobtype'])
    if (jobtype == u'hive' and node.name in _HIVE_PARAMS) or \
       (jobtype == u'streaming' and node.name in _STREAMING_PARAMS) or \
       (jobtype == u'custom-jar' and node.name in _CUSTOM_JAR_PARAMS):
        if node.name in _TEXT_AREA_WIDGET_PARAMS:
            return TextAreaWidget(cols=40, rows=5)
        else:
            return TextInputWidget()
    else:
        return HiddenWidget()

@colander.deferred
def deferred_default_step_args(node, kw):
    jobtype = get_context_data(kw['request'].context, 'jobflow', ['jobtype'])
    if jobtype == u'hive':
        resource = get_resource(kw['request'].context)
        args = _DEFAULT_HIVE_STEP_ARGS
        if resource.hive_versions:
            args += u'--hive-versions\n{0}\n'.format(resource.hive_versions)
        return args
    elif jobtype == u'custom-jar':
        return _DEFAULT_CUSTOM_JAR_STEP_ARGS
    else:
        return u''

_STEP_ARGS_VALIDICTORY_SCHEMA = {"type": "array"}

_DEFAULT_HIVE_STEP_ARGS = """
s3://us-east-1.elasticmapreduce/libs/hive/hive-script
--base-path
s3://us-east-1.elasticmapreduce/libs/hive/
--run-hive-script
"""

_DEFAULT_CUSTOM_JAR_STEP_ARGS = """
"""

@colander.deferred
def deferred_jobflow_id(node, kw):
    jobflow_id = kw['request'].context.jobflow_id
    return jobflow_id

def step_args_validator(node, value):
    if value:
        try:
            validictory.validate(value.split(), _STEP_ARGS_VALIDICTORY_SCHEMA)
        except Exception as err:
            raise colander.Invalid(node, _(u'Got Error: ${err}',
                                   mapping=dict(err=err)))

class JobStepSchema(ContentSchema):
    jobflow_id = colander.SchemaNode(
        colander.String(),
        title=_(u'Job flow ID'),
        description=_(u'a step belongs to the job flow ID.'),
        default=deferred_jobflow_id,
        widget=HiddenWidget(),
        missing=u'',
    )
    jar_uri = colander.SchemaNode(
        colander.String(),
        title=_(u'Custom Jar URI'),
        description=_(u'The custom Jar URI.'),
        widget=deferred_jobstep_widget,
        missing=u'',
    )
    mapper = colander.SchemaNode(
        colander.String(),
        title=_(u'Mapper'),
        description=_(u'The mapper URI.'),
        widget=deferred_jobstep_widget,
        missing=u'',
    )
    reducer = colander.SchemaNode(
        colander.String(),
        title=_(u'Reducer'),
        description=_(u'The reducer URI.'),
        widget=deferred_jobstep_widget,
        missing=u'',
    )
    input_uri = colander.SchemaNode(
        colander.String(),
        title=_(u'Input file URI'),
        description=_(u'The Input file URI.'),
        widget=deferred_jobstep_widget,
        missing=u'',
    )
    output_uri = colander.SchemaNode(
        colander.String(),
        title=_(u'Output file URI'),
        description=_(u'The Output file URI.'),
        widget=deferred_jobstep_widget,
        missing=u'',
    )
    step_args = colander.SchemaNode(
        colander.String(),
        title=_(u'Step arguments'),
        description=_(u'Arguments to pass to the step.'),
        widget=deferred_jobstep_widget,
        validator=step_args_validator,
        default=deferred_default_step_args,
        missing=u'',
    )

@ensure_view_selector
def edit_jobstep(context, request):
    return generic_edit(context, request, JobStepSchema())

def add_jobstep(context, request):
    return generic_add(context, request, JobStepSchema(),
                       JobStep, JobStep.type_info.title)

def view_jobstep(context, request):
    jobtype = get_context_data(context, 'jobflow', ['jobtype'])
    attr_names = _JOBTYPE_PARAMS.get(jobtype)
    return {
        'api': template_api(context, request),
        'attr_names': attr_names,
        'resource_models': [JobStep],
    }

def view_download_file(context, request):
    resource = get_resource(context)
    s3_conn = get_s3_connection(resource)
    bucket = s3_conn.get_bucket(request.params.get('bucket'))
    key_path = request.params.get('key')
    key = bucket.lookup(key_path)

    response = Response()
    fp = get_temporary_file(key.size)
    if fp:
        key.get_contents_to_file(fp)
        fp.seek(0)
        con_dis = 'attachment; filename={0}'.format(basename(key_path))
        response.content_disposition = con_dis
        response.app_iter = fp
    else:
        response.text = u'Download it yourself, '
        response.text += u'because of large file size: {0}'.format(key.size)
    return response

def has_download_params(context, request):
    if request.params.get('type') == 'download' and \
       request.params.get('key') and request.params.get('bucket'):
        return True
    else:
        return False

def includeme_edit(config):
    config.add_view(
        edit_job_container,
        context=JobContainer,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        add_job_container,
        name=JobContainer.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        edit_emrjob_resource,
        context=EMRJobResource,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        add_emrjob_resource,
        name=EMRJobResource.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        edit_jobservice,
        context=JobService,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        add_jobservice,
        name=JobService.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        edit_jobflow,
        context=JobFlow,
        name='edit',
        permission='edit',
        renderer='templates/jobflow-edit.pt',
    )

    config.add_view(
        add_jobflow,
        name=JobFlow.type_info.add_view,
        permission='add',
        renderer='templates/jobflow-edit.pt',
    )

    config.add_view(
        edit_bootstrap,
        context=Bootstrap,
        name='edit',
        permission='edit',
        renderer='templates/bootstrap-edit.pt',
    )

    config.add_view(
        add_bootstrap,
        name=Bootstrap.type_info.add_view,
        permission='add',
        renderer='templates/bootstrap-edit.pt',
    )

    config.add_view(
        edit_jobstep,
        context=JobStep,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
    )

    config.add_view(
        add_jobstep,
        name=JobStep.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
    )


def includeme_view(config):
    config.add_view(
        view_job_container,
        context=JobContainer,
        name='view',
        permission='view',
        renderer='templates/jobcontainer-view.pt',
    )

    config.add_view(
        view_emrjob_resource,
        context=EMRJobResource,
        name='view',
        permission='view',
        renderer='templates/emrjobresource-view.pt',
    )

    config.add_view(
        view_jobservice,
        context=JobService,
        name='view',
        permission='view',
        renderer='templates/jobflow-view.pt',
    )

    config.add_view(
        view_download_file,
        context=JobService,
        name='view',
        permission='view',
        custom_predicates=(has_download_params,),
    )

    config.add_view(
        view_jobflow_with_ajax,
        context=JobService,
        name='view',
        permission='view',
        xhr=True,
        request_method='POST',
        renderer='json',
    )

    config.add_view(
        view_jobflow,
        context=JobFlow,
        name='view',
        permission='view',
        renderer='templates/jobflow-view.pt',
    )

    config.add_view(
        view_download_file,
        context=JobFlow,
        name='view',
        permission='view',
        custom_predicates=(has_download_params,),
    )

    config.add_view(
        view_jobflow_with_ajax,
        context=JobFlow,
        name='view',
        permission='view',
        xhr=True,
        request_method='POST',
        renderer='json',
    )

    config.add_view(
        view_bootstrap,
        context=Bootstrap,
        name='view',
        permission='view',
        renderer='templates/bootstrap-view.pt',
    )

    config.add_view(
        view_jobstep,
        context=JobStep,
        name='view',
        permission='view',
        renderer='templates/jobstep-view.pt',
    )

    config.add_static_view('static-kotti_mapreduce', 'kotti_mapreduce:static')

def includeme(config):
    includeme_edit(config)
    includeme_view(config)
    config.add_translation_dirs('kotti_mapreduce:locale/')
