#-------------------------------------------------------------------------------
# Name:        repository
# Purpose:     Python wrapper around a Fedora 4 digital repository
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

RDF_NS = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
REST_API_NS = rdflib.Namespace('http://fedora.info/definitions/v4/rest-api#')

class Repository(object):
    """Python object wrapper around a Fedora 4 digital repository

    """

    def __init__(self, **kwargs):
        self.base_url = kwargs.get('base_url', 'http://localhost:8080/')


    def __connect__(self, fragment='rest/', data={}, method='GET'):
        """Internal method attempts to connect to REST servers of the Fedora
        Commons repository using the optional data.

        Args:
            data(dict): Data to through to REST endpoint

        Returns:
            result(string): Response string from Fedora

        """
        # Insures we're using the Fedora 4 REST services
        if not fragment.startswith('rest/'):
            fragment = 'rest/{}'.format(fragment)
        fedora_url = urllib.parse.urljoin(self.base_url, fragment)
        request = urllib.request.Request(fedora_url,
                                         data=data,
                                         method=method)
        try:
            response = urllib.request.urlopen(request)
        except URLError as e:
            if hasattr(e, 'reason'):
                print("failed to reach server at {}".format(self.base_url))
                print("Reason: ", e.reason)
            elif hasattr(e, 'code'):
                print("Server error {}".format(e.code))

    def __transaction__(self):
        """Internal method uses Fedora 4 transactions to wrap up a series of
        REST operations in a single transaction.
        """
        pass



