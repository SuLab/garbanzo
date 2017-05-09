"""
# curie to wd map
# monarch: https://github.com/monarch-initiative/dipper/blob/master/dipper/curie_map.yaml
# 'NCBITaxon' : 'http://purl.obolibrary.org/obo/NCBITaxon_'

provenence map: https://github.com/monarch-initiative/dipper/blob/master/dipper/models/Provenance.py

"""
import requests


def always_curie(s):
    assert s.startswith("Q") or s.startswith("wd:")
    return "wd:" + s if s.startswith("Q") else s

def always_qid(s):
    assert s.startswith("Q") or s.startswith("wd:")
    return s.replace("wd:", "") if s.startswith("wd:") else s

# if an item is "instance of" this item, this is its type
# https://metamap.nlm.nih.gov/Docs/SemGroups_2013.txt
# For futrue reference : https://github.com/monarch-initiative/SciGraph-docker-monarch-data/blob/master/src/main/resources/monarchLoadConfiguration.yaml.tmpl#L74
class Typer:
    qid_type = {
        # disease
        'Q12136': 'DISO',
        # gene
        'Q7187': 'GENE',
        # protein
        #'http://www.wikidata.org/entity/Q8054': '',
        # chromosome
        #'http://www.wikidata.org/entity/Q37748': '',
        # chemical compound
        'Q11173': 'CHEM',
        # pharmaceutical drug
        'Q12140': 'CHEM',
        # protein family
        #'http://www.wikidata.org/entity/Q417841': '',
        # protein domain
        #'http://www.wikidata.org/entity/Q898273': '',
        # human
        'Q5': 'LIVB',
        # BP
        'Q2996394': 'PHYS',
        # MF
        'Q14860489': 'PHYS',
        # CC
        'Q5058355': 'PHYS',
        }

    def get_type(self, qid):
        return self.qid_type.get(qid)

### not used for anything
"""
relationship_map = {'http://www.wikidata.org/prop/P2176': {'name': 'drug used for treatment',
                                                           'uri': 'RO:0002302'},
                    'http://www.wikidata.org/prop/P248': {'name': 'stated in',
                                                           'uri': 'oban:has_source'},
                    }
"""

