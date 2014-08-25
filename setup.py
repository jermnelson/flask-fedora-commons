"""
Flask-FedoraCommons
-------------------

This Flask extension provides CRUD operations for
`Fedora Commons <http://fedora-commons.org/>`_ digital repositories. Latest
version focuses on `Fedora 4 <https://wiki.duraspace.org/display/FF/Fedora+Repository+Home>`_
using Python 3.

Legacy support for Fedora 3.x and Python 2.7x are available by cloning the project's
git repository at <https://github.com/jermnelson/flask-fedora-commons.git> and
then checking out the legacy branch.
"""
__author__ = "Jeremy Nelson"
__version_info__ = ('0', '0', '8')
__version__ = '.'.join(__version_info__)

from setuptools import find_packages, setup

setup(
    name='Flask-FedoraCommons',
    version=__version__,
    url='http://github.com/jermnelson/flask-fedora-commons',
    license='MIT License',
    author=__author__,
    author_email='jermnelson@gmail.com',
    description='Library for manipulating Fedora Commons digitial repositories',
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'python-dateutil',
        'Flask',
        'rdflib'
    ],
    classifiers=[
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'

    ]
)
