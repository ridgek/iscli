#!/usr/bin/env python

from setuptools import setup

import iscli.linenoise


install_requires = [
    'cffi >= 0.8',
]
test_requires = [
    'nose',
]


setup(
    name='iscli',
    packages=['iscli'],
    description='',
    author='Ridge Kennedy',
    author_email='ridgefs@gmail.com',
    include_package_data=True,
    zip_safe=False,
    ext_modules=[iscli.linenoise.ffi.verifier.get_extension()],
    install_requires=install_requires,
    test_requires=test_requires,
    test_suite='nose.collector',
)
