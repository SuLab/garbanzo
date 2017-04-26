"""

"""

from flask import Flask, request, jsonify
from flask_restplus import Api, Resource, fields
import requests
from itertools import chain
from utils import CurieUtil, curie_map, execute_sparql_query
from lookup import getConcept, getConcepts, get_equiv_item, getEntitiesExternalIdClaims, getEntitiesCurieClaims

app = Flask(__name__)
api = Api(app, version='1.0', title='Garbanzo API', description='A SPARQL/Wikidata Query API wrapper for Translator')
translator_ns = api.namespace('translator')
ns = api.namespace('default')

##########
# Concepts
##########

id_label = api.model("id_label", {
    'id': fields.String(required=True, description="identifier", example="wd:Q7187"),
    'label': fields.String(required=True, description="label", example="gene"),
})

concept = api.model('concept', {
    'id': fields.String(required=True, description="identifier", example="wd:Q14883734"),
    'label': fields.String(required=True, description="label", example="WRN"),
    'types': fields.List(fields.Nested(id_label), required=False, description="type of item. gotten from instance of"),
    'aliases': fields.List(fields.String(), required=False, description="list of aliases",
                           example=['RECQ3', 'Werner syndrome RecQ like helicase']),
    'description': fields.String(required=True, description="description", example="gene of the species Homo sapiens"),
})


@translator_ns.route('/concepts/<conceptId>')
@translator_ns.param('conceptId', 'Wikidata entity curie', default="wd:Q18557952")
class GetConcept(Resource):
    @api.marshal_with(concept)
    def get(self, conceptId):
        """
        Retrieves details for a specified concept in Wikidata
        """
        return getConcept(conceptId)


search_result = api.model("search_result", {
    "keywords": fields.List(fields.String(), required=True, description="keywords that were searched",
                            example=['hereditary', 'blindness']),
    "types": fields.List(fields.String(), required=False, description="constrain search by type",
                         example=["wd:Q12136"]),
    "pageNumber": fields.Integer(required=True,
                                 description="(1-based) number of the page to be returned in a paged set of query results",
                                 example=1),
    "pageSize": fields.Integer(required=True,
                               description="number of concepts per page to be returned in a paged set of query results",
                               example=10),
    #"totalEntries": fields.Integer(required=True, description="totalEntries", example=1234),
    "dataPage": fields.List(fields.Nested(concept))
})


@translator_ns.route('/concepts')
@translator_ns.param('q', 'array of keywords or substrings against which to match concept names and synonyms',
          default=['night', 'blindness'])
@translator_ns.param('types', 'constrain search by type', default=['wd:Q12136'])
@translator_ns.param('pageNumber', '(1-based) number of the page to be returned in a paged set of query results', default=1)
@translator_ns.param('pageSize', 'number of concepts per page to be returned in a paged set of query results', default=10)
class GetConcepts(Resource):
    @api.marshal_with(search_result)
    def get(self):
        """
        Retrieves a (paged) list of concepts in Wikidata
        """
        q = request.args['q']
        search = ' '.join(q.split(","))
        types = request.args.get('types', None)
        types = types.split(",") if types else []
        pageNumber = int(request.args.get('pageNumber', 1))
        pageSize = int(request.args.get('pageSize', 10))

        params = {'action': 'wbsearchentities',
                  'language': 'en',
                  'search': search,
                  'type': "item",
                  'format': 'json',
                  'limit': pageSize,
                  'continue': (pageNumber - 1) * pageSize}
        print(params)
        r = requests.get("https://www.wikidata.org/w/api.php", params=params)
        r.raise_for_status()
        d = r.json()
        print(d)
        dataPage = d['search']
        for item in dataPage:
            item['id'] = "wd:" + item['id']
            del item['repository']
            del item['concepturi']
        items = [x['id'] for x in dataPage]
        print(items)
        dataPage = list(getConcepts(tuple(items)).values())

        if types:
            dataPage = [item for item in dataPage if any(t['id'] in types for t in item['types'])]

        return {
            'pageNumber': pageNumber,
            #'totalEntries': None,
            'keywords': q.split(","),
            'pageSize': pageSize,
            'dataPage': dataPage,
            "types": types,
        }

##########
# exactmatches
##########


id_model = api.model("id_model", {
    'id': fields.String(required=True, description="identifier", example="wd:Q7758678"),
})

match_model = api.model('match_model', {
    'id': fields.String(required=True, description="identifier", example="MESH:D009755"),
    'exactmatches': fields.List(fields.Nested(id_model), required=False, description="matches"),
})


@translator_ns.route('/exactMatches/<conceptId>')
@translator_ns.param('conceptId', 'entity curie', default="MESH:D009755")
class GetConcept(Resource):
    #@api.marshal_with(concept)
    def get(self, conceptId):
        """
        Retrieves identifiers that are specified as "external-ids" with the associated input identifier
        """
        if conceptId.startswith("wd:"):
            qids = [conceptId]
        else:
            qids = get_equiv_item(conceptId)
        claims = getEntitiesCurieClaims(qids)
        return {k:[claim.to_dict() for claim in v] for k,v in claims.items()}





