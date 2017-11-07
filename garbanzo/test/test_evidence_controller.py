# coding: utf-8

from __future__ import absolute_import

from garbanzo.models.annotation import Annotation
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestEvidenceController(BaseTestCase):
    """ EvidenceController integration test stubs """

    def test_get_evidence(self):
        """
        Test case for get_evidence

        
        """
        query_string = [('keywords', ''),
                        ('pageNumber', 1),
                        ('pageSize', 5)]
        response = self.client.open('/evidence/{statementId}'.format(statementId='wds:Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29'),
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
