# coding: utf-8

from __future__ import absolute_import

from garbanzo.models.predicate import Predicate
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestPredicatesController(BaseTestCase):
    """ PredicatesController integration test stubs """

    def test_get_predicates(self):
        """
        Test case for get_predicates

        
        """
        response = self.client.open('/predicates',
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
