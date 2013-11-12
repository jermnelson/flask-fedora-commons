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

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def connect(self):
        return Repository()

    def teardown(self, excpetion):
        ctx = stack.top
        if hasattr(ctx, 'repository'):
            ctx.repository.close()

    @property
    def respository(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'repository'):
                ctx.repository = self.connect()
            return ctx.repository
