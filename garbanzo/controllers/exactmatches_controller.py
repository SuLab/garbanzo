from itertools import chain

import connexion
from datetime import date, datetime
from typing import List, Dict
from six import iteritems

from garbanzo.lookup import get_equiv_item, getEntitiesCurieClaims
from ..util import deserialize_date, deserialize_datetime


def get_exact_matches_to_concept(conceptId):
    """
    get_exact_matches_to_concept
    Retrieves a list of qualified identifiers of \&quot;exact match\&quot; concepts, [sensa SKOS](http://www.w3.org/2004/02/skos/core#exactMatch) associated with a specified (url-encoded) CURIE (without brackets) concept object identifier,  typically, of a concept selected from the list of concepts originally returned by a /concepts API call on a given KS.  
    :param conceptId: (url-encoded) CURIE identifier of the concept to be matched
    :type conceptId: str

    :rtype: List[str]
    """
    # Retrieves identifiers that are specified as "external-ids" with the associated input identifier
    if conceptId.startswith("wd:"):
        qids = (conceptId,)
    else:
        qids = get_equiv_item(conceptId)
    if not qids:
        return []
    claims = getEntitiesCurieClaims(qids)
    claims = list(chain(*claims.values()))
    claims = [claim.to_dict() for claim in claims]
    response_ids = set(x['datavaluecurie'] for x in claims) | set(qids)
    return list(response_ids)


def get_exact_matches_to_concept_list(c):
    """
    get_exact_matches_to_concept_list
    Given an input list of [CURIE](https://www.w3.org/TR/curie/) identifiers of known exactly matched concepts [*sensa*-SKOS](http://www.w3.org/2004/02/skos/core#exactMatch), retrieves the list of [CURIE](https://www.w3.org/TR/curie/) identifiers of additional concepts that are deemed by the given knowledge source to be exact matches to one or more of the input concepts **plus** whichever identifiers from the input list which specifically matched these new additional concepts.  If an empty set is returned, the it can be assumed that the given  knowledge source does not know of any new equivalent concepts matching the input set. 
    :param c: set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of exactly matching concepts, to be used in a search for additional exactly matching concepts [*sensa*-SKOS](http://www.w3.org/2004/02/skos/core#exactMatch). 
    :type c: List[str]

    :rtype: List[str]
    """
    # Retrieves identifiers that are specified as "external-ids" with the associated input identifiers

    # c = ["DOID:1234", "MESH:1234", "wd:Q1049021"]
    input_concepts = set(c)

    # for curies specifically, get the matching qids
    curies = set(x for x in input_concepts if not x.startswith("wd:"))
    equiv_qid = {curie: get_equiv_item(curie) for curie in curies}
    # and add in the input qids
    input_qids = set(x for x in input_concepts if x.startswith("wd:"))
    qids = set(chain(*equiv_qid.values())) | input_qids

    # get the xrefs for the qids
    claims = getEntitiesCurieClaims(qids)
    qid_claims = {"wd:" + qid: [claim.datavaluecurie for claim in c] for qid, c in claims.items()}
    qids_no_matches = {k for k,v in qid_claims.items() if not v}
    qid_claims = {k:v for k,v in qid_claims.items() if v}
    new_ids = set(chain(*qid_claims.values()))
    new_ids.update(qids)

    # from input_qids, remove the qids that matched nothing
    new_ids = new_ids - qids_no_matches

    # if no new matching concepts, return empty list
    if all(x in input_concepts for x in new_ids):
        return []

    return list(new_ids)
