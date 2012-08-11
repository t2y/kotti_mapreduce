===============
kotti_mapreduce
===============

This is an extension to Kotti that allows to use MapReduce feature to your site.

`Find out more about Kotti`_


``kotti_mapreduce`` uses `Amazon Elastic MapReduce (Amazon EMR)`_ only
at this time. To run a MapReduce job, AWS access key is needed.
See also `Amazon Elastic MapReduce (Documentation)`_ about
the Job Flow for MapReduce.

Development happens at https://github.com/t2y/kotti_mapreduce

.. _Find out more about Kotti: http://pypi.python.org/pypi/Kotti
.. _Amazon Elastic MapReduce (Amazon EMR): http://aws.amazon.com/elasticmapreduce/
.. _Amazon Elastic MapReduce (Documentation): http://aws.amazon.com/documentation/elasticmapreduce/


Installation
============

From PyPI::

    $ pip install kotti_mapreduce

From github (for developers)::

    $ git clone git@github.com:t2y/kotti_mapreduce.git
    $ cd kotti_mapreduce/
    $ python setup.py develop


Configuration
=============

To enable the extension in your Kotti site, activate the configurator::

    kotti.configurators = kotti_mapreduce.kotti_configure


Documentation
=============

Documentation is hosted on readthedocs.org at http://kotti-mapreduce.readthedocs.org/en/latest/
