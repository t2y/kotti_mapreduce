# -*- coding: utf-8 -*-
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    AUTHORS = open(os.path.join(here, 'AUTHORS.txt')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = AUTHORS = CHANGES = ''

install_requires = [
    'Kotti >= 0.7',
    'Babel',
    'boto',
    'python-dateutil',
    'validictory',
]

tests_require = [
    'WebTest',
    'detox',
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-pep8',
    'pytest-xdist',
    'tox',
    'wsgi_intercept',
    'zope.testbrowser',
]

setup(name='kotti_mapreduce',
      version='0.2.0',
      description='The MapReduce addon for Kotti sites',
      long_description='\n\n'.join([README, AUTHORS, CHANGES]),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python',
          'Framework :: Pylons',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          'License :: Repoze Public License',
      ],
      author='Tetsuya Morimoto',
      author_email='tetsuya dot morimoto at gmail dot com',
      url='https://github.com/t2y/kotti_mapreduce',
      keywords='kotti web emr mapreduce',
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      packages=['kotti_mapreduce'],
      package_data={'kotti_mapreduce': [
          'static/*',
          'templates/*.pt',
          'locale/*.*',
          'locale/*/LC_MESSAGES/*.*']},
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      dependency_links=[
      ],
      #[fanstatic.libraries]
      #kotti_mapreduce = kotti_mapreduce.static:lib_kotti
      entry_points="""
      """,
      extras_require={
          'testing': tests_require,
      },
      message_extractors={'kotti_mapreduce': [
          ('**.py', 'lingua_python', None),
          ('**.pt', 'lingua_xml', None),
      ]},
      )
