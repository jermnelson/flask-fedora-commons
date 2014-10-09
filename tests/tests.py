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
from flask_fedora_commons import Repository, BIBFRAME, SCHEMA_ORG
from flask_fedora_commons import FEDORA_BASE_URL

class TestFedoraCommons(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True
        self.repo = Repository()
        self.repo.setup()
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
        self.work_rdf.add((self.work_uri,
                           BIBFRAME.workTitle,
                           rdflib.Literal("Original Work Title")))
        # Add RDF Graph to Fedora
        new_request = urllib.request.Request(
            str(self.work_uri),
            data=self.work_rdf.serialize(format='turtle'),
            method='PUT',
            headers={"Content-Type": "text/turtle"})
        urllib.request.urlopen(new_request)


    def test_repo_exists(self):
        self.assertTrue(self.repo is not None)

    def test__build_prefixes__(self):
        prefix_tst = "PREFIX bf: <http://bibframe.org/vocab/>\n"
        prefix_tst += "       schema: <http://schema.org/>\n"
        self.assertEqual(prefix_tst,
               self.repo.__build_prefixes__())
        self.assertEqual("PREFIX bf: <http://bibframe.org/vocab/>\n",
            self.repo.__build_prefixes__([[
                'bf',
                'http://bibframe.org/vocab/']]))


    def test__value_format__(self):
        self.assertEqual("<http://bibframe.org/vocab/Work>",
            self.repo.__value_format__('http://bibframe.org/vocab/Work'))
        self.assertEqual('"A most excellent work"',
            self.repo.__value_format__('A most excellent work'))


    def test_dedup(self):
##        self.repo.__dedup__()
        pass

    def test_delete(self):
        self.repo.delete(self.work_uri)
        self.assertFalse(self.repo.exists(self.work_uri))

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

    def test_exists(self):
        self.assertTrue(self.repo.exists(self.work_uri))
        self.assertFalse(self.repo.exists('http://example.org/Work/1'))

    def test_read(self):
        work_rdf = self.repo.read(str(self.work_uri))
        label = work_rdf.value(subject=self.work_uri,
                               predicate=rdflib.RDFS.label)
        self.assertEqual(label.value,
                         "Work for Unit Test")

    def test_remove(self):
        self.repo.remove([('rdf', str(rdflib.RDF))],
                         self.work_uri,
                         'rdf:type',
                         BIBFRAME.Monograph)
        work_rdf = self.repo.read(str(self.work_uri))
        work_types = [obj for obj in work_rdf.objects(
                subject=self.work_uri,
                predicate=rdflib.RDF.type)]
        self.assertNotIn(BIBFRAME.Monograph, work_types)


    def test_replace(self):
        self.repo.replace(
            [['bf', str(BIBFRAME)]],
            self.work_uri,
            'bf:workTitle',
            "Original Work Title",
            "A new title")
        work_rdf = self.repo.read(str(self.work_uri))
        self.assertEqual(
            "A new title",
            str(work_rdf.value(
                    subject=self.work_uri,
                    predicate=BIBFRAME.workTitle)))


    def test_repo_setup(self):
        fedora_namespaces = rdflib.Graph().parse("/".join([
            FEDORA_BASE_URL,
            "rest",
            "fcr:namespaces"]))
        prefNS_URI = rdflib.term.URIRef('http://purl.org/vocab/vann/preferredNamespaceUri')
        self.assertEqual(
            str(fedora_namespaces.value(
                subject=rdflib.term.URIRef(str(BIBFRAME)),
                predicate=prefNS_URI)),
            str(BIBFRAME))

    def test_search(self):
        work_results = self.repo.search("Unit Test")
        self.assertEqual(
            1,
            int(work_results.value(
                subject=rdflib.URIRef('http://localhost:8080/rest/fcr:search?q=Unit+Test'),
                predicate=rdflib.URIRef('http://sindice.com/vocab/search#totalResults'))))
        no_results = self.repo.search("4546WW")
        self.assertEqual(
            0,
            int(no_results.value(
                subject=rdflib.URIRef('http://localhost:8080/rest/fcr:search?q=4546WW'),
                predicate=rdflib.URIRef('http://sindice.com/vocab/search#totalResults'))))


    def test_update(self):
        self.repo.update([['schema', 'http://schema.org/']],
                         self.work_uri,
                         "schema:about",
                         "This is a test work")
        work_rdf = self.repo.read(str(self.work_uri))
        self.assertEqual(
            "This is a test work",
            str(work_rdf.value(subject=self.work_uri,
                predicate=SCHEMA_ORG.about)))
        self.repo.update(
            [('bf', str(BIBFRAME))],
            self.work_uri,
            "bf:sameAs",
            "http://example.org/Work/12334")
        work_rdf = self.repo.read(str(self.work_uri))
        self.assertEqual(
            rdflib.URIRef("http://example.org/Work/12334"),
            work_rdf.value(
                subject=self.work_uri,
                predicate=BIBFRAME.sameAs))





    def tearDown(self):
        self.repo.delete(urllib.parse.urljoin(FEDORA_BASE_URL, "/rest/test/"))


if __name__ == '__main__':
    unittest.main()
