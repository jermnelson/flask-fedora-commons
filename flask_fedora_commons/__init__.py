__version_info__ = ('0', '0', '8')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'MIT License'
__copyright__ = '(c) 2013, 2014 by Jeremy Nelson'

from flask import current_app, render_template


class Repository(object):
    """Class provides an interface to a Fedora Commons digital
     repository.
     """

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
        self.base_url = base_url

    def init_app(self, app):
        """
        Initializes a Flask app object for the extension.

        Args:
            app(Flask): Flask app
        """
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
                format='json-ld').decode())
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
        if not entity_exists(entity_id):
            create_entity(entity_id)
        print(entity_uri)
        ranges_set = set(schema_json['properties'][property_name]['ranges'])
        if len(literal_set.intersection(ranges_set)) > 0:
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