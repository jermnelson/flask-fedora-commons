"""
 FlaskFedoraCommons is a Flask extension for the Fedora Commons Digital
 Repository software

>> from flask_fedora_commons import Repository
>> repo = Repository()
"""
__version_info__ = ('0', '0', '9')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'MIT License'
__copyright__ = '(c) 2013, 2014 by Jeremy Nelson'

import json
import rdflib
import urllib

from flask import current_app, render_template
from string import Template

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

BIBFRAME = rdflib.Namespace("http://bibframe.org/vocab/")
FEDORA_BASE_URL = "http://localhost:8080"
FEDORA_NS = rdflib.Namespace('http://fedora.info/definitions/v4/rest-api#')
FEDORA_RELS_EXT = rdflib.Namespace(
    'http://fedora.info/definitions/v4/rels-ext#')
FCREPO = rdflib.Namespace("http://fedora.info/definitions/v4/repository#")
IDLOC_RT = rdflib.Namespace("http://id.loc.gov/vocabulary/relators/")
MADS = rdflib.Namespace("http://www.loc.gov/standards/mads/")
MADS_RDF = rdflib.Namespace("http://www.loc.gov/mads/rdf/v1#")
SCHEMA_ORG = rdflib.Namespace("http://schema.org/")
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')

DEFAULT_NAMESPACES = [
    ('bf', str(BIBFRAME)),
    ('fedora', str(FEDORA_NS)),
    ('fedorarelsext', str(FEDORA_RELS_EXT)),
    ('fcrepo', str(FCREPO)),
    ('idloc_rt', str(IDLOC_RT)),
    ('mads', str(MADS)),
    ('madsrdf', str(MADS_RDF)),
    ('owl', str(rdflib.OWL)),
    ('rdf', str(rdflib.RDF)),
    ('rdfs', str(rdflib.RDFS)),
    ('schema', str(SCHEMA_ORG))]

CONTEXT = {}
for row in DEFAULT_NAMESPACES:
    CONTEXT[row[0]] = row[1]

def build_prefixes(namespaces=None):
    """Internal function takes a list of prefix, namespace uri tuples and
    generates a SPARQL PREFIX string.

    Args:
        namespaces(list): List of tuples, defaults to BIBFRAME and
                          Schema.org

    Returns:
        string
    """
    if namespaces is None:
        namespaces = [
            ('bf', str(BIBFRAME)),
            ('schema', str(SCHEMA_ORG))
        ]
    output = "PREFIX {}: <{}>\n".format(
        namespaces[0][0],
        namespaces[0][1])
    if len(namespaces) == 1:
        return output
    else:
        for namespace in namespaces[1:]:
            output += "PREFIX  {}: <{}>\n".format(namespace[0], namespace[1])
    return output

def copy_graph(subject, existing_graph):
    """Function takes a subject and an existing graph, returns a new graph with
    all predicate and objects of the existing graph copied to the new_graph with
    subject as the new subject

    Args:
        subject(rdflib.URIRef): A URIRef subject
        existing_graph(rdflib.Graph): A rdflib.Graph

    Returns:
        rdflib.Graph
    """
    new_graph = rdflib.Graph()
    for predicate, object_ in existing_graph.predicate_objects():
        new_graph.add((subject, predicate, object_))
    return new_graph

