from garbanzo.models.predicate import Predicate
from garbanzo.utils import execute_sparql_query
from typing import List


def get_predicates():
    """
    get_predicates
    Get a list of predicates used in statements issued by the knowledge source 

    :rtype: List[Predicate]
    """
    # Possible types: {'CommonsMedia', 'Time', 'Quantity', 'WikibaseProperty', 'WikibaseItem', 'GlobeCoordinate',
    # 'String', 'ExternalId', 'Math', 'Monolingualtext', 'TabularData', 'Url', 'GeoShape'}
    query = """SELECT ?p ?pt ?pLabel ?d ?aliases WHERE {
      {
        SELECT ?p ?pt ?d (GROUP_CONCAT(DISTINCT ?alias; separator="|") as ?aliases) WHERE {
          ?p wikibase:propertyType ?pt .
          OPTIONAL {?p skos:altLabel ?alias FILTER (LANG (?alias) = "en")}
          OPTIONAL {?p schema:description ?d FILTER (LANG (?d) = "en") .}
        } GROUP BY ?p ?pt ?d
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }"""
    results = execute_sparql_query(query)['results']['bindings']
    results = [{k: v['value'] for k, v in item.items()} for item in results]
    print(results[0])

    items = [{'id': "wd:" + x['p'].split("/")[-1],
              'name': x['pLabel'],
              'definition': x.get("d", ""),
              'aliases': x['aliases'].split("|") if x['aliases'] else [],
              'ptype': x['pt'].replace("http://wikiba.se/ontology#", "")} for x in results]
    # note: 'aliases' and 'ptype' are not in the official spec!

    return items
