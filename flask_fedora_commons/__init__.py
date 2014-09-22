__version_info__ = ('0', '0', '8')
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
MADS = rdflib.Namespace("http://www.loc.gov/standards/mads/")
MADS_RDF =  rdflib.Namespace("http://www.loc.gov/mads/rdf/v1#")
SCHEMA_ORG = rdflib.Namespace("http://schema.org/")
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')

CONTEXT = {
    'bf': str(BIBFRAME),
    'fedora': str(FEDORA_NS),
    'fedorarelsext': str(FEDORA_RELS_EXT),
    'mads': str(MADS),
    'madsrdf': str(MADS_RDF)}
schema_json = json.loads(
    urllib.request.urlopen('http://schema.rdfs.org/all.json').read().decode())

class Repository(object):
    """Class provides an interface to a Fedora Commons digital
     repository.
     """
    DEFAULT_ID_URIS = [
        BIBFRAME.authorizedAccessPoint,
        rdflib.RDFS.label,
        MADS.authoritativeLabel]
    LITERAL_SET = set(["Text", "Number", "Date", "Duration"])

    def __init__(self, app=None, base_url='http://localhost:8080'):
        """
        Initializes a Repository object

        Args:
            app(Flask): Flask app, default is None
            base_url(str): Base url for Fedora Commons, defaults to
                           localhost:8080.
        """
        self.app = app
        if app is not None:
            self.init_app(app)
            if 'FEDORA_BASE_URL' in app.config:
                self.base_url = app.config.get('FEDORA_BASE_URL')

        self.base_url = base_url

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


    def connect(self,
                fedora_url,
                data={},
                method='GET'):
        """Method attempts to connect to REST servers of the Fedora
        Commons repository using optional data parameter.

        Args:
            fedora_url(string): Fedora URL
            data(dict): Data to through to REST endpoint
            method(str): REST Method, defaults to GET

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
            abort(404)
        entity_graph = self.read(entity_url)
        entity_json = json.loads(
            entity_graph.serialize(
                format='json-ld',
                context=context).decode())
        return json.dumps(entity_json)

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
            create_response = self.connect(
                uri,
                data=graph.serialize(format='turtle'),
                method='PUT')
        else:
            # Creates a stub Fedora object for the uri
            create_response = self.connect(uri,
                method='PUT')
        return create_response.read()

    def delete(self, uri):
        delete_response = self.connect(uri, method='DELETE')
        return True

    def exists(self, entity_id):
        ##entity_uri = "/".join([self.base_url, entity_id])
        try:
            urllib.request.urlopen(entity_id)
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
        read_response = self.connect(uri)
        fedora_graph = rdflib.Graph().parse(
            data=read_response.read(),
            format='turtle')
        return fedora_graph

    def remove(self,
               ns_prefix,
               ns_uri,
               entity_id,
               property_uri,
               value):
        """Method removes a triple for the given/subject.

        Args:
            ns_prefix(string): Prefix of namespace
            ns_uri(string): URI of namespace
            entity_id(string): Fedora Object ID, ideally URI of the subject
            property_uri(string):
            value(string):

        Return:
            boolean: True if triple was removed from the object
        """
        if not entity_id.startswith("http"):
            entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
        else:
            entity_uri = entity_id
        if value.startswith("http"):
            value_str = "<{}>".format(value)
        else:
            value_str = value
        sparql_template = Template("""PREFIX $prefix: <$namespace>
        DELETE {
            <$entity> $prop_name $value_str
        } WHERE {
            <$entity> $prop_name $value_str
        }""")
        sparql = sparql_template.substitute(
            prefix=ns_prefix,
            namespace=ns_uri,
            entity=entity_uri,
            prop_name=property_uri,
            value_str=value_str)
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


        """
        if not entity_id.startswith("http"):
            entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
        else:
            entity_uri = entity_id
        if len(literal_set.intersection(
            ['properties'][property_name]['ranges'])) < 1 or\
            not 'ranges' in ['properties'][property_name]:
            sparql_template = Template("""PREFIX schema: <http://schema.org/>
            DELETE {
             <$entity> $prop_name <$old_value>
            } INSERT {
             <$entity> $prop_name <$new_value>
            } WHERE {
            }""")
        else:
            sparql_template = Template("""PREFIX schema: <http://schema.org/>
            DELETE {
             <$entity> $prop_name "$old_value"
            } INSERT {
             <$entity> $prop_name "$new_value"
            } WHERE {
            }""")
        sparql = sparql_template.substitute(
            entity=entity_uri,
            prop_name="schema:{}".format(property_name),
            old_value=old_value,
            new_value=value)
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

    def setup(self):
        """Method registers common namespaces, loads various graphs with initial
        mappings, and preps Fedora 4 for full use in the Catalog Pull Platform.
        """
        fedora_namespace_uri = "/".join([
            self.base_url,
            'rest',
            'fcr:namespaces'])
        sparql_template = Template("""INSERT {
        <$uri> <http://purl.org/vocab/vann/preferredNamespacePrefix> "$ns"
        } WHERE {

        }""")
        def process_namespace(uri, namespace):
            sparql = sparql_template.substitute(uri=uri,
                ns=namespace)
            request = urllib.request.Request(
                fedora_namespace_uri,
                data=sparql.encode(),
                headers={'Content-Type': 'application/sparql-update'})
            response = urllib.request.urlopen(request)

        # Register BIBFRAME, Schema.org, and MADS namespaces
        process_namespace(str(BIBFRAME), 'bf')
        process_namespace(str(MADS), 'mads')
        process_namespace(str(SCHEMA_ORG), 'schema')





    def teardown(self, exception):
        ctx = stack.top


    def update(self,
               entity_id,
               property_name,
               value):
        """Method updates the Entity's property in Fedora4 Repository

        Args:
            entity_id(string): Unique ID of Fedora object
            property_name(string): Name of schema.org property
            value: Value of the schema.org property

        Returns:
            boolean: True if successful changed in Fedora, False otherwise
        """
        if not entity_id.startswith("http"):
            entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
        else:
            entity_uri = entity_id
        if not self.exists(entity_id):
            self.create(entity_id)
        ranges_set = set(schema_json['properties'][property_name]['ranges'])
        if len(Repository.LITERAL_SET.intersection(ranges_set)) > 0:
            sparql_template = Template("""PREFIX schema: <http://schema.org/>
        INSERT DATA {
            <$entity> $prop_name "$prop_value"
        }""")
        else:
            sparql_template = Template("""PREFIX schema: <http://schema.org/>
        INSERT DATA {
            <$entity> $prop_name <$prop_value>
        }""")
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