from itertools import chain

import requests
from flask import Flask, request, jsonify
from flask_restplus import abort, Api, Resource, fields

from lookup import getConcept, get_equiv_item, getEntitiesCurieClaims, get_forward_items, get_reverse_items, \
    search_wikidata, get_concept_details, get_all_types

app = Flask(__name__)

try:
    app.config.from_object('local')
except ImportError:
    print("failed importing local settings")

description = """A SPARQL/Wikidata Query API wrapper for Translator

Implements a Knowedge Beacon for the Translator Knowledge Beacon API
(http://beacon.medgeninformatics.net/api/swagger-ui.html) version 1.0.11

"""
api = Api(app, version='1.0.112', title='Garbanzo API', description=description,
          contact_url="https://github.com/stuppie/garbanzo", contact="gstupp", contact_email="gstupp@scripps.edu")
concepts_ns = api.namespace('concepts', "Queries for concepts")
exactmatches_ns = api.namespace('exactmatches', "Queries for exactly matching concepts")
statements_ns = api.namespace('statements', "Queries for concept-relationship statements")
evidence_ns = api.namespace('evidence', "Queries for references cited as evidence for statements")
types_ns = api.namespace('types', "Summary statistics about the knowledge source")


@app.route("/swagger_smartapi.json")
def get_modified_swagger():
    d = api.__schema__
    d['info']['contact']['responsibleOrganization'] = 'TSRI'
    d['info']['contact']['responsibleDeveloper'] = 'Greg Stupp'
    return jsonify(d)


##########
# GET /concepts/{conceptId}
##########

concept_detail = api.model("concept_detail", {
    'tag': fields.String(description="property name"),
    'value': fields.String(description="property value"),
})

concept_model = api.model('concept_model', {
    'id': fields.String(required=True, description="local object identifier for the concept", example="wd:Q14883734"),
    'name': fields.String(required=True, description="canonical human readable name of the concept (aka label)",
                          example="WRN"),
    'semanticGroup': fields.String(required=False, description="concept semantic type"),
    'synonyms': fields.List(fields.String(), required=False, description="aka aliases",
                            example=['RECQ3', 'Werner syndrome RecQ like helicase']),
    'definition': fields.String(required=True, description="concept definition (aka description)",
                                example="gene of the species Homo sapiens"),
    'details': fields.List(fields.Nested(concept_detail, required=False), required=False)
})

concepts_model = api.model('concepts_model', {
    'id': fields.String(required=True, description="local object identifier for the concept", example="wd:Q14883734"),
    'name': fields.String(required=True, description="canonical human readable name of the concept (aka label)",
                          example="WRN"),
    'semanticGroup': fields.String(required=False, description="concept semantic type"),
    'synonyms': fields.List(fields.String(), required=False, description="aka aliases",
                            example=['RECQ3', 'Werner syndrome RecQ like helicase']),
    'definition': fields.String(required=True, description="concept definition (aka description)",
                                example="gene of the species Homo sapiens"),
})


@concepts_ns.route('/<conceptId>')
@concepts_ns.param('conceptId', 'Wikidata entity curie', default="wd:Q18557952")
class GetConcept(Resource):
    @api.marshal_with(concept_model)
    def get(self, conceptId):
        """
        Retrieves details for a specified concept in Wikidata
        """
        concept = getConcept(conceptId)
        details = get_concept_details(conceptId)
        concept['details'] = details
        return [concept]


##########
# GET /concepts
##########

@concepts_ns.route('/')
@concepts_ns.param('keywords',
                   'space delimited set of keywords or substrings against which to match concept names and synonyms',
                   default='night blindness', required=True)
@concepts_ns.param('semgroups',
                   'space-delimited set of semantic groups to which to constrain concepts matched by the main keyword search',
                   default='DISO CHEM')
@concepts_ns.param('pageNumber', '(1-based) number of the page to be returned in a paged set of query results',
                   default=1, type=int)
@concepts_ns.param('pageSize', 'number of concepts per page to be returned in a paged set of query results',
                   default=10, type=int)
class GetConcepts(Resource):
    @api.marshal_with(concepts_model)
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

        return dataPage


##########
# GET /types
##########
@types_ns.route('')
class GetTypes(Resource):
    # @api.marshal_with(types)
    def get(self):
        return get_all_types('g')


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


@exactmatches_ns.route('/')
@exactmatches_ns.param('c', 'space-delimited set of CURIE-encoded identifiers of exactly matching concepts, '
                            'to be used in a search for additional exactly matching concepts',
                       default="MESH:D009755", required=True)
class GetExactMatches(Resource):
    # @api.marshal_with(match_model)
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
            if 'references' in claim:
                del claim['references']

        # figure out all ids that we got, make sure the wd curie is in it, then remove the input curies
        response_ids = set(x['id'] for x in claims)
        response_ids.update(qids)
        response_ids = response_ids - input_concepts

        return list(response_ids)


