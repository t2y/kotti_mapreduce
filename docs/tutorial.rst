.. _tutorial:

Tutorial
========

In current version, `kotti_mapreduce` uses only Amazon Elastic MapReduce
(Amazon EMR). Let's make a streaming job flow.

Job Container
-------------

First of all, create a Job Container.

.. figure:: _static/k1.png
    :alt: Add Job Container
    :align: center

    Add Job Container

You can see an Edit page for Job Container. Then, input for a title
what you like and click `save` button. Sorry, `Cloud vendor` is
only accepted `aws`.

.. figure:: _static/k2.png
    :alt: Create Job Container
    :align: center

    Create Job Container

A Job Container content is created. You can see :ref:`resource` and
:ref:`bootstrap` and :ref:`jobservice` sections.

.. figure:: _static/k3.png
    :alt: Created Job Container
    :align: center

    Created Job Container


.. _resource:

Resource
--------

You have to register an AWS settings at least one.

.. figure:: _static/k4.png
    :alt: Add EMR Job Resource
    :align: center

    Add EMR Job Resource


.. _bootstrap:

Bootstrap
---------

As necessary, you can register Hadoop bootstrap processes.

.. figure:: _static/k5.png
    :alt: Add Bootstrap
    :align: center

    Add Bootstrap

Select `Action Type` and input other parameters. For example,
`Configure Daemons` is below.

.. figure:: _static/k6.png
    :alt: Create Bootstrap
    :align: center

    Create Bootstrap


.. _jobservice:

Job Service
-----------

Now, you're ready to create the EMR Job Flow. Before creating a job flow,
make a job service to be able to include several job flows.
The job service is used as a container for jobflows.

.. figure:: _static/k7.png
    :alt: Add Job Service
    :align: center

    Add Job Service

Select :ref:`resource` to be used on this job service.

.. note::

    Job Service requires a resource so you have to register
    the resource at least one.

.. figure:: _static/k8.png
    :alt: Create Job Service
    :align: center

    Create Job Service

After saving a job service, you can see below page.

.. figure:: _static/k9.png
    :alt: Created Job Service
    :align: center

    Created Job Service


.. _jobflow:

Job Flow
--------

Let's keep trying a little longer. We believe you already get used to
Kotti user interface. Take it easy!

.. figure:: _static/k10.png
    :alt: Add Job Flow
    :align: center

    Add Job Flow

`Job type` is important configuration to select Hadoop application.
There three applications as below.

* hive
* custom-jar
* streaming

If your application requires bootstrap processes, set them as the
job flow's configuration. For example, `Streaming Job` is below.

.. figure:: _static/k11.png
    :alt: Create Job Flow
    :align: center

    Create Job Flow

.. _jobstep:

Job Step
--------

This is last task. Add several steps to a job flow.

.. figure:: _static/k12.png
    :alt: Add Job Step
    :align: center

    Add Job Step

This step is a `Word Count Example`_.

.. _Word Count Example: http://aws.amazon.com/articles/2273

.. figure:: _static/k13.png
    :alt: Create Job Step
    :align: center

    Create Job Step

Back to upper job flow after you created a job step.

.. figure:: _static/k14.png
    :alt: Created Job Step
    :align: center

    Created Job Step

You can see a `Run Jobflow` button. It means all settings are completed.

.. figure:: _static/k15.png
    :alt: Run Job Flow
    :align: center

    Run Job Flow

Click `Run Jobflow` button, then you'll see the job flow's information.
To show latest information, click `Refresh` button.

.. figure:: _static/k16.png
    :alt: View Job Flow Status
    :align: center

    View Job Flow Status

Get Log
-------

Your job flow is finished, then you can get the logs. The log is located
on `Log URI` of ref:`resource`. To get download each log file,
click an icon next to its log file name.

.. figure:: _static/k17.png
    :alt: Get Log from S3
    :align: center

    Get Log from S3
