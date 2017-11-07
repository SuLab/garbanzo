# coding: utf-8

from __future__ import absolute_import

from garbanzo.models.concept import Concept
from garbanzo.models.concept_with_details import ConceptWithDetails
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestConceptsController(BaseTestCase):
    """ ConceptsController integration test stubs """

    def test_get_concept_details(self):
        """
        Test case for get_concept_details

        
        """
        response = self.client.open('/concepts/{conceptId}'.format(conceptId='wd:Q18557952'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_get_concepts(self):
        """
        Test case for get_concepts

        
        """
        query_string = [('keywords', 'night blindness'),
                        ('semanticGroups', 'DISO CHEM'),
                        ('pageNumber', 1),
                        ('pageSize', 10)]
        response = self.client.open('/concepts',
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
