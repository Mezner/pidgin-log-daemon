#from distutils.core import setup
from setuptools import setup, find_packages

requirements = [
    'bleach>=1.0',
    #'thrift',
    'evernote-sdk-python>=1.23'
    ]

dependency_links = [
    'git+https://github.com/mezner/evernote-sdk-python'
    + '#egg=evernote-sdk-python-1.23',
    'git+https://github.com/mezner/bleach'
    + '#egg=bleach-1.0'
    ]

setup(
    name = "pidgin-log-daemon",
    version = "0.1",
    author = "Russell Myers",
    packages = find_packages(),
    install_requires = requirements,
    dependency_links = dependency_links,
    )
