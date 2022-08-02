import os
import metricbeat
import unittest
from nose.plugins.skip import SkipTest
import urllib2
import json


class Test(metricbeat.BaseTest):

    COMPOSE_SERVICES = ['elasticsearch', 'kibana']
    COMPOSE_TIMEOUT = 600

    @unittest.skipUnless(metricbeat.INTEGRATION_TESTS, "integration test")
    def test_status(self):
        """
        kibana status metricset test
        """
        # FIXME: Need to skip conditionally for Kibana versions < 6.4.0 (see commented out
        # code below)
        raise SkipTest

    def get_hosts(self):
        return [os.getenv('KIBANA_HOST', 'localhost') + ':' +
                os.getenv('KIBANA_PORT', '5601')]

    def get_version(self):
        host = self.get_hosts()[0]
        res = urllib2.urlopen(f"{host}/api/status").read()

        body = json.loads(res)
        return body["version"]["number"]
