"""-----------------------------------------------------------------------------
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
#----------------------------------------------------------------------------"""
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

from flask import Flask
from flask import current_app
from flask_fedora_commons import build_prefixes
from flask_fedora_commons import Repository
from flask_fedora_commons import BIBFRAME
from flask_fedora_commons import FEDORA_BASE_URL
from flask_fedora_commons import SCHEMA_ORG

class TestBuildPrefixes(unittest.TestCase):
    "Unit tests for the flask_fedora_commons.build_prefixes function"

    def setUp(self):
        "Standard unit test setUp"
        pass

    def test_default_namespaces(self):
        "Tests default namespaces for build_prefixes"
        prefix_tst = "PREFIX bf: <http://bibframe.org/vocab/>\n"
        prefix_tst += "PREFIX  schema: <http://schema.org/>\n"
        self.assertEqual(
            prefix_tst,
            build_prefixes())

    def test_custom_namespaces(self):
        "Tests passing in custom namespaces into function"
        self.assertEqual(
            "PREFIX bf: <http://bibframe.org/vocab/>\n",
            build_prefixes(
                [['bf', 'http://bibframe.org/vocab/']]))

    def tearDown(self):
        "Standard unit test overridden teardown method"
        pass

class TestFedoraCommons(unittest.TestCase):
    "Unit tests for flask_fedora_commons.Repository class"

    def setUp(self):
        "Setup's repository, assumes Fedora 4 is localhost:8080"
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
        "Tests if repository exists"
        self.assertTrue(self.repo is not None)




    def test__value_format__(self):
        """Tests simple function that returns SPARQL format for object, either
        wraps URI with <{URI}> or literal value with quotes "{VALUE}" """
        self.assertEqual(
            "<http://bibframe.org/vocab/Work>",
            self.repo.__value_format__('http://bibframe.org/vocab/Work'))
        self.assertEqual(
            '"A most excellent work"',
            self.repo.__value_format__('A most excellent work'))

    def test_create(self):
        "Method tests default creation of an opaque URI"
        default_uri = self.repo.create()
        self.assertTrue(default_uri)
        # Remove default_uri because it won't be in test collection
        self.repo.delete(default_uri)

    def test_create_uri(self):
        "Method tests creation of a URI pattern in Fedora"
        bibframe_test_uri = self.repo.create(uri=self.work_uri)
        self.assertEqual(
            bibframe_test_uri,
            self.work_uri)

    def test_create_graph(self):
        "Method tests creation of a URI with an existing graph"
        new_graph = rdflib.Graph()
        test_uri = rdflib.URIRef('http://example.org/1234')
        new_graph.add(
            (test_uri,
            BIBFRAME.workTitle,
            rdflib.Literal("Example Title")))
        bibframe_uri = self.repo.create(uri=None, graph=new_graph)
        self.assertTrue(bibframe_uri)
        fedora_graph = rdflib.Graph().parse(bibframe_uri)
        self.assertEqual(
            "Example Title",
            str(fedora_graph.value(
                subject=rdflib.URIRef(bibframe_uri),
                predicate=BIBFRAME.workTitle)))
        self.repo.delete(bibframe_uri)


    def test_create_uri_graph(self):
        "Method tests creation of Fedora object with existing URI and Graph"
        new_graph = rdflib.Graph()
        new_graph.add(
            (self.work_uri,
            BIBFRAME.title,
            rdflib.URIRef('http://example.org/4567')))
        result = self.repo.create(
            uri=self.work_uri,
            graph=new_graph)
        self.assertEqual(self.work_uri, result)
        fedora_graph = rdflib.Graph().parse(self.work_uri)
        self.assertEqual(
            'http://example.org/4567',
            str(fedora_graph.value(
                subject=self.work_uri,
                predicate=BIBFRAME.title)))


    def test_dedup(self):
        "Tests deduplication method for repository"
