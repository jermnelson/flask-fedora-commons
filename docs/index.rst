.. Flask-FedoraCommons documentation master file, created by
   sphinx-quickstart on Tue Nov 12 15:43:44 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Flask-FedoraCommons
===================

.. module:: flask_fedora_commons

Flask-FedoraCommons is an extension to `Flask`_ that provides an interface 
to the open-source `Fedora Commons`_ digital repository. Certain modules from the 
`Eulfedora`_ project were forked and included as libraries in this extension.

Fedora 4
--------
`Fedora 4`_ support is now in active development in this extension. will be merged 
into the main branch when `Fedora 4`_ is out of beta release.  


Installation
------------

Install the extension with one of the following commands::

    $ easy_install Flask-FedoraCommons

or alternatively if you have pip installed::

    $ pip install Flask-FedoraCommons


Configuration
-------------
The fedora object itself can be used to configure the following 
required settings (and example values) for this extension:

====================== ======================================
`FEDORA_ROOT`          'http://fedora.host.name:8080/fedora/'
`FEDORA_USER`          'user'
`FEDORA_PASSWORD`      'password'
`FEDORA_PIDSPACE`      'changeme'
`FEDORA_TEST_ROOT`     'http://fedora.host.name:8180/fedora/'
`FEDORA_TEST_PIDSPACE` 'testme'
====================== ======================================


Using in a Flask Application
----------------------------
To get started with Flask-FedoraCommons, you need to instantiate a 
:class:`FedoraCommons` object after configuring the application::

    from flask import Flask
    from flask_fedora_commons import FedoraCommons

    app = Flask(__name__)
    app.config.from_pyfile('mysettings.cfg')
    fedora = FedoraCommons(app)


API Access to Fedora
--------------------

You can access both M-API and A-API REST web services available in the digital 
repository through the :class:`FedoraCommons` API interface.

.. toctree::
   :maxdepth: 2

   examples
   fedora4
   python3

Classes and Methods
-------------------

.. autoclass:: FedoraCommons
   :members:

.. autoclass:: Repository
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Eulfedora: https://github.com/emory-libraries/eulfedora/
.. _Fedora Commons: http://fedora-commons.org/
.. _Fedora 4: https://wiki.duraspace.org/display/FF/Fedora+Repository+Home
.. _Flask: http://flask.pocoo.org/
