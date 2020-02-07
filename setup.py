#
# Copyright (c) 2015, Prometheus Research, LLC
#

from setuptools import setup, find_packages

setup(
    name='rios.conversion',
    version='0.6.2',
    description='Module for converting Instruments to and from RIOS',
    long_description=open('README.rst', 'r').read(),
    keywords='rios instrument assessment conversion',
    author='Prometheus Research, LLC',
    author_email='contact@prometheusresearch.com',
    license='Apache-2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    url='https://github.com/prometheusresearch/rios.conversion',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=True,
    include_package_data=True,
    namespace_packages=['rios'],
    entry_points={},
    install_requires=[
        'pyyaml',
        'rios.core>=0.6.0,<1',
        'simplejson==3.8.2',
    ],
    test_suite='nose.collector',
)