prop = api.model('prop', {
    'count': fields.Integer(min=0, readOnly=True, description='count', example=7),
    'property': fields.String(required=True, description='pid', example="P704"),
    'propertyDescription': fields.String(required=True, description='descr',
                                         example="transcript ID issued by Ensembl database"),
    'propertyLabel': fields.String(required=True, description='label', example="Ensembl Transcript ID")
})
map_result = api.model("map_result", {
    'itemLabel': fields.String(),
    'from_id': fields.String(),
    'to_id': fields.String(),
    'item': fields.String()
})
item_mapping_result = api.model("item_mapping_result", {
    'from_curie': fields.String(required=True, description="CURIE that was mapped from"),
    'to_curie': fields.String(required=True, description="CURIE that was mapped to"),
    'item': fields.String(required=True, description="Wikidata URI for the item that was mapped through"),
})

cu = CurieUtil(curie_map)


@ns.route('/getEquivalentWikidataItem')
@api.doc(description="Return the Wikidata item(s) for a given CURIE")
@ns.param('curie', 'Curie to search for. (e.g. PMID:1234, DOID:1432)', default="PMID:1234", required=True)
class getEquivalentWikidataItem(Resource):
    # @api.doc(description="this is more description")
    def get(self):
        """docstring"""
        curie = request.args.get("curie", "PMID:1234")
        equiv_items = get_equiv_item(curie)
        return equiv_items


def get_equivalent_class(curie, to_ns):
    """
    Given a curie (e.g. PMID:1234) and a to namespace (e.g. DOI), return the equivalent curie (E.g. DOI:10.1099/00207713-49-1-201)
    :param curie:
    :param to_ns:
    :return:
    """
    pid, value = cu.parse_curie(curie)
    prop_direct = "<http://www.wikidata.org/prop/direct/{}>".format(pid.split("/")[-1])
    to_pid = curie_map[to_ns]['pid']
    to_prop_direct = "<http://www.wikidata.org/prop/direct/{}>".format(to_pid.split("/")[-1])
    query_str = "SELECT ?item ?to_value WHERE {{ ?item {} '{}' . ?item {} ?to_value }}".format(prop_direct, value,
                                                                                               to_prop_direct)
    d = execute_sparql_query(query_str)['results']['bindings']
    results = [{k: v['value'] for k, v in x.items()} for x in d]
    for result in results:
        result['from_curie'] = curie
        # result['from_value'] = value
        result['to_curie'] = cu.make_curie(to_ns, result['to_value'])
        del result['to_value']

    return results


# get_equivalent_class('PMID:18613750', 'DOI')
# get_equivalent_class('PMID:10028264', 'DOI')

@ns.route('/getEquivalentClass')
@ns.param('curie', 'Curie to search for', default="PMID:18613750")
@ns.param('namespace', 'return the equivalentclass in this namespace', default="DOI")
@ns.param('returnReferences', '(bool) return references. NOT IMPLEMENTED', default=False)
class getEquivalentClass(Resource):
    @api.marshal_with(item_mapping_result, as_list=True)
    def get(self):
        curie = request.args.get("curie", "PMID:18613750")
        namespace = request.args.get("namespace", "DOI")
        returnReferences = request.args.get("returnReferences", False)
        equiv_class = get_equivalent_class(curie, namespace)
        if not returnReferences:
            return equiv_class


@ns.route('/searchentities', )
@ns.param('search', 'Search for this text', default="")
@ns.param('type', 'Search for this type of entity. One of the following values: item, property', default="item")
class Searchentities(Resource):
    # @ns.doc("Wrapper for Wikidata wbsearchentities API")
    def get(self):
        search = request.args.get('search', None)
        type_ = request.args.get('type', "item")
        params = {'action': 'wbsearchentities',
                  'language': 'en',
                  'search': search,
                  'type': type_,
                  'format': 'json'}
        r = requests.get("https://www.wikidata.org/w/api.php", params=params)
        r.raise_for_status()
        return r.json()


def generate_query_str(ids, from_prop, to_prop):
    query_str_template = """SELECT ?item ?itemLabel ?from_id ?to_id
    WHERE
    {{
      values ?from_id {{{s}}}
      ?item wdt:{from_prop} ?from_id .
      ?item wdt:{to_prop} ?to_id
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}"""
    return query_str_template.format(s=" ".join(map(lambda x: '"' + x + '"', ids)), from_prop=from_prop,
                                     to_prop=to_prop)


