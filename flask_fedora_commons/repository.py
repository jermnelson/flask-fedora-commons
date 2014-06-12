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

RDF_NS = rdflib.RDF
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
        if not fragment.startswith('rest'):
            fragment = 'rest/{}'.format(fragment)
        fedora_url = urllib.parse.urljoin(self.base_url, fragment)
        request = urllib.request.Request(fedora_url,
                                         method=method)
        request.add_header('Accept', 'text/turtle')
        if len(data) > 0:
            request.data = data
        try:
            response = urllib.request.urlopen(request)

        except URLError as e:
            if hasattr(e, 'reason'):
                print("failed to reach server at {}".format(fedora_url))
                print("Reason: ", e.reason)
            elif hasattr(e, 'code'):
                print("Server error {}".format(e.code))
            raise e
        return response

        return fedora_graph

    def __dedup__(self, token):
        sparql_url = urllib.parse.urljoin(self.base_url, "rest/fcr:sparql")
        sparql_query = """SELECT ?x
        WHERE ?x <http://bibframe/vocab/authorizedAccessPoint> "{}" """.format(
            token)
        search_request = urllib.request.Request(
                sparql_url,
                data=b"{}".format(sparql_query))
        search_request.add_header(
            "Accept",
            "text/turtle")
        search_request.add_header(
                "Content-Type",
                "application/sparql-query")
        search_response = urllib.request.urlopen(search_request)
        if search_response.code < 400:
            return rdflib.Graph().parse(
                data=search_response.read(),
                format='turtle')

    def __transaction__(self):
        """Internal method uses Fedora 4 transactions to wrap up a series of
        REST operations in a single transaction.
        """
        pass

    # Provides standard CRUD operations on a Fedora Object
    def create(self, graph, url=None, workspace=None):
        # Checks for duplicates
        auth_access_uri = rdflib.URIRef(
            'http://bibframe/vocab/authorizedAccessPoint')
        for auth_access_pt in graph.objects(
            predicate=auth_access_uri):
                if self.__dedup__(auth_access_pt.value()):
                    return
        create_response = self.__connect__(
            url,
            data==graph.serialize(format='turtle'),
            method='PUT')
        return create_response.read()

    def delete(self, url):
        delete_response = self.__connect__(url, method='DELETE')
        return True

    def read(self, url):
        read_response = self.__connect__(url)
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






