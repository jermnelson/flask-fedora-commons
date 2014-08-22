#-------------------------------------------------------------------------------
# Name:        tests
# Purpose:     Modules provides unit testing of the Flask-FedoraCommons Fedora 4
#              <https://wiki.duraspace.org/display/FF/Fedora+Repository+Home>
#              support.
#
# Author:      Jeremy Nelson
#
# Created:     2014/06/06
# Copyright:   (c) Jeremy Nelson, Colorado College 2014
# Licence:     MIT
#-------------------------------------------------------------------------------
__author__ = "Jeremy Nelson"

import json
import os
import rdflib
import sys
import unittest
import urllib.parse
import urllib.request
import uuid

sys.path.append(os.path.split(os.getcwd())[0])

from flask import Flask, current_app
from flask_fedora_commons import Repository

BIBFRAME = rdflib.Namespace("http://bibframe.org/vocab/")
FEDORA_BASE_URL = "http://localhost:8080"
SCHEMA_ORG = rdflib.Namespace("http://schema.org/")


class TestFedoraCommons(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True
        self.repo = Repository()
        self.work_uri = rdflib.URIRef(
            urllib.parse.urljoin(FEDORA_BASE_URL,
                                 "/rest/test/work/{}".format(uuid.uuid4())))
        self.work_rdf = rdflib.Graph()
        self.work_rdf.add((self.work_uri,
                           rdflib.RDFS.label,
                           rdflib.Literal("Work for Unit Test")))
        self.work_rdf.add((self.work_uri,
                           rdflib.RDF.type,
                           BIBFRAME.Monograph))
        self.work_rdf.add((self.work_uri,
                           rdflib.RDF.type,
                           SCHEMA_ORG.Book))
        # Add RDF Graph to Fedora
        new_request = urllib.request.Request(
            str(self.work_uri),
            data=self.work_rdf.serialize(format='turtle'),
            method='PUT',
            headers={"Content-Type": "text/turtle"})
        urllib.request.urlopen(new_request)


    def test_repo_exists(self):
        self.assertTrue(self.repo is not None)

    def test_as_json(self):
        # JSON-LD without Context
        work_json = json.loads(self.repo.as_json(str(self.work_uri)))
        self.assertEqual(work_json[0]['@id'], str(self.work_uri))

    def test_as_json_context(self):
        # JSON-LD with Context
        work_json = json.loads(self.repo.as_json(str(self.work_uri),
                                                 context={
            "@vocab": "http://bibframe.org/vocab/",
            "fcrepo": "http://fedora.info/definitions/v4/repository#",
            "fedora": "http://fedora.info/definitions/v4/rest-api#",
            "@language": "en"}))
        self.assertEqual(work_json['@id'], str(self.work_uri))


    def test_read(self):
        work_rdf = self.repo.read(str(self.work_uri))
        label = work_rdf.value(subject=self.work_uri,
                               predicate=rdflib.RDFS.label)
        self.assertEqual(label.value,
                         "Work for Unit Test")


    def tearDown(self):
        self.repo.delete(urllib.parse.urljoin(FEDORA_BASE_URL, "/rest/test/"))


if __name__ == '__main__':
    unittest.main()
