__author__ = "Jeremy Nelson"

import os
import sys
import unittest
sys.path.append(os.path.split(os.getcwd())[0])

from flask import Flask, current_app

from flask_fedora_commons import FedoraCommons
from flask_fedora_commons.lib.server import Repository


class RepositoryMock(object):

    def __init__(self):
        pass

class FedoraCommonsTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True
        self.app.config['FEDORA_ROOT'] = 'http://localhost:8080/fedora/'
        self.app.config['FEDORA_USER'] = 'fedoraAdmin'
        self.app.config['FEDORA_PASSWORD'] = 'fedoraAdmin'

    def test_fedora_vars(self):
        """ Tests existence and some values for Fedora variables in app
        config"""
        for fedora_var in ['FEDORA_ROOT', 'FEDORA_USER', 'FEDORA_PASSWORD']:
            self.assertIn(fedora_var, self.app.config)
        self.assertEquals(self.app.config['FEDORA_ROOT'],
                          'http://localhost:8080/fedora/')

    def test_init(self):
        fedora = FedoraCommons(self.app)
        self.assert_(fedora.app)

    def test_connect(self):
        fedora = FedoraCommons(self.app)
        self.assertEquals(type(fedora.connect()),
                          Repository)

    def test_move(self):
        fedora = FedoraCommons(self.app)
        self.assert_(not fedora.move('fedora:5', 'fedora:2'))


    def test_repository(self):
        fedora = FedoraCommons(self.app)
        self.assert_(not fedora.repository)


    def tearDown(self):
        pass



if __name__ == '__main__':
    unittest.main()
