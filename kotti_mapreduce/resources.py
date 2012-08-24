# -*- coding: utf-8 -*-
from kotti.resources import Content
from kotti.sqla import JsonType
from kotti.sqla import MutationList
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from kotti_mapreduce import _


class JobContainer(Content):
    __tablename__ = 'jobcontainers'
    __mapper_args__ = dict(polymorphic_identity='jobcontainer')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    cloud_vendor = Column(String(32))

    type_info = Content.type_info.copy(
        name=u'JobContainer',
        title=_(u"Job Container"),
        add_view=u'add_jobcontainer',
        addable_to=[u'Document'],
    )

    def __init__(self, cloud_vendor=u'aws', **kwargs):
        super(JobContainer, self).__init__(**kwargs)
        self.cloud_vendor = cloud_vendor


class EMRJobResource(Content):
    __tablename__ = 'emrjobresources'
    __mapper_args__ = dict(polymorphic_identity='emrjobresource')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    aws_access_key_id = Column(String(256))
    aws_secret_access_key = Column(String(256))
    region = Column(String(64))
    master_instance_type = Column(String(32))
    slave_instance_type = Column(String(32))
    ec2_keyname = Column(String(256))
    ec2_keyfile = Column(Text())
    num_instances = Column(Integer())
    action_on_failure = Column(String(64))
    keep_alive = Column(Boolean())
    enable_debugging = Column(Boolean())
    termination_protection = Column(Boolean())
    log_uri = Column(String(1024))
    ami_version = Column(String(32))
    hadoop_version = Column(String(32))
    hive_versions = Column(String(32))

    type_info = Content.type_info.copy(
        name=u'EMRJobResource',
        title=_(u"EMR Job Resource"),
        add_view=u'add_emrjobresource',
        addable_to=[u'JobContainer'],
    )

    def __init__(self, aws_access_key_id=u'', aws_secret_access_key=u'',
                 region=u'', master_instance_type=u'm1.small',
                 slave_instance_type=u'm1.small', ec2_keyname=u'',
                 ec2_keyfile=u'', num_instances=1,
                 action_on_failure=u'TERMINATE_JOB_FLOW', keep_alive=False,
                 enable_debugging=False, termination_protection=False,
                 log_uri=None, ami_version=None, hadoop_version=None,
                 hive_versions=None, **kwargs):
        super(EMRJobResource, self).__init__(**kwargs)
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region
        self.master_instance_type = master_instance_type
        self.slave_instance_type = slave_instance_type
        self.ec2_keyname = ec2_keyname
        self.ec2_keyfile = ec2_keyfile
        self.num_instances = num_instances
        self.action_on_failure = action_on_failure
        self.keep_alive = keep_alive
        self.enable_debugging = enable_debugging
        self.termination_protection = termination_protection
        self.log_uri = log_uri
        self.ami_version = ami_version
        self.hadoop_version = hadoop_version
        self.hive_versions = hive_versions


class JobService(Content):
    __tablename__ = 'jobservices'
    __mapper_args__ = dict(polymorphic_identity='jobservice')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    resource_id = Column(Integer(), ForeignKey('emrjobresources.id'),
                         index=True)

    type_info = Content.type_info.copy(
        name=u'JobService',
        title=_(u'Job Service'),
        add_view=u'add_jobservice',
        addable_to=[u'JobContainer'],
    )

    def __init__(self, resource_id, **kwargs):
        super(JobService, self).__init__(**kwargs)
        self.resource_id = resource_id


class JobFlow(Content):
    __tablename__ = 'jobflows'
    __mapper_args__ = dict(polymorphic_identity='jobflow')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    jobflow_id = Column(String(64))
    jobtype = Column(String(32))
    state = Column(String(64))
    hive_site = Column(String(1024))
    bootstrap_titles = Column(MutationList.as_mutable(JsonType))

    type_info = Content.type_info.copy(
        name=u'JobFlow',
        title=_(u'Job Flow'),
        add_view=u'add_jobflow',
        addable_to=[u'JobService'],
    )

    def __init__(self, jobflow_id=u'', jobtype=u'', state=u'', hive_site=u'',
                 bootstrap_titles=[], **kwargs):
        super(JobFlow, self).__init__(**kwargs)
        self.jobflow_id = jobflow_id
        self.jobtype = jobtype
        self.state = state
        self.hive_site = hive_site
        self.bootstrap_titles = bootstrap_titles


class JobStep(Content):
    __tablename__ = 'jobsteps'
    __mapper_args__ = dict(polymorphic_identity='jobstep')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    jobflow_id = Column(Integer(), ForeignKey('jobflows.id'), index=True)
    jar_uri = Column(String(1024))
    mapper = Column(String(1024))
    reducer = Column(String(1024))
    input_uri = Column(String(1024))
    output_uri = Column(String(1024))
    step_args = Column(Text())
    step_name = Column(String(64))
    step_run = Column(Boolean())

    type_info = Content.type_info.copy(
        name=u'JobStep',
        title=_(u'Job Step'),
        add_view=u'add_jobstep',
        addable_to=[u'JobFlow'],
    )

    def __init__(self, jobflow_id=u'', jar_uri=u'', mapper=u'',
                 reducer=u'', input_uri=u'', output_uri=u'', step_args=u'',
                 step_name=u'', step_run=False, **kwargs):
        super(JobStep, self).__init__(**kwargs)
        self.jobflow_id = jobflow_id
        self.jar_uri = jar_uri
        self.mapper = mapper
        self.reducer = reducer
        self.input_uri = input_uri
        self.output_uri = output_uri
        self.step_args = step_args


class Bootstrap(Content):
    __tablename__ = 'bootstraps'
    __mapper_args__ = dict(polymorphic_identity='bootstrap')
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    action_type = Column(String(32))
    path_uri = Column(String(1024))
    optional_args = Column(Text())

    type_info = Content.type_info.copy(
        name=u'Bootstrap',
        title=_(u'Bootstrap'),
        add_view=u'add_bootstrap',
        addable_to=[u'JobContainer'],
    )

    def __init__(self, jobflow_id=u'', action_type=u'', path_uri=u'',
                 optional_args=u'', **kwargs):
        super(Bootstrap, self).__init__(**kwargs)
        self.jobflow_id = jobflow_id
        self.action_type = action_type
        self.path_uri = path_uri
        self.optional_args = optional_args