curie_map = {
    # formatter: curie value to wikidata value
    # default formatter: '{}'
    # reverse_formatter: wikidata value to curie value
    # default reverse_formatter: '{}'
    # can be a string or function that gets applied to the string
    'NCBITaxon': {
        'uri': 'http://purl.obolibrary.org/obo/NCBITaxon_',
        'pid': 'http://www.wikidata.org/prop/P685',
        'formatter': '{}'
    },
    'NCBIGene': {
        'uri': 'http://www.ncbi.nlm.nih.gov/gene/',
        'pid': 'http://www.wikidata.org/prop/P351',
    },
    'UniProtKB': {
        'uri': 'http://identifiers.org/uniprot/',
        'pid': 'http://www.wikidata.org/prop/P352',
    },
    'HGNCS': {  # hgnc symbol
        'uri': 'http://identifiers.org/hgnc.symbol/',
        'pid': 'http://www.wikidata.org/prop/P353',
    },
    'HGNC': {  # hgnc id
        'uri': 'http://identifiers.org/hgnc/',
        'pid': 'http://www.wikidata.org/prop/P354',
    },
    'DOID': {
        'uri': 'http://purl.obolibrary.org/obo/DOID_',
        'pid': 'http://www.wikidata.org/prop/P699',
        'formatter': 'DOID:{}',
        'reverse_formatter': lambda s: s.replace("DOID:", "")
    },
    'OMIM': {
        'uri': 'http://purl.obolibrary.org/obo/OMIM_',
        'pid': 'http://www.wikidata.org/prop/P492'
    },
    'MESH': {
        'uri': 'http://purl.obolibrary.org/obo/MESH_',
        'pid': 'http://www.wikidata.org/prop/P486'
    },
    'UMLS': {
        'uri': 'http://purl.obolibrary.org/obo/UMLS_',
        'pid': 'http://www.wikidata.org/prop/P2892'
    },
    'ECO': {
        'uri': 'http://purl.obolibrary.org/obo/ECO_',
        'pid': 'http://www.wikidata.org/prop/P3811',
        'formatter': 'ECO:{}',
        'reverse_formatter': lambda s: s.replace("ECO:", "")
    },
    'PMID': {
        'uri': 'http://www.ncbi.nlm.nih.gov/pubmed/',
        'pid': 'http://www.wikidata.org/prop/P698',
    },
    'DOI': {
        'uri': 'http://dx.doi.org/',
        'pid': 'http://www.wikidata.org/prop/P356',
    },
    'CHEBI': {
        'uri': 'http://purl.obolibrary.org/obo/CHEBI_',
        'pid': 'http://www.wikidata.org/prop/P683',
    },
    'DrugBank': {
        'uri': 'http://www.drugbank.ca/drugs/',
        'pid': 'http://www.wikidata.org/prop/P715',
    },
    'RXCUI': {
        'uri': 'http://purl.bioontology.org/ontology/RXNORM/',
        'pid': 'http://www.wikidata.org/prop/P3345',
    },
    'UNII': {
        'uri': 'http://fdasis.nlm.nih.gov/srs/unii/',
        'pid': 'http://www.wikidata.org/prop/P652',
    },
    # not in monarch
    'CAS': {
        'uri': 'http://identifiers.org/cas/',
        'pid': 'http://www.wikidata.org/prop/P231',
    },
    'ChEMBL': {
        'uri': 'http://identifiers.org/chembl.compound/',
        'pid': 'http://www.wikidata.org/prop/P592',
        'formatter': "{}",
        'reverse_formatter': lambda s: s.replace("CHEMBL", ''),
    },
    'ICD9': {
        'uri': '',
        'pid': 'http://www.wikidata.org/prop/P493',
    },
    'ICD10': {
        'uri': '',
        'pid': 'http://www.wikidata.org/prop/P494',
    },
    'wd': {
        'uri': 'http://www.wikidata.org/entity/',
        'pid': 'http://www.wikidata.org/entity/',
    }
}
prop_curie = {v['pid']: k for k, v in curie_map.items()}


class CurieUtil(object):
    """

    """

    def __init__(self, curie_map):
        for k, v in curie_map.items():
            if 'formatter' not in v:
                v['formatter'] = '{}'
            if 'reverse_formatter' not in v:
                v['reverse_formatter'] = '{}'
            if not (isinstance(v['formatter'], str) or hasattr(v['formatter'], '__call__')):
                raise ValueError(v['formatter'])
            if not (isinstance(v['reverse_formatter'], str) or hasattr(v['reverse_formatter'], '__call__')):
                raise ValueError(v['reverse_formatter'])
        self.curie_map = curie_map

    def parse_curie(self, curie: str):
        """
        Given a curie (e.g. CHEBI:1234), return the wikidata property and formatted value
        :param curie:
        :return:
        """
        if curie.count(':') != 1:
            raise ValueError("There must be one ':' in the curie: {}".format(curie))
        ns, value = curie.split(':')
        if ns not in self.curie_map:
            raise ValueError("Unknown namespace: {}".format(ns))
        cm = self.curie_map[ns]

        wikidata_value = None
        if isinstance(cm['formatter'], str):
            wikidata_value = cm['formatter'].format(value)
        elif hasattr(cm['formatter'], '__call__'):
            wikidata_value = cm['formatter'](value)
        return cm['pid'], wikidata_value

    def make_curie(self, ns: str, value: str):
        """
        Given a namespace(e.g. DOID) and a value (e.g. DOID:1234, this value comes from wikidata!!), return the curie
        :param ns:
        :param value:
        :return:

        print(cu.make_curie("DOID", "DOID:1234"))
        print(cu.make_curie("PMID", "1234"))
        """
        if ns not in self.curie_map:
            raise ValueError("Unknown namespace: {}".format(ns))
        cm = self.curie_map[ns]

        curie_value = None
        if isinstance(cm['reverse_formatter'], str):
            curie_value = cm['reverse_formatter'].format(value)
        elif hasattr(cm['reverse_formatter'], '__call__'):
            curie_value = cm['reverse_formatter'](value)
        return ns + ':' + curie_value

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
