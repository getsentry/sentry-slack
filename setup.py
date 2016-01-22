#!/usr/bin/env python
"""
sentry-slack
============

An extension for `Sentry <https://getsentry.com>`_ which posts notifications
to `Slack <https://slack.com>`_.

:copyright: (c) 2015 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


install_requires = [
    'sentry>=7.0.0',
]

tests_require = [
    'exam',
    'flake8>=2.0,<2.1',
    'responses',
]

setup(
    name='sentry-slack',
    version='0.5.0',
    author='Matt Robenolt',
    author_email='matt@ydekproductons.com',
    url='https://github.com/getsentry/sentry-slack',
    description='A Sentry extension which posts notifications to Slack (https://slack.com/).',
    long_description=open('README.rst').read(),
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
    },
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'slack = sentry_slack',
        ],
        'sentry.plugins': [
            'slack = sentry_slack.plugin:SlackPlugin',
        ]
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
