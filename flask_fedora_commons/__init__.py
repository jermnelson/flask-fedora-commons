__version_info__ = ('0', '0', '2')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'MIT License'
__copyright__ = '(c) 2013 by Jeremy Nelson'
                    
from lib.server import Repository
from flask import current_app

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

import xml.etree.ElementTree as etree

FEDORA_NS = 'info:fedora/fedora-system:def/relations-external#'
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
