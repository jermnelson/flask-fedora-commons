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
from string import Template
from urllib.error import URLError
import urllib.request
import urllib.parse

BF_NS = rdflib.Namespace('http://bibframe.org/vocab')
MADS_NS = rdflib.Namespace("http://www.loc.gov/mads/rdf/v1#")
REST_API_NS = rdflib.Namespace('http://fedora.info/definitions/v4/rest-api#')

class Repository(object):
    """Python object wrapper around a Fedora 4 digital repository

    """
    literal_set = set(['Text', 'Number', 'Date'])

    def __init__(self, **kwargs):
        self.base_url = kwargs.get('base_url', 'http://localhost:8080')
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]


    def __connect__(self, fedora_url, data={}, method='GET'):
        """Internal method attempts to connect to REST servers of the Fedora
        Commons repository using optional data parameter.

        Args:
            fedora_url(string): Fedora URL
            data(dict): Data to through to REST endpoint

        Returns:
            result(string): Response string from Fedora

        """
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
        if graph is None:
            return
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

                sparql_template = Template("""SELECT ?x
                WHERE { ?x <$uri> "$obj_uri" \}""")
                sparql_query = sparql_template.substitute(
                    uri=uri,
                    obj_uri=obj_uri)
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
    def create(self, uri, graph=None):
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
        if graph is not None:
            create_response = self.__connect__(
                uri,
                data=graph.serialize(format='turtle'),
                method='PUT')
        else:
            # Creates a stub Fedora object for the uri
            create_response = self.__connect__(uri,
                method='PUT')
        return create_response.read()

    def delete(self, uri):
        delete_response = self.__connect__(uri, method='DELETE')
        return True

    def exists(self, entity_id):
        entity_uri = "/".join([self.base_url, entity_id])
        try:
            urllib.request.urlopen(entity_uri)
            return True
        except urllib.error.HTTPError:
            return False

    def flush(self):
        """Method flushes repository, deleting all objects"""
        base_graph = rdflib.Graph().parse('{}/rest'.format(self.base_url))
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
        fedora_search_url = "/".join([self.base_url, 'rest', 'fcr:search'])
        fedora_search_url = "{}?{}".format(
            fedora_search_url,
            urllib.parse.urlencode({"q": query_term}))
        search_request = urllib.request.Request(
            fedora_search_url,
            method='GET')
        search_request.add_header('Accept', 'text/turtle')
        try:
            search_response = urllib.request.urlopen(search_request)
        except URLError as e:
            raise e
        fedora_results = rdflib.Graph().parse(data=search_response.read(),
            format='turtle')
        return fedora_results

    def update_entity(self,
                      entity_id,
                      property_name,
                      value):
        """Method updates a Entity's property in Fedora4

        Args:
            entity_id(string): Unique ID of Fedora object
            property_name(string): Name of property
            value: Value of the property

        Returns:
            boolean: True if successful changed in Fedora, False otherwise
        """
        entity_uri = "/".join([self.base_url, 'rest', entity_id])
        if not self.exists(entity_id):
            self.create(entity_id)
        ranges_set = set(schema_json['properties'][property_name]['ranges'])
        prefix = """PREFIX schema: <http://schema.org/>
            bf: <http://bibframe.org>
            dc: <http://purl.org/dc/elements/1.1/>
            rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"""
        if len(Repository.literal_set.intersection(ranges_set)) > 0:
            sparql_template = Template("""{}
        INSERT DATA {
            <$entity> $prop_name "$prop_value"
        }""".format(prefix))
        else:
            sparql_template = Template("""{}
        INSERT DATA {
            <$entity> $prop_name <$prop_value>
        }""".format(prefix))
        sparql = sparql_template.substitute(
            entity=entity_uri,
            prop_name="schema:{}".format(property_name),
            prop_value=value)
        update_request = urllib.request.Request(
            entity_uri,
            data=sparql.encode(),
            method='PATCH',
            headers={'Content-Type': 'application/sparql-update'})
        response = urllib.request.urlopen(update_request)
        if response.code < 400:
            return True
        return False






