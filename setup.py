#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import cms_saq

version = cms_saq.__version__

setup(
    name='django-cms-saq',
    version=version,
    description='Self-assessment questionnaires with Django CMS.',
    author='Olly Smith',
    author_email='oliver.smith@maplecroft.com',
    url='http://git.maplecroft.com/',
    packages=['cms_saq', 'cms_saq.migrations', 'cms_saq.management', 'cms_saq.management.commands'],
    license='Maplecroft',
    include_package_data = True,
)
