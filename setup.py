"""
Flask-FedoraCommons
-------------------

This Flask extension provides CRUD operations for
`Fedora Commons <http://fedora-commons.org/>`_ digital repositories.

"""
__author__ = "Jeremy Nelson"

from setuptools import find_packages, setup



setup(
    name='Flask-FedoraCommons',
    version='0.0.5',
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
        'poster',
        'rdflib'
    ],
    classifiers=[
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',        
        'Topic :: Software Development :: Libraries :: Python Modules'

    ]
)
