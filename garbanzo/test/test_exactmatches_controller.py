# coding: utf-8

from __future__ import absolute_import

from . import BaseTestCase
from six import BytesIO
from flask import json


class TestExactmatchesController(BaseTestCase):
    """ ExactmatchesController integration test stubs """

    def test_get_exact_matches_to_concept(self):
        """
        Test case for get_exact_matches_to_concept

        
        """
        response = self.client.open('/exactmatches/{conceptId}'.format(conceptId='MESH:D009755'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_get_exact_matches_to_concept_list(self):
        """
        Test case for get_exact_matches_to_concept_list

        
        """
        query_string = {'c': ['MESH:D009755', 'wd:Q14883734']}
        response = self.client.open('/exactmatches',
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_get_exact_match_curie(self):
        response = self.client.open('/exactmatches/{conceptId}'.format(conceptId='DOID:1234'),
                                    method='GET')
        d = json.loads(response.data.decode('utf-8'))
        assert "wd:Q1049021" in d
        assert 'MESH:D000068116' in d
        assert 'DOID:1234' in d

    def test_get_exact_match_wd(self):
        response = self.client.open('/exactmatches/{conceptId}'.format(conceptId='wd:Q1049021'),
                                    method='GET')
        d = json.loads(response.data.decode('utf-8'))
        assert "wd:Q1049021" in d
        assert 'MESH:D000068116' in d
        assert 'DOID:1234' in d

    def test_get_exact_matches_to_concept_list_1(self):
        query_string = {'c': ["DOID:1234", "MESH:1234", "wd:Q1049021"]}
        response = self.client.open('/exactmatches',
                                    method='GET',
                                    query_string=query_string)
        d = json.loads(response.data.decode('utf-8'))
        print(d)
        assert all(x in d for x in {"DOID:1234", "wd:Q1049021", "MESH:D000068116"})
        assert "MESH:1234" not in d


if __name__ == '__main__':
    import unittest

    unittest.main()
