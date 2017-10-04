"""
These are live tests, hitting the production wikidata.
"""

import json

from app import app

client = app.test_client()


def test_get_concept():
    r = client.get("/concepts/wd:Q27869338")
    result = json.loads(r.data.decode('utf8'))
    assert len(result) == 1
    d = result[0]
    assert d['id'] == 'wd:Q27869338'
    assert d['semanticGroup'] == 'LIVB'
    assert len(d['details']) > 1


def test_get_concepts():
    r = client.get("/concepts/?semgroups=DISO%20CHEM&pageSize=10&keywords=night%20blindness&pageNumber=1")
    d = json.loads(r.data.decode('utf8'))
    items = [x for x in d if x['id'] == 'wd:Q7758678']
    assert len(items) == 1


def test_exact_match():
    r = client.get("/exactmatches/MESH%3AD009755")
    d = json.loads(r.data.decode('utf8'))
    assert all(x in d for x in ['wd:Q7758678', 'UMLS:C0028077', 'ICD10CM:H53.60', 'DOID:8499', 'ICD10CM:H53.6']), d


def test_evidence():
    r = client.get("/evidence/Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29")
    result = json.loads(r.data.decode('utf8'))
    assert len(result) == 1
    d = result[0]
    assert d['id'] == 'wds:Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29'
    assert d['evidence'] == 'https://www.wikidata.org/wiki/Q7758678#P279'


def test_bad_curie():
    r = client.get("/exactmatches/GREG%3AD009755")
    d = json.loads(r.data.decode('utf8'))
    assert len(d) == 0
