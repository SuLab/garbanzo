# coding: utf-8

from __future__ import absolute_import

from garbanzo import lookup
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
        query_string = dict([('s', ["wd:Q133696"]),
                             ('relations', ''),
                             ('t', ''),
                             ('keywords', ''),
                             ('semanticGroups', 'LIVB'),
                             ('pageNumber', 1),
                             ('pageSize', 10)])
        response = self.client.open('/statements',
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


def test_query_statements():
    s = ["wd:Q27869338"]  # gregory stupp
    datapage = lookup.query_statements(s)
    subjects = [x['subject']['id'] for x in datapage]
    objects = [x['object']['id'] for x in datapage]
    # the item searched for should be both in objects and subjects
    assert "wd:Q27869338" in subjects and "wd:Q27869338" in objects
    # Q41949373 is a publication. it should be in the subjects only
    assert "wd:Q41949373" in subjects and "wd:Q41949373" not in objects

    s = ["wd:Q7758678"]  # night blindess
    relations = ['wd:P461']  # opposite of (has recip relation)
    datapage = lookup.query_statements(s, relations=relations)
    subjects = [x['subject']['id'] for x in datapage]
    objects = [x['object']['id'] for x in datapage]
    assert 'wd:Q7758678' in objects and 'wd:Q7758678' in subjects
    assert 'wd:Q7757581' in objects and 'wd:Q7757581' in subjects

    s = ["wd:Q7758678"]  # night blindess
    relations = ['wd:P461']  # opposite of (has recip relation)
    t = ['wd:Q7757581']
    datapage = lookup.query_statements(s, t, relations=relations)
    subjects = [x['subject']['id'] for x in datapage]
    objects = [x['object']['id'] for x in datapage]
    assert 'wd:Q7758678' in objects and 'wd:Q7758678' in subjects
    assert 'wd:Q7757581' in objects and 'wd:Q7757581' in subjects

    s = ["wd:Q7758678", "wd:Q7757581", "wd:Q550455"]
    t = ["wd:Q7758678", "wd:Q7757581"]
    datapage = lookup.query_statements(s, t)

    s = ["wd:Q7758678", "wd:Q7757581", "wd:Q550455"]
    datapage = lookup.query_statements(s)


if __name__ == '__main__':
    import unittest

    unittest.main()
