# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "garbanzo"
VERSION = "1.0.15"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="Translator Knowledge Beacon API",
    author_email="richard@starinformatics.com",
    url="",
    keywords=["Swagger", "Translator Knowledge Beacon API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    long_description="""\
    This is the Translator Knowledge Beacon web service application programming interface (API). 
    """
)

