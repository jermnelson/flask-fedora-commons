"""
Flask-FedoraCommons
-------------------

This Flask extension read/write access to the digital repository `Fedora
Commons <http://fedora-commons.org/>`_ for use by Flask applications

"""
__author__ = "Jeremy Nelson"

from setuptools import setup

setup(
    name='Flask-FedoraCommons',
    version='0.0.2',
    url='http://github.com/jermnelson/flask-fedora-commons',
    license='MIT License',
    author=__author__,
    author_email='jermnelson@gmail.com',
    description='Library for manipulating Fedora Commons digitial repositories',
    long_description=__doc__,
    py_modules=['flask_fedora_commons'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Framework :: Flask',
        'Topic :: Software Development :: Libraries :: Python Modules'

    ]
)
