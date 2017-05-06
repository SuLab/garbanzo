from itertools import chain

from flask import Flask, request, jsonify
from flask_restplus import abort
from flask_restplus import Api, Resource, fields
import requests
from utils import CurieUtil, curie_map, execute_sparql_query
from lookup import getConcept, getConcepts, get_equiv_item, getEntitiesCurieClaims, getEntities, getEntitiesClaims, \
    get_forward_items, get_reverse_items, search_wikidata

app = Flask(__name__)
api = Api(app, version='1.0', title='Garbanzo API', description='A SPARQL/Wikidata Query API wrapper for Translator',
          contact_url="https://github.com/stuppie/garbanzo", contact="gstupp")
translator_ns = api.namespace('translator')
ns = api.namespace('default')

##########
# GET /concepts/{conceptId}
##########

concept_detail = api.model("concept_detail", {
    'tag': fields.String(description="property name"),
    'value': fields.String(description="property value"),
})

concept = api.model('concept', {
    'id': fields.String(required=True, description="local object identifier for the concept", example="wd:Q14883734"),
    'name': fields.String(required=True, description="canonical human readable name of the concept (aka label)", example="WRN"),
    'semanticGroup': fields.String(required=False, description="concept semantic type"),
    'synonyms': fields.List(fields.String(), required=False, description="aka aliases",
                           example=['RECQ3', 'Werner syndrome RecQ like helicase']),
    'definition': fields.String(required=True, description="concept definition (aka description)", example="gene of the species Homo sapiens"),
    'details': fields.List(fields.Nested(concept_detail, required=False), required=False)
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

##########
# GET /concepts
##########

search_result = api.model("search_result", {
    "keywords": fields.String(required=True, description="keywords that were searched", example='night blindness'),
    "semgroups": fields.String(description="constrain search by semantic groups", example='DISO CHEM'),
    "pageNumber": fields.Integer(required=True, description="(1-based) number of the page returned", example=1, type=int),
    "pageSize": fields.Integer(required=True, description="number of concepts per page", example=10, type=int),
    # "totalEntries": fields.Integer(required=True, description="totalEntries", example=1234),
    "dataPage": fields.List(fields.Nested(concept))
})


@translator_ns.route('/concepts')
@translator_ns.param('keywords', 'space delimited set of keywords or substrings against which to match concept names and synonyms',
                     default='night blindness', required = True)
@translator_ns.param('semgroups', 'space-delimited set of semantic groups to which to constrain concepts matched by the main keyword search', default='DISO CHEM')
@translator_ns.param('pageNumber', '(1-based) number of the page to be returned in a paged set of query results',
                     default=1, type=int)
@translator_ns.param('pageSize', 'number of concepts per page to be returned in a paged set of query results',
                     default=10, type=int)
class GetConcepts(Resource):
    @api.marshal_with(search_result)
    def get(self):
        """
        Retrieves a (paged) list of concepts in Wikidata
        """
        keywords = request.args['keywords'].split(" ")
        semgroups = request.args.get('semgroups', None)
        semgroups = semgroups.split(" ") if semgroups else []
        pageNumber = int(request.args.get('pageNumber', 1))
        pageSize = int(request.args.get('pageSize', 10))
        if pageSize > 50:
            abort(message="pageSize can not be greater than 50")

        dataPage = search_wikidata(keywords, semgroups=semgroups, pageNumber=pageNumber, pageSize=pageSize)

        return {
            'pageNumber': pageNumber,
            # 'totalEntries': None,
            'keywords': request.args['keywords'],
            'pageSize': pageSize,
            'dataPage': dataPage,
            "semgroups": request.args.get('semgroups', ''),
        }


##########
# GET /exactmatches
##########

"""
evidence_model = api.model("evidence_model", {
    'id': fields.String(description="local identifier to evidence record",
                        example='Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29'),
})

id_model = api.model("id_model", {
    'id': fields.String(required=True, description="identifier", example="DOID:8499"),
    'evidence': fields.Nested(evidence_model),
})

match_model = api.model('match_model', {
    'id': fields.String(required=True, description="identifier that was searched for", example="MESH:D009755"),
    'exactmatches': fields.List(fields.Nested(id_model), required=False, description="matches"),
})
"""


@translator_ns.route('/exactMatches/')
@translator_ns.param('c', 'space-delimited set of CURIE-encoded identifiers of exactly matching concepts, '
                          'to be used in a search for additional exactly matching concepts',
                     default="MESH:D009755", required=True)
class GetConcept(Resource):
    #@api.marshal_with(match_model)
    @api.doc(
        description="""Given an input list of CURIE identifiers of known exactly matched concepts sensa-SKOS, retrieves
        the list of CURIE identifiers of additional concepts that are deemed by the given knowledge source to be exact
        matches to one or more of the input concepts. If an empty set is returned, the it can be assumed that the given
        knowledge source does not know of any new equivalent concepts to add to the input set.""")
    def get(self):
        """
        Retrieves identifiers that are specified as "external-ids" with the associated input identifiers
        """
        concepts = request.args.get("c", '')
        concepts = concepts.split(" ") if concepts else []
        input_concepts = set(concepts)
        curies = set(x for x in concepts if not x.startswith("wd:"))
        try:
            equiv_qid = {curie: get_equiv_item(curie) for curie in curies}
        except ValueError as e:
            abort(message=str(e))
            return None

        qids = set(x for x in concepts if x.startswith("wd:"))
        qids.update(set(chain(*equiv_qid.values())))

        # get all xrefs from these qids
        claims = getEntitiesCurieClaims(qids)
        claims = list(chain(*claims.values()))
        claims = [claim.to_dict() for claim in claims]
        for claim in claims:
            claim['evidence'] = {'id': claim['id']}
            claim['id'] = claim['datavaluecurie']
            del claim['datavaluecurie']
            del claim['references']

        # figure out all ids that we got, make sure the wd curie is in it, then remove the input curies
        response_ids = set(x['id'] for x in claims)
        response_ids.update(qids)
        response_ids = response_ids - input_concepts

        return list(response_ids)


##########
# statements
##########


evidence_model = api.model("evidence_model", {
    'id': fields.String(description="local identifier to evidence record",
                        example='Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29', required=True),
    # I don't know what 'count' is for
})

object_model = api.model("object_model", {
    'id': fields.String(description="CURIE-encoded local identifier", example='', required=True),
    'name': fields.String(description="human readable label of concept", example=''),
})

datapage_model = api.model("datapage_model", {
    'id': fields.String(description="local statement identifier", example='', required=True),
    'evidence': fields.Nested(evidence_model, required=True),
    'subject': fields.Nested(object_model, required=True),
    'object': fields.Nested(object_model, required=True),
    'predicate': fields.Nested(object_model, required=True),

})

response_model = api.model("response_model", {
    'keywords': fields.List(fields.String(), description="see input args", required=True),
    'semanticGroups': fields.List(fields.String(), description="see input args", required=True),
    'pageNumber': fields.Integer(required=True, description="(1-based) number of the page returned", example=1, type=int),
    "pageSize": fields.Integer(required=True, description="number of concepts per page", example=10, type=int),
    "totalEntries": fields.Integer(required=True, description="total number of concepts", example=100, type=int),
    "dataPage": fields.List(fields.Nested(datapage_model), required=True)
})



@translator_ns.route('/statements')
@translator_ns.param('emci', 'a (urlencoded) space-delimited set of CURIE-encoded identifiers of exactly matching '
                             'concepts to be used in a search for associated concept-relation statements',
                     default="wd:Q133696", required=True)
@translator_ns.param('types', 'constrain search by type', default=['wd:Q12136'])
@translator_ns.param('pageNumber', '(1-based) number of the page to be returned in a paged set of query results',
                     default=1, type=int)
@translator_ns.param('pageSize', 'number of concepts per page to be returned in a paged set of query results',
                     default=10, type=int)
@translator_ns.param('keywords', 'a (urlencoded) space delimited set of keywords or substrings against which to apply '
                                 'against the subject, predicate or object names of the set of concept-relations matched '
                                 'by any of the input exact matching concepts')
class GetStatements(Resource):
    @api.marshal_with(response_model)
    @api.doc(
        description="Given an input CURIE, retrieves the list of CURIE identifiers of additional concepts that are deemed to be exact matches. "
                    "This new list of concept identifiers is returned with the full list of any additional identifiers deemed by the KS to also be "
                    "identifying exactly matched concepts.")
    def get(self):
        """
        Get statements
        """
        qids = request.args['emci']
        qids = tuple([x.strip().replace("wd:", "") for x in qids.split()])
        items = get_forward_items(qids) + get_reverse_items(qids)

        datapage = [{'id': item['id'],
                     'subject': {'id': item['item'], 'name': item['itemLabel']},
                     'predicate': {'id': item['property'], 'name': item['propertyLabel']},
                     'object': {'id': item['value'], 'name': item['valueLabel']},
                     'evidence': {'id': item['id']}
                     } for item in items]



        return {'keywords': [], 'semanticGroups': [], 'dataPage': datapage}






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
