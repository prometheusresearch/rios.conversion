#
# Copyright (c) 2015, Prometheus Research, LLC
#

from setuptools import setup, find_packages

setup(
    name='rios.conversion',
    version='0.5.0',
    description='Module for converting Instruments to and from RIOS',
    long_description=open('README.rst', 'r').read(),
    keywords='rios instrument assessment conversion',
    author='Prometheus Research, LLC',
    author_email='contact@prometheusresearch.com',
    license='Apache Software License 2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    url='https://bitbucket.org/prometheus/rios.conversion',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=True,
    include_package_data=True,
    namespace_packages=['rios'],
    entry_points={
        'console_scripts': [
            'redcap-rios = rios.conversion.redcap.to_rios:main',
            'rios-redcap = rios.conversion.redcap.from_rios:main',
            'qualtrics-rios = rios.conversion.qualtrics.to_rios:main',
            'rios-qualtrics = rios.conversion.qualtrics.from_rios:main',
        ]
    },
    install_requires=[
        'pyyaml',
        'rios.core>=0.6.0,<1',
    ],
    extras_require={
        'dev': [
            'coverage>=3.7,<4',
            'nose>=1.3,<2',
            'nosy>=1.1,<2',
            'prospector[with_pyroma]>=0.10,<0.11',
            'twine>=1.5,<2',
            'wheel>=0.24,<0.25',
            'Sphinx>=1.3,<2',
            'sphinx-autobuild>=0.5,<0.6',
            'tox>=2,<3',
            'flake8>=2.5.0,<3',
        ],
    },
    test_suite='nose.collector',
)
