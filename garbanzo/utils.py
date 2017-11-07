"""
# curie to wd map
# monarch: https://github.com/monarch-initiative/dipper/blob/master/dipper/curie_map.yaml
# 'NCBITaxon' : 'http://purl.obolibrary.org/obo/NCBITaxon_'

provenence map: https://github.com/monarch-initiative/dipper/blob/master/dipper/models/Provenance.py

"""
from collections import defaultdict
from itertools import chain

import requests


def alwayslist(value):
    """If input value if not a list/tuple type, return it as a single value list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return value
    else:
        return [value]


def always_curie(s):
    assert s.startswith("Q") or s.startswith("wd:")
    return "wd:" + s if s.startswith("Q") else s


def always_qid(s):
    assert s.startswith("Q") or s.startswith("wd:"), s
    return s.replace("wd:", "") if s.startswith("wd:") else s

# For future reference : https://github.com/monarch-initiative/SciGraph-docker-monarch-data/blob/master/src/main/resources/monarchLoadConfiguration.yaml.tmpl#L74

# An item's type is the list of item it is an 'instance of', which can be anything
# these are the types we care about:
# supporting both "wikidata" types and semgroups (https://metamap.nlm.nih.gov/Docs/SemGroups_2013.txt)

qid_label = {
    'Q12136': 'disease',
    'Q7187': 'gene',
    'Q8054': 'protein',
    'Q37748': 'chromosome',
    'Q11173': 'chemical_compound',
    'Q12140': 'pharmaceutical_drug',
    'Q417841': 'protein_family',
    'Q898273': 'protein_domain',
    'Q5': 'human',
    'Q2996394': 'biological_process',
    'Q14860489': 'molecular_function',
    'Q5058355': 'cellular_component',
}
label_qid = {v:k for k,v in qid_label.items()}

qid_semgroup = {
    'Q12136': ['DISO'],
    'Q7187': ['GENE'],
    'Q8054': ['GENE', 'CHEM'],
    'Q11173': ['CHEM'],
    'Q12140': ['CHEM'],
    'Q5': ['LIVB']
}

type_qid = defaultdict(set)
for k,vs in qid_semgroup.items():
    vs = alwayslist(vs)
    for v in vs:
        type_qid[v].add(k)

def get_types_from_qids(qids):
    qids = map(always_qid, qids)
    semgroups = list(set(chain(*[qid_semgroup[x] for x in qids if x in qid_semgroup])))
    return semgroups


def get_qids_from_types(types):
    qids = list(map(always_qid, set(chain(*[type_qid[x] for x in types if x in type_qid]))))
    return qids


def execute_sparql_query(query, prefix=None, endpoint='https://query.wikidata.org/sparql',
                         user_agent='tmp: github.com/SuLab/tmp'):
    wd_standard_prefix = '''
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX v: <http://www.wikidata.org/prop/statement/>
        PREFIX q: <http://www.wikidata.org/prop/qualifier/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    '''
    if not prefix:
        prefix = wd_standard_prefix
    params = {'query': prefix + '\n' + query,
              'format': 'json'}
    headers = {'Accept': 'application/sparql-results+json',
               'User-Agent': user_agent}
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
