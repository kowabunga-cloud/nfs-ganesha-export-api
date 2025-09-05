# coding: utf-8

"""
    NFS Ganesha Export API
"""  # noqa: E501

#!/usr/bin/env python3

from setuptools import setup, find_packages # noqa: H301

long_description = """
NFS Ganesha Export API Server provides a REST interface to perform CRUD operations and manage NFS Ganesha's server exports, generating the appropriate configuration file.
"""

def extract_private_package(s):
    start = s.find('#egg=') + 5
    return s[start:]

requirements_lines = [line.strip() for line in open('requirements.txt').readlines()]
install_requires = list(filter(lambda s: not s.startswith('-e '), requirements_lines))
dependency_links = list(map(lambda d: d.replace("-e ", ""), filter(lambda s: s.startswith('-e '), requirements_lines)))
additionnal_requires = map(lambda s: extract_private_package(s), dependency_links)

install_requires.extend(additionnal_requires)

scripts = ['bin/nfs-ganesha-export-api']
pkgdir = {'': 'nfsapi'}

setup(
    name='nfs-ganesha-export-api',
    version='0.3.0',
    description='nfs-ganesha-export-api: a REST web-server to manage Ganesha NFS export configuration files',
    keywords='nfs ganesha web rest api',
    long_description=long_description,
    author='The Kowabunga Project',
    author_email='maintainers@kowabunga.cloud',
    url='https://github.com/kowabunga-cloud/nfs-ganesha-export-api',
    scripts=scripts,
    package_dir=pkgdir,
    packages=find_packages(),
    platforms=['All'],
    license='Apache 2.0',
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=dependency_links,
)