##        self.repo.__dedup__()
        pass

    def test_delete(self):
        "Test delete a Fedora object based on an URI"
        self.repo.delete(self.work_uri)
        self.assertFalse(self.repo.exists(self.work_uri))

    def test_as_json(self):
        "Tests outputting JSON-LD without Context"
        # JSON-LD without Context
        work_json = json.loads(self.repo.as_json(str(self.work_uri)))
        self.assertEqual(work_json[0]['@id'], str(self.work_uri))

    def test_as_json_context(self):
        "Tests outputing Fedora 4 object as JSON-LD with Context"
        # JSON-LD with Context
        work_json = json.loads(
            self.repo.as_json(
                str(self.work_uri),
                context={
                    "@vocab": "http://bibframe.org/vocab/",
                    "fcrepo": "http://fedora.info/definitions/v4/repository#",
                    "fedora": "http://fedora.info/definitions/v4/rest-api#",
                    "@language": "en"}))
        self.assertEqual(work_json['@id'], str(self.work_uri))

    def test_exists(self):
        "Tests if a Fedora Object exists in the repository"
        self.assertTrue(self.repo.exists(self.work_uri))
        self.assertFalse(self.repo.exists('http://example.org/Work/1'))

    def test_read(self):
        "Tests if a Fedora Object can be read into a rdflib.Graph object"
        work_rdf = self.repo.read(str(self.work_uri))
        label = work_rdf.value(subject=self.work_uri,
                               predicate=rdflib.RDFS.label)
        self.assertEqual(label.value,
                         "Work for Unit Test")

    def test_remove(self):
        "Tests a property can be removed from a Fedora Object"
        self.repo.remove(self.work_uri,
                         'rdf:type',
                         BIBFRAME.Monograph)
        work_rdf = self.repo.read(str(self.work_uri))
        work_types = [
            obj for obj in work_rdf.objects(
                subject=self.work_uri,
                predicate=rdflib.RDF.type)]
        self.assertNotIn(BIBFRAME.Monograph, work_types)


    def test_replace(self):
        """Tests if Fedora Object's property value (the object in a
        subject-predicate-object triple) can be replaced"""
        self.repo.replace(
            self.work_uri,
            'bf:workTitle',
            "Original Work Title",
            "A new title")
        work_rdf = self.repo.read(str(self.work_uri))
        self.assertEqual(
            "A new title",
            str(
                work_rdf.value(
                    subject=self.work_uri,
                    predicate=BIBFRAME.workTitle)))


    def test_repo_setup(self):
        "Tests if all namespaces are registered in the repository"
        fedora_namespaces = rdflib.Graph().parse("/".join([
            FEDORA_BASE_URL,
            "rest",
            "fcr:namespaces"]))
        pref_namespace_uri = rdflib.term.URIRef(
            'http://purl.org/vocab/vann/preferredNamespaceUri')
        self.assertEqual(
            str(fedora_namespaces.value(
                subject=rdflib.term.URIRef(str(BIBFRAME)),
                predicate=pref_namespace_uri)),
            str(BIBFRAME))

    def test_search(self):
        "Tests basic SPARQL "
        work_results = self.repo.search("Unit Test")
        self.assertEqual(
            1,
            int(work_results.value(
                subject=rdflib.URIRef(
                    'http://localhost:8080/rest/fcr:search?q=Unit+Test'),
                predicate=rdflib.URIRef(
                    'http://sindice.com/vocab/search#totalResults'))))
        no_results = self.repo.search("4546WW")
        self.assertEqual(
            0,
            int(no_results.value(
                subject=rdflib.URIRef(
                    'http://localhost:8080/rest/fcr:search?q=4546WW'),
                predicate=rdflib.URIRef(
                    'http://sindice.com/vocab/search#totalResults'))))


    def test_insert(self):
        "Tests inserting a new property to an existing Fedora Object"
        self.repo.insert(self.work_uri,
                         "schema:about",
                         "This is a test work")
        work_rdf = self.repo.read(str(self.work_uri))
        self.assertEqual(
            "This is a test work",
            str(
                work_rdf.value(
                    subject=self.work_uri,
                    predicate=SCHEMA_ORG.about)))
        self.repo.insert(
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
        """Standard unit test overridden teardown method, deletes all Fedora
        objects stored under rest/tests"""
        self.repo.delete(urllib.parse.urljoin(FEDORA_BASE_URL, "/rest/test/"))

class TestFlaskExtension(unittest.TestCase):
    "Unit tests for use of Repository as a Flask extension"

    def setUp(self):
        "Setup's repository, assumes Fedora 4 is localhost:8080"
        application = Flask(__name__)
        self.repo = Repository(app=application)
        self.repo.setup()
        self.client = self.repo.app.test_client()


    def test_app_exists(self):
        "Method tests if app exits"
        rev = self.client.get('/')
        self.assertTrue(rev)

    def tearDown(self):
        "Standard unit test overridden teardown method"
        pass



if __name__ == '__main__':
    unittest.main()
