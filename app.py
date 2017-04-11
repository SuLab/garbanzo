"""

# start with entrez ids, get direct xrefs
http://localhost:5000/suggest_item_externalids?from_prop=P351&from_ids=3949,59340,181,472

# start with entrez ids, get related items
http://localhost:5000/suggest_item_props?from_prop=P351&from_ids=3949,59340,181,472


# one hop
http://localhost:5000/query_one_hop?from_prop=P351&to_prop=P352&from_ids=1107,1017,12345,123&related_prop=P688

"""

from flask import Flask, request, jsonify
from flask_restplus import Api, Resource, fields, reqparse

import requests
from itertools import chain

from utils import CurieUtil, curie_map, execute_sparql_query


from utils import execute_sparql_query

app = Flask(__name__)
api = Api(app, version='1.0', title='Translatizer API', description='A simple API')
ns = api.namespace('wikidata')

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

cu = CurieUtil(curie_map)

def get_equiv_item(curie):
    """
    From a curie, get the wikidata item
    # this one has two wikidata id because someone fucked up
    get_equiv_item("PMID:10028264")
    :param curie:
    :return:
    """
    pid, value = cu.parse_curie(curie)
    prop_direct = "<http://www.wikidata.org/prop/direct/{}>".format(pid.split("/")[-1])
    query_str = "SELECT ?item WHERE {{ ?item {} '{}' }}".format(prop_direct, value)
    d = execute_sparql_query(query_str)['results']['bindings']
    equiv_qids = list(set(chain(*[{v['value'] for k, v in x.items()} for x in d])))
    return {curie: equiv_qids}


@ns.route('/getEquivalentWikidataItem')
@ns.param('curie', 'Curie to search for', default="PMID:1234")
@ns.param('returnReferences', '(bool) return references. Requires an extra query. NOT IMPLEMENTED', default=False)
class getEquivalentWikidataItem(Resource):
    def get(self):
        curie = request.args.get("curie", "PMID:1234")
        returnReferences = request.args.get("returnReferences", False)
        equiv_items = get_equiv_item(curie)
        if not returnReferences:
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
    query_str = "SELECT ?item ?to_value WHERE {{ ?item {} '{}' . ?item {} ?to_value }}".format(prop_direct, value, to_prop_direct)
    d = execute_sparql_query(query_str)['results']['bindings']
    results = [{k: v['value'] for k, v in x.items()} for x in d]
    for result in results:
        result['from_curie'] = curie
        #result['from_value'] = value
        result['to_curie'] = cu.make_curie(to_ns, result['to_value'])
        del result['to_value']

    return results

#get_equivalent_class('PMID:18613750', 'DOI')
#get_equivalent_class('PMID:10028264', 'DOI')

@ns.route('/getEquivalentClass')
@ns.param('curie', 'Curie to search for', default="PMID:18613750")
@ns.param('namespace', 'return the equivalentclass in this namespace', default="DOI")
@ns.param('returnReferences', '(bool) return references. NOT IMPLEMENTED', default=False)
class getEquivalentClass(Resource):
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
    #@ns.doc("Wrapper for Wikidata wbsearchentities API")
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


#@ns.route('/getConceptExternalIds', )



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
    #assert query_type in {'wikibase:ExternalId ', 'wikibase:WikibaseItem'}
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