class Repository(object):
    """Class provides an interface to a Fedora Commons digital
     repository.
     """

    def __init__(
        self,
        app=None,
        base_url='http://localhost:8080',
        namespaces=DEFAULT_NAMESPACES):
        """
        Initializes a Repository object

        Args:
            app(Flask): Flask app, default is None
            base_url(str): Base url for Fedora Commons, defaults to
                           localhost:8080.
            namespaces(list): List of namespace tuples of prefix, uri for
                              each namespace in Fedora
        """
        self.app = app
        self.namespaces = namespaces
        self.base_url = None
        if app is not None:
            self.init_app(app)
            if 'FEDORA_BASE_URL' in app.config:
                self.base_url = app.config.get('FEDORA_BASE_URL')
        if self.base_url is None:
            self.base_url = base_url
        # Removes trailing forward-slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        self.transaction = []


    def __build_url__(self, url):
        """Internal method takes a URL or URL fragment and builds a Fedora
        URI for the object based on URL, if a transaction exists, and
        returns the correct URL

        Args:
            url(str): String URL or URL fragment

        Returns:
            url(str): Full dereferenced URL to the Fedora object
        """
        return url

    def __dedup__(self,
                  subject,
                  graph):
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
        for uri in Repository.DEFAULT_ID_URIS:
            # Checks for duplicates
            for obj_uri in graph.objects(subject=subject, predicate=uri):
                sparql_url = urllib.parse.urljoin(
                    self.base_url,
                    "rest/fcr:sparql")
                sparql_template = Template("""SELECT ?x
                    WHERE { ?x <$uri> "$obj_uri" }""")
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

    def __value_format__(self, value):
        """Internal Method takes a value and constructs either an URI or
        literal string in constructing an SPAQRL query.

        """
        if value.startswith("http"):
            return "<{}>".format(value)
        else:
            return '"{}"'.format(value)

    def init_app(self, app):
        """
        Initializes a Flask app object for the extension.

        Args:
            app(Flask): Flask app
        """
        app.config.setdefault('FEDORA_BASE_URL', 'http://localhost:8080')
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def create_transaction(self):
        """Method creates a new transaction resource and sets instance's
        transaction."""
        request = urlllib.request.urlopen(
            urllib.parse.urljoin(self.base_url, 'fcr:tx'))
        self.transaction = request.read()


    def connect(self,
                fedora_url,
                data=None,
                method='Get'):
        """Method attempts to connect to REST servers of the Fedora
        Commons repository using optional data parameter.

        Args:
            fedora_url(string): Fedora URL
            data(dict): Data to through to REST endpoint
            method(str): REST Method, defaults to GET

        Returns:
            result(string): Response string from Fedora

        """
        if data is None:
            data = {}
        if not fedora_url.startswith("http"):
            fedora_url = urllib.parse.urljoin(self.base_url, fedora_url)
        request = urllib.request.Request(fedora_url,
                                         method=method)
        request.add_header('Accept', 'text/turtle')
        request.add_header('Content-Type', 'text/turtle')
        if len(data) > 0:
            request.data = data
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as err:
            if hasattr(err, 'reason'):
                print("failed to reach server at {} with {} method".format(
                    fedora_url,
                    request.method))
                print("Reason: ", err.reason)
                print("Data: ", data)
            elif hasattr(err, 'code'):
                print("Server error {}".format(err.code))
            raise err
        return response

    def as_json(self,
                entity_url,
                context=None):
        """Method takes a entity uri and attempts to return the Fedora Object
        as a JSON-LD.

        Args:
            entity_url(str): Fedora Commons URL of Entity
            context(None): Returns JSON-LD with Context, default is None

        Returns:
            str: JSON-LD of Fedora Object
        """
        try:
            urllib.request.urlopen(entity_url)
        except urllib.error.HTTPError:
            raise ValueError("Cannot open {}".format(entity_url))
        entity_graph = self.read(entity_url)
        entity_json = json.loads(
            entity_graph.serialize(
                format='json-ld',
                context=context).decode())
        return json.dumps(entity_json)

        # Provides standard CRUD operations on a Fedora Object
    def create(self, uri=None, graph=None, data=None):
        """Method takes an optional URI and graph, first checking if the URL is already
        present in Fedora, if not, creates a Fedora Object with the graph as
        properties. If URI is None, uses Fedora 4 default PID minter to create
        the object's URI.

        Args:
            uri(string): String of URI, default is None
            graph(rdflib.Graph): RDF Graph of subject, default is None
            data(object): Binary datastream that will be saved as fcr:content

        Returns:
            URI(string): New Fedora URI or None if uri already exists
        """
        if uri is not None:
            existing_entity = self.__dedup__(rdflib.URIRef(uri), graph)
            if existing_entity is not None:
                return # Returns nothing
        else:
            default_request = urllib.request.Request(
                "/".join([self.base_url, "rest"]),
                method='POST')
            uri = urllib.request.urlopen(default_request).read().decode()
        if graph is not None:
            new_graph = copy_graph(rdflib.URIRef(uri), graph)
            create_response = self.connect(
                uri,
                data=new_graph.serialize(format='turtle'),
                method='PUT')
            raw_response = create_response.read()
        return uri


    def delete(self, uri):
        """Method deletes a Fedora Object in the repository

        Args:
            uri(str): URI of Fedora Object
        """
        try:
            self.connect(uri, method='DELETE')
            return True
        except urllib.error.HTTPError:
            return False



    def exists(self, uri):
        """Method returns true is the entity exists in the Repository,
        false, otherwise

        Args:
            uri(str): Entity URI

        Returns:
            bool
        """
        ##entity_uri = "/".join([self.base_url, entity_id])
        try:
            urllib.request.urlopen(uri)
            return True
        except urllib.error.HTTPError:
            return False

    def flush(self):
        """Method flushes repository, deleting all objects"""
        base_graph = rdflib.Graph().parse('{}/rest'.format(self.base_url))
        has_child = rdflib.URIRef(
            'http://fedora.info/definitions/v4/repository#hasChild')
        for obj in base_graph.objects(predicate=has_child):
            self.delete(str(obj))\

    def insert(self,
               entity_id,
               property_uri,
               value):
        """Method inserts a new entity's property in Fedora4 Repository

        Args:
            entity_id(string): Unique ID of Fedora object
            property_uri(string): URI of property
            value: Value of the property, can be literal or URI reference

        Returns:
            boolean: True if successful changed in Fedora, False otherwise
        """
        if not entity_id.startswith("http"):
            entity_uri = urllib.parse.urljoin(self.base_url, entity_id)
        else:
            entity_uri = entity_id
        if entity_uri.endswith("/"):
            entity_uri = entity_uri[:-1]
        if not entity_id.endswith("fcr:metadata"):
            entity_uri = "/".join([entity_uri, "fcr:metadata"])
        if not self.exists(entity_id):
            self.create(entity_id)
        sparql_template = Template("""$prefix
        INSERT DATA {
             <$entity> $prop_uri $value_str;
        }""")
        sparql = sparql_template.substitute(
            prefix=build_prefixes(self.namespaces),
            entity=entity_uri,
            prop_uri=property_uri,
            value_str=self.__value_format__(value))
        update_request = urllib.request.Request(
            entity_uri,
            data=sparql.encode(),
            method='PATCH',
            headers={'Content-Type': 'application/sparql-update'})
        response = urllib.request.urlopen(update_request)
        if response.code < 400:
            return True
        return False


    def read(self, uri):
        """Method takes uri and creates a RDF graph from Fedora Repository

        Args:
            uri(str): URI of Fedora URI

        Returns:
            rdflib.Graph
        """
        read_response = self.connect(uri)
        fedora_graph = rdflib.Graph().parse(
            data=read_response.read(),
            format='turtle')
        return fedora_graph

    def remove(self,
               entity_id,
               property_uri,
               value):
        """Method removes a triple for the given/subject.

        Args:
            entity_id(string): Fedora Object ID, ideally URI of the subject
            property_uri(string):
            value(string):

        Return:
            boolean: True if triple was removed from the object
        """
        if not entity_id.startswith("http"):
            entity_uri = urllib.parse.urljoin(self.base_url, entity_id)
        else:
            entity_uri = entity_id
        sparql_template = Template("""$prefix
        DELETE {
            <$entity> $prop_name $value_str
        } WHERE {
            <$entity> $prop_name $value_str
        }""")
        sparql = sparql_template.substitute(
            prefix=build_prefixes(self.namespaces),
            entity=entity_uri,
            prop_name=property_uri,
            value_str=self.__value_format__(value))
        delete_property_request = urllib.request.Request(
            entity_uri,
            data=sparql.encode(),
            method='PATCH',
            headers={'Content-Type': 'application/sparql-update'})
        response = urllib.request.urlopen(delete_property_request)
        if response.code < 400:
            return True
        return False


    def replace(self,
                entity_id,
                property_name,
                old_value,
                value):
        """Method replaces a triple for the given entity/subject. Property
        name is from the schema.org vocabulary.

        Args:
            entity_id(string): Unique ID of Fedora object
            property_name(string): Prefix and property name i.e. schema:name
            old_value(string): Literal or URI of old value
            value(string): Literal or new value
        """
        if not entity_id.startswith("http"):
            entity_uri = '/'.join([self.base_url, self.transaction, entity_id])
        else:
            entity_uri = entity_id
        sparql_template = Template("""$prefix
            DELETE {
             <$entity> $prop_name $old_value
            } INSERT {
             <$entity> $prop_name $new_value
            } WHERE {
            }""")
        sparql = sparql_template.substitute(
            prefix=build_prefixes(self.namespaces),
            entity=entity_uri,
            prop_name=property_name,
            old_value=self.__value_format__(old_value),
            new_value=self.__value_format__(value))
        update_request = urllib.request.Request(
            entity_uri,
            data=sparql.encode(),
            method='PATCH',
            headers={'Content-Type': 'application/sparql-update'})
        response = urllib.request.urlopen(update_request)
        if response.code < 400:
            return True
        return False

    def search(self, query_term):
        """DEPRECIATED
        Method takes a query term and searches Fedora Repository using SPARQL
        search endpoint and returns a RDF graph of the search results.

        Args:
            query_term(str): String to search repository

        Returns:
            rdflib.Graph()
        """
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
        except urllib.error.URLError as error:
            raise error
        fedora_results = rdflib.Graph().parse(
            data=search_response.read(),
            format='turtle')
        return fedora_results


    def sparql(self, statement, end_point='fcr:sparql', accept_format='text/csv'):
        """DEPRECIATED
        Method takes and executes a generic SPARQL statement and returns
        the result. NOTE: The Fedora 4 supports a limited subset of SPARQL,
        see <https://wiki.duraspace.org/display/FF/RESTful+HTTP+API+-+Search#RESTfulHTTPAPI-Search-SPARQLEndpoint>
        for more information.

        Args:
            statement(string): SPARQL statement
            end_point(string): SPARQL URI end-point, default to fcr:sparql
            accept_format(string): Format for output, defaults to text/csv

        Returns:
            result(string): Raw decoded string of the result from executing the
            SPARQL statement
        """
        request = urllib.request.Request(
            '/'.join([self.base_url, 'rest', end_point]),
            data=statement.encode(),
            method='POST',
            headers={"Context-Type": "application/sparql-query",
                     "Accept": accept_format})
        result = urllib.request.urlopen(request)
        return result.read().decode()




    def teardown(self, exception):
        """Supporting method for Flask applications

        Args:
            exception: Exception
        """
        if self.app is not None:
            ctx = stack.top



