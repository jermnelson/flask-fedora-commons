__version_info__ = ('0', '0', '6')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'MIT License'
__copyright__ = '(c) 2013, 2014 by Jeremy Nelson'

from lib.server import Repository
from flask import current_app, render_template

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

import xml.etree.ElementTree as etree

FEDORA_NS = 'info:fedora/fedora-system:def/relations-external#'
FOXML_NS = 'info:fedora/fedora-system:def/foxml#'
RDF_NS = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

class FedoraCommons(object):
    """Class provides an interface to a Fedora Commons digital
     repository.
     """

    def __init__(self, app=None):
        """
        Initializes a :class:`FedoraCommons` object

        :param app: Flask app, default is None
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes a :class:`Flask` app object for the extension.

        :param app: Flask app
        """
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def connect(self):
        """
        Returns a :class:`Repository` object initializes with default
        configuration values
        """
        return Repository(root=self.app.config.get('FEDORA_ROOT'),
                          username=self.app.config.get('FEDORA_USER'),
                          password=self.app.config.get('FEDORA_PASSWORD'))



    def create_stubs(self,
                     mods_xml,
                     title,
                     parent_pid,
                     num_objects,
                     content_model):
        """
        Method creates 1-n number of basic Fedora Objects in a repository


        :param mods_xml: MODS XML used for all stub MODS datastreams
        :param title: Title of Fedora Object
        :param parent_pid: PID of Parent collection
        :param num_objects: Number of stub records to create in the parent collection
        :param content_model: Content model for the stub records, defaults to
                              adr:adrBasicObject
        :rtype list: List of PIDS
        """
        pids = []
        for i in xrange(0, int(num_objects)):
            # Retrieves the next available PID
            new_pid = self.repository.api.ingest(text=None)
            # Sets Stub Record Title
            self.repository.api.modifyObject(pid=new_pid,
                                             label=title,
                                             ownerId=self.app.config.get('FEDORA_USER'),
                                             state="A")
            # Adds MODS datastream to the new object
            self.repository.api.addDatastream(pid=new_pid,
                                              dsID="MODS",
                                              dsLabel="MODS",
                                              mimeType="text/xml",
                                              content=mods_xml)
            # Add RELS-EXT datastream
            rels_ext = render_template('rels-ext.xml',
                                       object_pid=new_pid,
                                       content_model=content_model,
                                       parent_pid=parent_pid)
            self.repository.api.addDatastream(pid=new_pid,
                                              dsID="RELS-EXT",
                                              dsLabel="RELS-EXT",
                                              mimeType="application/rdf+xml",
                                              content=rels_ext)
            pids.append(new_pid)
        return pids

    def get_all_pids(self, content_model, only_active=True):
        """Method returns a list of all pids matching collection's content model.

        Args:
            content_model: Fedora Content Model for the Collection
            only_active: Boolean, include only active Fedora Objects in result

        Returns:
            list: List of PIDS in the Repository
        """
        pids = set()
        all_collections_sparql = '''
        PREFIX fedora: <info:fedora/fedora-system:def/relations-external#>
        PREFIX fedora-model: <info:fedora/fedora-system:def/model#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT $pid
        FROM <#ri>
        WHERE {{
        $pid fedora-model:hasModel <{}>
        }}'''.format(content_model)
        for row in self.repository.risearch.sparql_query(all_collections_sparql):
            collection_pid = row.get('pid').split("/")[-1]
            for child_pid in self.get_collection_pids(collection_pid,
                                                      only_active):
                pids.add(child_pid)
        return list(pids)

    def get_collection_pids(self, collection_pid, only_active=True):
        """
        Method returns a list of pids that are in a collection

        Parameters:
            collection_pid: Collection PID
            only_active: Boolean, include only active Fedora Objects in result

        Returns:
            list: List of pids
        """
        pids = []
        get_collection_sparql = '''
        PREFIX fedora: <info:fedora/fedora-system:def/relations-external#>
        SELECT ?a
        FROM <#ri>
        WHERE
        {{
          ?a fedora:isMemberOfCollection <info:fedora/{}>
        }}
        '''.format(collection_pid)
        for row in self.repository.risearch.sparql_query(get_collection_sparql):
            pid = row.get('a').split("/")[-1]
            if only_active is True:
                fo_xml = etree.XML(self.repository.api.getObjectXML(pid)[0])
                fo_state = fo_xml.find(
                "{{{0}}}objectProperties/{{{0}}}property[@NAME='info:fedora/fedora-system:def/model#state']".format(FOXML_NS))
                if fo_state.attrib["VALUE"].startswith("Active"):
                    pids.append(pid)
            else:
                pids.append(pid)
        return pids

    def move(self, source_pid, collection_pid):
        """
        Method takes a source_pid and collection_pid,
        retrives source_pid RELS-EXT and updates
        fedora:isMemberOfCollection value with new collection_pid

        :param source_pid: Source Fedora Object PID
        :param collection_pid: Collection Fedora Object PID
        :rtype boolean: True if move was a success
        """
        raw_rels_ext = self.repository.api.getDatastreamDissemination(
            pid=source_pid,
            dsID='RELS-EXT')
        rels_ext = etree.XML(raw_rels_ext[0])
        collection_of = rels_ext.find(
            '{{{0}}}Description/{{{1}}}isMemberOfCollection'.format(
                RDF_NS,
                FEDORA_NS))
        if collection_of is not None:
            attrib_key = '{{{0}}}resource'.format(RDF_NS)
            new_location = "info:fedora/{0}".format(collection_pid)
            collection_of.attrib[attrib_key] = new_location
            self.repository.api.modifyDatastream(pid=source_pid,
                                                 dsID="RELS-EXT",
                                                 dsLabel="RELS-EXT",
                                             mimeType="application/rdf+xml",
                                             content=etree.tostring(rels_ext))
            return True



    def teardown(self, exception):
        """
        Teardown and closes the connection to a :class:`Repository` instance

        :param exception: Exception to catch during teardown
        """
        pass
        ## ctx = stack.top

    @property
    def repository(self):
        """
        Property method function returns or creates a class property for
        a :class:`Repository` instance.
        """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'repository'):
                ctx.repository = self.connect()
            return ctx.repository
