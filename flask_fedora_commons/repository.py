#-------------------------------------------------------------------------------
# Name:        repository
# Purpose:     Python 3 wrapper around a Fedora 4 digital repository
#
# Author:      Jeremy Nelson
#
# Created:     2014/06/06
# Copyright:   (c) Jeremy Nelson 2014
# Licence:     MIT
#-------------------------------------------------------------------------------
import json
import rdflib
from urllib.error import URLError
import urllib.request
import urllib.parse

BF_NS = rdflib.Namespace('http://bibframe.org/vocab')
MADS_NS = rdflib.Namespace("http://www.loc.gov/mads/rdf/v1#")
REST_API_NS = rdflib.Namespace('http://fedora.info/definitions/v4/rest-api#')

class Repository(object):
    """Python object wrapper around a Fedora 4 digital repository

    """

    def __init__(self, **kwargs):
        self.base_url = kwargs.get('base_url', 'http://localhost:8080/')



    def __connect__(self, fragment='rest/', data={}, method='GET'):
        """Internal method attempts to connect to REST servers of the Fedora
        Commons repository using optional data parameter.

        Args:
            fragment(dict): URL fragment
            data(dict): Data to through to REST endpoint

        Returns:
            result(string): Response string from Fedora

        """
        # Insures we're using the Fedora 4 REST services
##        if not fragment.startswith('rest'):
##            fragment = 'rest/{}'.format(fragment)
        fedora_url = urllib.parse.urljoin(self.base_url, fragment)
        request = urllib.request.Request(fedora_url,
                                         method=method)
        request.add_header('Accept', 'text/turtle')
        request.add_header('Content-Type', 'text/turtle')
        if len(data) > 0:
            request.data = data
        try:
            response = urllib.request.urlopen(request)
        except URLError as e:
            if hasattr(e, 'reason'):
                print("failed to reach server at {} with {} method".format(
                    fedora_url,
                    request.method))
                print("Reason: ", e.reason)
                print("Data: ", data)
            elif hasattr(e, 'code'):
                print("Server error {}".format(e.code))
            raise e
        return response

        return fedora_graph

    def __dedup__(self, subject, graph):
        """Internal method takes a RDF graph, cycles through the RDFS
        label and BIBFRAME authorizedAccessPoint triples to see if the graph's
        entity already exists in Fedora. As other searchable unique triples are
        added from other vocabularies, they should be added to this method.

        Args:
            subject(rdflib.rdflibURIRef): RDF Subject URI
            graph(rdflib.Graph): RDF Graph

        Returns:
            graph(rdflib.Graph): Existing RDF Graph in Fedora or None
        """
        for uri in [BF_NS.authorizedAccessPoint,
                    rdflib.RDFS.label,
                    MADS_NS.authoritativeLabel]:
            # Checks for duplicates
            for obj_uri in graph.objects(
                subject=subject,
                predicate=uri):
                sparql_url = urllib.parse.urljoin(
                    self.base_url,
                    "rest/fcr:sparql")
                sparql_query = """SELECT ?x
                WHERE \{ ?x <{0}> "{1}" \}""".format(
                    uri,
                    obj_uri)
                search_request = urllib.request.Request(
                    sparql_url,
                    data=sparql_query.encode())
                search_request.add_header(
                    "Accept",
                    "text/turtle")
                search_request.add_header(
                    "Content-Type",
                    "application/sparql-query")
                try:
                    search_response = urllib.request.urlopen(search_request)
                    if search_response.code < 400:
                        return rdflib.Graph().parse(
                            data=search_response.read(),
                            format='turtle')
                except urllib.error.HTTPError:
                    print("Error with sparql query:\n{}".format(sparql_query))


    def __transaction__(self):
        """Internal method uses Fedora 4 transactions to wrap up a series of
        REST operations in a single transaction.
        """
        pass

    # Provides standard CRUD operations on a Fedora Object
    def create(self, uri, graph):
        """Method takes a URL and a graph, first checking if the URL is already
        present in Fedora, if not, creates a Fedora Object with the graph as
        properties

        Args:
            uri(string): String of URI
            graph(rdflib.Graph): RDF Graph of subject

        Returns:
            URI(string): New Fedora URI or None if uri already exists
        """
        existing_entity = self.__dedup__(rdflib.URIRef(uri), graph)
        if existing_entity:
            return # Returns nothing
        print(rdflib.URIRef(uri), graph)
        # Replace all external subject uri with fedora base_url
        split_result = urllib.parse.urlsplit(uri)

        create_response = self.__connect__(
            split_result.path,
            data=graph.serialize(format='turtle'),
            method='PUT')
        return create_response.read()

    def delete(self, uri):
        delete_response = self.__connect__(uri, method='DELETE')
        return True

    def flush(self):
        """Method flushes repository, deleting all objects"""
        base_graph = rdflib.Graph().parse('{}/rest/'.format(self.base_url))
        has_child = rdflib.URIRef(
            'http://fedora.info/definitions/v4/repository#hasChild')
        for obj in base_graph.objects(
            predicate=has_child):
                self.delete(str(obj))


    def read(self, uri):
        read_response = self.__connect__(uri)
        fedora_graph = rdflib.Graph().parse(
            data=read_response.read(),
            format='turtle')
        return fedora_graph

    def search(self, query_term):
        fedora_search_url = urllib.parse.urljoin(self.base_url,
                                                 'fcr:search')
        search_request = urllib.request.Request(
            fedora_url,
            data=urllib.parse.urlencode({"q": query_term}))
        request.add_header('Accept', 'text/turtle')
        try:
            search_response = urllib.request.urlopen(search_request)
        except URLError as e:
            raise e
        fedora_results = rdflib.Graph().parse(data=search_response.read(),
            format='turtle')
        return fedora_results

    def update(self, url, data):
        pass






