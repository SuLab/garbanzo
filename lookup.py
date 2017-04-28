from itertools import chain
from pprint import pprint

from cachetools import cached, TTLCache
import requests

from utils import prop_curie, CurieUtil, curie_map, Typer, relationship_map, execute_sparql_query

cu = CurieUtil(curie_map)
CACHE_SIZE = 99999
CACHE_TIMEOUT_SEC = 300  # 5 min

# a claim looks like this
example_claim = {'datatype': 'external-id',
                 'datavalue': '368.6',
                 'datavaluetype': 'string',
                 'id': 'q7757581$F9DF6AB9-80BC-45A4-9CF8-6D39274EF7F3',
                 'property': 'P493',
                 'rank': 'normal',
                 'references': [[{'datatype': 'wikibase-item',
                                  'datavalue': 'Q328',
                                  'datavaluetype': 'wikibase-entityid',
                                  'property': 'P143'}]]}


class Claim:
    def __init__(self, id=None, datatype=None, rank=None, property=None, datavalue=None, datavaluetype=None,
                 references=None, qualifiers=None):
        self.datatype = datatype
        self.datavalue = datavalue
        self.datavaluetype = datavaluetype
        self.id = id
        self.property = property
        self.rank = rank
        self.references = references
        self.qualifiers = qualifiers
        self.datavaluecurie = None

    def to_dict(self):
        d = {'datatype': self.datatype,
             'datavalue': self.datavalue,
             'datavaluetype': self.datavaluetype,
             'property': self.property,
             'id': self.id,
             'rank': self.rank,
             'references': [[ref.to_dict() for ref in refblock] for refblock in
                            self.references] if self.references else None,
             'qualifiers': [qual.to_dict() for qual in self.qualifiers] if self.qualifiers else None,
             'datavaluecurie': self.datavaluecurie
             }
        d = {k: v for k, v in d.items() if v is not None}
        return d

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return self.__repr__()

    def to_curie(self):
        prop = self.property
        value = self.datavalue
        if 'http://www.wikidata.org/prop/' + prop in prop_curie:
            return cu.make_curie(prop_curie['http://www.wikidata.org/prop/' + prop], value)
        else:
            return None


def parse_snak(snak):
    claim = Claim(datatype=snak['datatype'], property=snak['property'])
    claim.datavaluetype = snak['datavalue']['type']
    if snak['datavalue']['type'] == 'string':
        claim.datavalue = snak['datavalue']['value']
    elif snak['datavalue']['type'] == 'wikibase-entityid':
        claim.datavalue = snak['datavalue']['value']['id']
    elif snak['datavalue']['type'] == 'time':
        claim.datavalue = snak['datavalue']['value']['time']
    else:
        raise ValueError(snak['datavalue'])

    return claim


def parse_claims(wdclaims):
    wdclaims = list(chain(*wdclaims.values()))
    claims = []
    for wdclaim in wdclaims:
        claim = parse_snak(wdclaim['mainsnak'])
        claim.id = wdclaim['id']
        claim.rank = wdclaim['rank']
        if 'references' in wdclaim:
            wdclaim['references'] = [list(chain(*refblock["snaks"].values())) for refblock in wdclaim['references']]
            claim.references = [[parse_snak(snak) for snak in refblock] for refblock in wdclaim['references']]
        if 'qualifiers' in wdclaim:
            wdclaim['qualifiers'] = list(chain(*wdclaim['qualifiers'].values()))
            claim.qualifiers = [parse_snak(snak) for snak in wdclaim['qualifiers']]
        claims.append(claim)
    return claims


def add_prop_uri(claims):
    for claim in claims:
        prop_uri = 'http://www.wikidata.org/prop/' + claim['property']
        if prop_uri in relationship_map:
            claim['property_uri'] = relationship_map[prop_uri]
    return claims


def getEntities(qids):
    qids = {qid.replace("wd:", "") if qid.startswith("wd:") else qid for qid in qids}
    assert all(qid.startswith("Q") for qid in qids), "All QIDs must start with 'Q'"
    params = {'action': 'wbgetentities', 'ids': "|".join(qids), 'languages': 'en', 'format': 'json'}
    r = requests.get("https://www.wikidata.org/w/api.php", params=params)
    print(r.url)
    r.raise_for_status()
    response_json = r.json()
    if 'error' in response_json:
        raise ValueError(response_json)
    entities = response_json['entities']
    return entities


def getEntitiesClaims(qids):
    """
    # qid = 'Q14911732'
    # qid = 'Q18557952'

    """
    entities = getEntities(qids)
    allclaims = {}
    for qid, entity in entities.items():
        allclaims[qid] = parse_claims(entity['claims'])

    return allclaims


def getEntitiesExternalIdClaims(qids):
    allclaims = getEntitiesClaims(qids)
    externalidclaims = {qid: [claim for claim in claims if claim.datatype == 'external-id'] for qid, claims in
                        allclaims.items()}
    for qid, claims in externalidclaims.items():
        for claim in claims:
            claim.datavaluecurie = claim.to_curie()

    return externalidclaims


def getEntitiesCurieClaims(qids):
    externalidclaims = getEntitiesExternalIdClaims(qids)
    for qid in externalidclaims:
        externalidclaims[qid] = [claim for claim in externalidclaims[qid] if claim.datavaluecurie]
        for claim in externalidclaims[qid]:
            claim.property = None
            claim.datavalue = None
            claim.datavaluetype = None
            claim.datatype = None

    return externalidclaims


