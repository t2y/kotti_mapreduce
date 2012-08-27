.. _developer-manual:

Developer manual
================

tests
-----

kotti_mapreduce needs `pytest`_ for testing. See also `[pytest]` section in
`setup.cfg` about default pytest configuration::

    $ cd kotti_mapreduce
    $ py.test

Or, run `tox`_ test if you have multiple python interpreters.
See also `tox.ini` about tox environment::

    $ tox # or detox

.. _pytest: http://pytest.org/latest/
.. _tox: http://tox.testrun.org/latest/
