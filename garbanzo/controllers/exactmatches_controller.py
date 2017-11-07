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
    for claim in claims:
        claim['evidence'] = {'id': claim['id']}
        claim['id'] = claim['datavaluecurie']
        del claim['datavaluecurie']
        if 'references' in claim:
            del claim['references']

    response_ids = set(x['id'] for x in claims) | set(qids)
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
    concepts = connexion.request.args.get("c", '')
    concepts = concepts.split(" ") if concepts else []
    input_concepts = set(concepts)
    curies = set(x for x in concepts if not x.startswith("wd:"))
    equiv_qid = {curie: get_equiv_item(curie) for curie in curies}

    qids = set(x for x in concepts if x.startswith("wd:"))
    qids.update(set(chain(*equiv_qid.values())))

    if not qids:
        return []

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