def get_types(claims):
    typer = Typer()
    instances = set()
    for claim in claims:
        if claim['property'] == 'P31':
            instances.add(claim['datavalue'])
    types = [typer.get_type(x) for x in instances if typer.get_type(x)]
    return types


@cached(TTLCache(CACHE_SIZE, CACHE_TIMEOUT_SEC))
def getConceptLabel(qid):
    return getConceptLabels((qid,))[qid]


@cached(TTLCache(CACHE_SIZE, CACHE_TIMEOUT_SEC))
def getConceptLabels(qids):
    qids = "|".join({qid.replace("wd:", "") if qid.startswith("wd:") else qid for qid in qids})
    params = {'action': 'wbgetentities', 'ids': qids, 'languages': 'en', 'format': 'json', 'props': 'labels'}
    r = requests.get("https://www.wikidata.org/w/api.php", params=params)
    print(r.url)
    r.raise_for_status()
    wd = r.json()['entities']
    return {k: v['labels']['en']['value'] for k, v in wd.items()}


def getConcept(qid):
    return getConcepts((qid,))[qid]


@cached(TTLCache(10000, 300))  # expire after 5 min
def getConcepts(qids):
    entities = getEntities(qids)

    dd = dict()
    for qid, wd in entities.items():
        d = dict()
        d['id'] = 'wd:{}'.format(wd['id'])
        d['label'] = wd['labels']['en']['value'] if 'en' in wd['labels'] else ''
        d['description'] = wd['descriptions']['en']['value'] if 'en' in wd['descriptions'] else ''
        d['aliases'] = [x['value'] for x in wd['aliases']['en']] if 'aliases' in wd and 'en' in wd['aliases'] else []
        if 'P31' in wd['claims']:
            instances = [x['mainsnak']['datavalue']['value']['id'] for x in wd['claims']['P31']]
            d['types'] = [{'id': "wd:" + instance_qid} for instance_qid in instances]
        else:
            d['types'] = []
        dd["wd:" + qid] = d

    # add labels to the types. Do it in one API call
    types = set()
    for value in dd.values():
        if 'types' in value and value['types']:
            types.update({x['id'] for x in value['types']})
    if types:
        typed = getConceptLabels(tuple(types))
        for value in dd.values():
            if 'types' in value and value['types']:
                value['types'] = [{'id': x['id'], 'label': typed[x['id'].replace("wd:", "")]} for x in value['types']]
    return dd


@cached(TTLCache(CACHE_SIZE, CACHE_TIMEOUT_SEC))
def get_equiv_item(curie):
    """
    From a curie, get the wikidata item
    get_equiv_item("PMID:10028264")
    :param curie:
    :return:
    """
    pid, value = cu.parse_curie(curie)
    prop_direct = "<http://www.wikidata.org/prop/direct/{}>".format(pid.split("/")[-1])
    query_str = "SELECT ?item WHERE {{ ?item {} '{}' }}".format(prop_direct, value)
    d = execute_sparql_query(query_str)['results']['bindings']
    equiv_qids = list(set(chain(*[{v['value'] for k, v in x.items()} for x in d])))
    equiv_qids = ["wd:" + x.replace("http://www.wikidata.org/entity/", "") for x in equiv_qids]
    return equiv_qids


"""
Turn a list of claims into triple format:


"""
example_claim = {'id': 'Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29',
                 'rank': 'normal',
                 'property': 'P279',
                 'datavalue': 'Q550455',
                 'datavaluetype': 'wikibase-entityid',
                 'references': [[
                     {
                         'datavalue': 'Q28556593',
                         'datavaluetype': 'wikibase-entityid',
                         'property': 'P248',
                         'datatype': 'wikibase-item'},
                     {
                         'datavalue': '+2017-01-31T00:00:00Z',
                         'datavaluetype': 'time',
                         'property': 'P813',
                         'datatype': 'time'},
                     {
                         'datavalue': 'DOID:8499',
                         'datavaluetype': 'string',
                         'property': 'P699',
                         'datatype': 'external-id'}]],
                 'datatype': 'wikibase-item'}

example_triple = {"source": "wikidata",
                  "id": "Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29",
                  "subject": {"id": "wd:Q7758678",
                              "name": "night blindness"},
                  "predicate": {"id": "wd:P279",
                                "name": "subclass of",
                                "equivalentProperty": ["http://www.w3.org/2000/01/rdf-schema#subClassOf"]},
                  "object": {"id": "wd:Q550455",
                             "name": "retinal disease"},
                  "evidence": [
                      {
                          'value': {'id': 'wd:Q28556593', 'name': 'Disease Ontology release 2017-01-27'},
                          'predicate': {'id': 'wd:P248', 'name': 'stated in', 'equivalentProperty': []}
                      },
                      {
                          'value': {'datavalue': '+2017-01-31T00:00:00Z', 'datavaluetype': 'time'},
                          'predicate': {'id': 'wd:P813', 'name': 'retrieved', 'equivalentProperty': []}
                      },
                      {
                          'value': {'datavalue': 'DOID:8499', 'datavaluetype': 'string'},
                          'predicate': {'id': 'wd:P699', 'name': 'Disease Ontology ID', 'equivalentProperty':
                              ['http://identifiers.org/doid/', 'http://purl.obolibrary.org/obo/DOID']}
                      },
                  ]
                  }
