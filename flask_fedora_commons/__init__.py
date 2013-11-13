__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'Apache License, Version 2.0'
__copyright__ = '(c) 2013 by Jeremy Nelson'
                    
from lib.server import Repository
from flask import current_app

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


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
        return Repository()

    def teardown(self, exception):
        """
        Teardown and closes the connection to a :class:`Repository` instance

        :param exception: Exception to catch during teardown
        """
        ctx = stack.top
        if hasattr(ctx, 'repository'):
            ctx.repository.close()

    @property
    def respository(self):
        """
        Property method function returns or creates a class property for
        a :class:`Repository` instance.
        """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'repository'):
                ctx.repository = self.connect()
            return ctx.repository
