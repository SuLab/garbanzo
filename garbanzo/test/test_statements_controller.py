# coding: utf-8

from __future__ import absolute_import

from garbanzo.models.statement import Statement
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestStatementsController(BaseTestCase):
    """ StatementsController integration test stubs """

    def test_get_statements(self):
        """
        Test case for get_statements

        
        """
        query_string = [('s', ["wd:Q133696"]),
                        ('relations', ''),
                        ('t', ''),
                        ('keywords', ''),
                        ('semanticGroups', 'LIVB'),
                        ('pageNumber', 1),
                        ('pageSize', 10)]
        response = self.client.open('/statements',
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