@api.route('/query')
@api.param('from_prop', 'Wikidata property PID', default="P353")
@api.param('from_ids', 'List of IDs (comma-separated)', default="CDK2,EDNRB,CHD3")
@api.param('to_prop', 'Wikidata property PID', default="P354")
class S(Resource):
    @api.marshal_with(map_result, as_list=True)
    def get(self):
        from_prop = request.args.get('from_prop', None)
        to_prop = request.args.get('to_prop', None)
        s = request.args.get('from_ids', None)

        query_str = generate_query_str(s.split(","), from_prop, to_prop)
        print(query_str)

        d = execute_sparql_query(query_str)['results']['bindings']
        d = [{k: v['value'] for k, v in x.items()} for x in d]

        return d


def generate_query_str_one_hop(ids, from_prop, related_prop, to_prop):
    query_str_template = """SELECT ?item ?itemLabel ?from ?item2Label ?to
    WHERE
    {{
      values ?from {{{s}}}
      ?item wdt:{from_prop} ?from .
      ?item wdt:{related_prop} ?item2 .
      ?item2 wdt:{to_prop} ?to
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}"""
    return query_str_template.format(s=" ".join(map(lambda x: '"' + x + '"', ids)), from_prop=from_prop,
                                     to_prop=to_prop, related_prop=related_prop)


@api.route('/query_one_hop')
@api.param('from_prop', 'Wikidata property PID', default="P351")
@api.param('from_ids', 'List of IDs (comma-separated)', default="1107,1017,1234")
@api.param('to_prop', 'Wikidata property PID', default="P352")
@api.param('related_prop', 'Wikidata property PID', default="P688")
class S(Resource):
    def get(self):
        from_prop = request.args.get('from_prop', None)
        to_prop = request.args.get('to_prop', None)
        s = request.args.get('from_ids', None)
        related_prop = request.args.get('related_prop', None)
        query_str = generate_query_str_one_hop(s.split(','), from_prop, related_prop, to_prop)
        print(query_str)
        d = execute_sparql_query(query_str)['results']['bindings']
        d = [{k: v['value'] for k, v in x.items()} for x in d]
        return d


def generate_externalid_from_items_query(qids):
    query_template = """
    # list of item props
    SELECT ?property ?propertyLabel ?propertyDescription ?count WHERE {{
        {{
            select ?propertyclaim (COUNT(*) AS ?count) where {{
                values ?item {{{s}}}
                ?item ?propertyclaim [] .
            }} group by ?propertyclaim
        }}
        ?property wikibase:propertyType wikibase:ExternalId .
        ?property wikibase:claim ?propertyclaim .
        SERVICE wikibase:label {{bd:serviceParam wikibase:language "en" .}}
    }} ORDER BY DESC (?count)
    """
    return query_template.format(s=" ".join(map(lambda x: 'wd:' + x, qids)))


@app.route('/item_externalids')
def item_externalids():
    s = request.args.get('qid', None)
    if not s:
        s = "Q15978631,Q130888,Q131065"
    query_str = generate_externalid_from_items_query(s.split(','))
    print(query_str)
    d = execute_sparql_query(query_str)['results']['bindings']
    d = [{k: v['value'] for k, v in x.items()} for x in d]
    return jsonify(d)


def generate_suggest_props_query(ids, from_prop, query_type=None):
    # assert query_type in {'wikibase:ExternalId ', 'wikibase:WikibaseItem'}
    query_template = """
        SELECT ?property ?propertyLabel ?propertyDescription ?count WHERE {{
        	{{
        		select ?propertyclaim (COUNT(*) AS ?count) where {{
        			values ?from {{{s}}}
                    ?item wdt:{from_prop} ?from .
        			?item ?propertyclaim [] .
        		}} group by ?propertyclaim
        	}}
        	?property wikibase:propertyType {qt} .
        	?property wikibase:claim ?propertyclaim .
        	SERVICE wikibase:label {{bd:serviceParam wikibase:language "en" .}}
        }} ORDER BY DESC (?count)
        """
    return query_template.format(s=" ".join(map(lambda x: '"' + x + '"', ids)), from_prop=from_prop, qt=query_type)


@api.route('/suggest_props')
@api.param('from_prop', 'Wikidata property PID', default="P353")
@api.param('from_ids', 'List of IDs (comma-separated)', default="CDK2,EDNRB,CHD3")
@api.param('prop_type', 'Property type (item or externalid)', default="externalid")
class S(Resource):
    @api.marshal_with(prop, as_list=True)
    def get(self):
        from_prop = request.args.get('from_prop', None)
        s = request.args.get('from_ids', None)
        prop_type = request.args.get("prop_type", None)
        ptmap = {"externalid": "wikibase:ExternalId",
                 "item": "wikibase:WikibaseItem"}
        query_str = generate_suggest_props_query(s.split(','), from_prop, ptmap[prop_type])
        print(query_str)
        d = execute_sparql_query(query_str)['results']['bindings']
        d = [{k: v['value'] for k, v in x.items()} for x in d]
        d = [{k: v.replace("http://www.wikidata.org/entity/", "") for k, v in x.items()} for x in d]
        return d


if __name__ == '__main__':
    app.run(host='0.0.0.0')