##########
# GET /exactmatches/{conceptId}
##########

@exactmatches_ns.route('/<conceptId>')
@exactmatches_ns.param('conceptId', 'curie', default="MESH:D009755")
class GetExactMatch(Resource):
    @api.doc(
        description="""Retrieves a list of qualified identifiers of "exact match" concepts, sensa SKOS associated with
        a specified (url-encoded) CURIE (without brackets) concept object identifier, typically, of a concept selected
        from the list of concepts originally returned by a /concepts API call on a given KS.""")
    def get(self, conceptId):
        """
        Retrieves identifiers that are specified as "external-ids" with the associated input identifier
        """
        if conceptId.startswith("wd:"):
            qids = (conceptId,)
        else:
            qids = get_equiv_item(conceptId)
        if not qids:
            return []
        claims = getEntitiesCurieClaims(qids)
        claims = list(chain(*claims.values()))
        claims = [claim.to_dict() for claim in claims]
        for claim in claims:
            claim['evidence'] = {'id': claim['id']}
            claim['id'] = claim['datavaluecurie']
            del claim['datavaluecurie']
            if 'references' in claim:
                del claim['references']

        response_ids = set(x['id'] for x in claims) | set(qids)
        return list(response_ids)


##########
# statements
##########


object_model = api.model("object_model", {
    'id': fields.String(description="CURIE-encoded local identifier", example='', required=True),
    'name': fields.String(description="human readable label of concept", example=''),
})

datapage_model = api.model("datapage_model", {
    'id': fields.String(description="local statement identifier", example='', required=True),
    'subject': fields.Nested(object_model, required=True),
    'object': fields.Nested(object_model, required=True),
    'predicate': fields.Nested(object_model, required=True),

})


@statements_ns.route('/')
@statements_ns.param('c', 'set of CURIE-encoded identifiers of exactly matching concepts to be used in a search '
                          'for associated concept-relation statements',
                     default=["wd:Q133696"], required=True, type=[str])
@statements_ns.param('types', 'constrain search by type', default='wd:Q12136')
@statements_ns.param('pageNumber', '(1-based) number of the page to be returned in a paged set of query results',
                     default=1, type=int)
@statements_ns.param('pageSize', 'number of concepts per page to be returned in a paged set of query results',
                     default=10, type=int)
@statements_ns.param('keywords', 'a (urlencoded) space delimited set of keywords or substrings against which to apply '
                                 'against the subject, predicate or object names of the set of concept-relations matched '
                                 'by any of the input exact matching concepts')
class GetStatements(Resource):
    @api.marshal_with(datapage_model)
    @api.doc(
        description="Given an input CURIE, retrieves the list of CURIE identifiers of additional concepts that are deemed to be exact matches. "
                    "This new list of concept identifiers is returned with the full list of any additional identifiers deemed by the KS to also be "
                    "identifying exactly matched concepts.")
    def get(self):
        """
        Get statements
        """
        qids = request.args.getlist('c')
        qids = set(chain(*[x.split(",") for x in qids]))
        print(qids)
        qids = tuple([x.strip().replace("wd:", "") for x in qids])
        print(qids)
        items = get_forward_items(qids) + get_reverse_items(qids)

        datapage = [{'id': item['id'],
                     'subject': {'id': item['item'], 'name': item['itemLabel']},
                     'predicate': {'id': item['property'], 'name': item['propertyLabel']},
                     'object': {'id': item['value'], 'name': item['valueLabel']},
                     } for item in items]

        return datapage


##########
# GET /evidence/{statementId}
##########


evidence_statement_model = api.model("evidence_statement_model", {
    'id': fields.String(description="local evidence identifier", example='', required=True),
    'evidence': fields.String(required=True),
})


@evidence_ns.route('/<statementId>')
@evidence_ns.param('statementId', '', default='Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29')
class GetEvidence(Resource):
    @api.marshal_with(evidence_statement_model)
    @api.doc(description="Retrieve evidence for a specified concept-relationship statement")
    def get(self, statementId):
        """
        Get statements
        """
        if '$' not in statementId:
            statementId = statementId.replace("-", '$', 1)

        params = {'action': 'wbgetclaims',
                  'claim': statementId,
                  'format': 'json'}
        r = requests.get("https://www.wikidata.org/w/api.php", params=params)
        r.raise_for_status()
        d = r.json()
        pid = list(d['claims'].keys())[0]
        qid = statementId.split("$")[0].upper()
        url = "https://www.wikidata.org/wiki/{}#{}".format(qid, pid)

        return [{"id": statementId, "evidence": url}]


if __name__ == '__main__':
    app.run()
